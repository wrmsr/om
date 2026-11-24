# ruff: noqa: N803 N806 N812
"""
What a model's weights are read through, whatever its family: `TensorSource` -- a config, a tokenizer and the
canonical parameters by name, float32 or as the file packs them -- and the pieces sources are made of: Ollama's
blob store and manifests, a safetensors reader (no `safetensors` package needed), and how a model named on a command
line is found and opened (`open_source`: an Ollama name, a GGUF, a blob, a Hugging Face checkpoint directory). Which
source reads a given file is its family's to say (families.py); the sources themselves are with the families
(models/).
"""
import json
import os
import pathlib
import struct
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.logs import all as logs

from ..core.config import ModelConfig
from ..ops.microscaled import MicroscaledWeight


if ta.TYPE_CHECKING:
    import numpy as np

    from . import families
else:
    np = lang.proxy_import('numpy')
    families = lang.proxy_import('.families', __package__)  # (lazily: the families' readers build on this module)


##


log = logs.get_module_logger(globals())


MT_GGUF = 'application/vnd.ollama.image.model'
MT_TENSOR = 'application/vnd.ollama.image.tensor'
MT_JSON = 'application/vnd.ollama.image.json'


##
# Ollama manifest resolution


def ollama_models_dir() -> pathlib.Path:
    env = os.environ.get('OLLAMA_MODELS')
    cands = [pathlib.Path(env)] if env else []
    cands += [
        pathlib.Path.home() / '.ollama' / 'models',
        pathlib.Path('/usr/share/ollama/.ollama/models'),
    ]
    for c in cands:
        if (c / 'manifests').is_dir():
            return c
    raise FileNotFoundError('Ollama models dir not found (set OLLAMA_MODELS)')


class ParsedModelName(ta.NamedTuple):
    host: str
    ns: str
    model: str
    tag: str


def parse_model_name(name: str) -> ParsedModelName:
    """'qwen3.5:0.8b' -> (host, namespace, model, tag)."""

    host = 'registry.ollama.ai'
    ns = 'library'
    tag = 'latest'
    if ':' in name.rsplit('/', 1)[-1]:
        name, tag = name.rsplit(':', 1)
    parts = name.split('/')
    if len(parts) == 3:
        host, ns, model = parts
    elif len(parts) == 2:
        ns, model = parts
    else:
        model = parts[0]
    return ParsedModelName(
        host,
        ns,
        model,
        tag,
    )


@dc.dataclass()
class OllamaModel:
    manifest_path: pathlib.Path
    manifest: dict
    blobs_dir: pathlib.Path

    def blob(self, digest: str) -> pathlib.Path:
        return self.blobs_dir / digest.replace(':', '-')

    def layers(self, media_type: str) -> list[dict]:
        return [
            l
            for l in self.manifest.get('layers', [])
            if l.get('mediaType') == media_type
        ]


def resolve_ollama(name: str) -> OllamaModel:
    root = ollama_models_dir()
    host, ns, model, tag = parse_model_name(name)
    mp = root / 'manifests' / host / ns / model / tag
    if not mp.exists():
        raise FileNotFoundError(f'manifest not found: {mp}')
    return OllamaModel(mp, json.loads(mp.read_text()), root / 'blobs')


##
# Packed safetensors reader (no `safetensors` package needed)


def _st_dtypes() -> dict[str, ta.Any]:
    """safetensors dtype names -> numpy dtypes (a function: numpy is imported lazily)."""

    return {
        'F32': np.float32,
        'F16': np.float16,
        'BF16': None,
        'F64': np.float64,
        'I8': np.int8,
        'U8': np.uint8,
        'I16': np.int16,
        'I32': np.int32,
        'I64': np.int64,
        'U32': np.uint32,
        'BOOL': np.bool_,
    }


def bf16_to_f32(raw: np.ndarray) -> np.ndarray:
    u16 = raw.view(np.uint16).astype(np.uint32) << 16
    return u16.view(np.float32)


class SafetensorsFile:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = pathlib.Path(path)
        with open(path, 'rb') as f:
            (hlen,) = struct.unpack('<Q', f.read(8))
            header = json.loads(f.read(hlen))
        self.metadata = header.pop('__metadata__', {}) or {}
        self.header = header
        self._base = 8 + hlen
        self._mm = np.memmap(path, dtype=np.uint8, mode='r')

    def names(self) -> list[str]:
        return list(self.header.keys())

    def dtype(self, name: str) -> str:
        """The stored dtype's safetensors name ('BF16', 'U8', 'F8_E4M3', ...)."""

        return self.header[name]['dtype']

    def shape(self, name: str) -> tuple[int, ...]:
        return tuple(self.header[name]['shape'])

    def raw(self, name: str) -> np.ndarray:
        """
        A one-byte-per-element tensor's bytes as stored, uint8 in its shape, memory-mapped: for a tensor whose bytes
        are codes of a format numpy has no dtype for ('F8_E4M3') or that only its reader knows how to pair with
        others. Not numbers: see ops/microscaled.py.
        """

        info = self.header[name]
        if info['dtype'] not in ('U8', 'I8', 'F8_E4M3', 'F8_E5M2'):
            raise ValueError(f'{name}: {info["dtype"]} is not a one-byte dtype')
        start, end = info['data_offsets']
        return self._mm[self._base + start:self._base + end].reshape(tuple(info['shape']))

    def get(self, name: str) -> np.ndarray:
        info = self.header[name]
        start, end = info['data_offsets']
        buf = self._mm[self._base + start:self._base + end]
        dt = info['dtype']
        shape = tuple(info['shape'])
        if dt not in _st_dtypes():
            raise ValueError(f'{name}: no numeric reading of safetensors dtype {dt} (see `raw`)')
        if dt == 'BF16':
            return bf16_to_f32(np.frombuffer(buf, dtype=np.uint16)).reshape(shape)
        arr = np.frombuffer(buf, dtype=_st_dtypes()[dt]).reshape(shape)
        return arr


##
# Tensor sources


@dc.dataclass()
class NativeQuant:
    """A tensor the source already holds in affine `bits`-bit form: w ≈ values * scale + bias (see quant.py)."""

    values: np.ndarray  # uint8 [out, in], one value per element (unpacked)
    scale: np.ndarray  # [out, in // group]
    bias: np.ndarray  # [out, in // group]
    bits: int
    group: int


class TensorSource:
    config: ModelConfig
    tokenizer_spec: dict  # see tokenizer.py

    def names(self) -> list[str]:
        raise NotImplementedError

    def get(self, name: str) -> np.ndarray:
        raise NotImplementedError

    def get_quant(self, name: str) -> NativeQuant | None:
        """The tensor in its stored quantized form, if the source has one that quant.py can use directly."""

        return None

    def get_microscaled(self, name: str) -> MicroscaledWeight | None:
        """
        The tensor as the source stores it in a microscaled float format (ops/microscaled.py), if it does: a stack of
        matrices a backend adopts as it is, where `get` would expand it to float32.
        """

        return None

    def has(self, name: str) -> bool:
        return name in set(self.names())


def find_hf_checkpoint(p: pathlib.Path) -> pathlib.Path:
    """
    The directory holding config.json under `p`: `p` itself, the Hugging Face cache layout
    (models--org--name/snapshots/<hash>/), or a single checkpoint directory one level down.
    """

    if (p / 'config.json').exists():
        return p
    cands = sorted(p.glob('snapshots/*/config.json')) + sorted(p.glob('*/snapshots/*/config.json'))
    cands += sorted(p.glob('*/config.json'))
    if cands:
        if len({c.parent for c in cands}) > 1:
            raise FileNotFoundError(
                f'{p}: several checkpoints under it ({", ".join(str(c.parent) for c in cands)}); point at one',
            )
        return cands[0].parent
    raise FileNotFoundError(
        f'{p} is a directory without a config.json (a Hugging Face checkpoint has config.json, tokenizer.json '
        f'and *.safetensors); pass the checkpoint directory itself, a .gguf, or an Ollama model name',
    )


##
# Entry point


def resolve_weights(model: str) -> pathlib.Path | OllamaModel | TensorSource:
    """
    `model` -> a GGUF path, the Ollama manifest for tensor-blob models, or -- for a Hugging Face checkpoint directory
    -- the source itself, of whichever family its config names (families.py).
    """

    p = pathlib.Path(model).expanduser()
    if p.is_dir():
        return families.open_hf_source(str(find_hf_checkpoint(p)))
    if p.is_file() and p.suffix == '.gguf':
        return p
    if p.is_file():  # maybe a raw blob: sniff magic
        with open(p, 'rb') as f:
            magic = f.read(4)
        if magic == b'GGUF':
            return p
        raise ValueError(f'{p}: not a GGUF')
    om = resolve_ollama(model)
    ggufs = om.layers(MT_GGUF)
    if ggufs:
        ggufs.sort(key=lambda l: -l.get('size', 0))
        if len(ggufs) > 1:
            log.info('%d model layers in manifest; using largest (%s)', len(ggufs), ggufs[0]['digest'][:19])
        return om.blob(ggufs[0]['digest'])
    if om.layers(MT_TENSOR):
        return om
    raise ValueError(f'no model weights found in manifest {om.manifest_path}')


def open_source(model: str) -> TensorSource:
    """
    `model` is an Ollama model name (qwen3.5:0.8b), a path to a .gguf or a GGUF blob (read by whichever source its
    architecture has: families.py), a path to an Ollama manifest, or a Hugging Face checkpoint directory.
    """

    r = resolve_weights(model)
    if isinstance(r, TensorSource):
        return r
    if isinstance(r, OllamaModel):
        return families.open_ollama_source(r)
    return families.open_gguf_source(str(r))


def describe_gguf(path: str | pathlib.Path, max_blocks: int = 4) -> str:
    """
    Raw metadata and tensor listing (names, ggml shapes, types) straight from the file, before any mapping -- the thing
    to look at when a load fails.
    """

    from .gguf.reader import GGUFReader

    r = GGUFReader(str(path))
    lines = [f'# {path}', '## metadata']
    for k, f in r.fields.items():
        if k.startswith('tokenizer.ggml.') and k not in ('tokenizer.ggml.model', 'tokenizer.ggml.pre'):
            continue  # token lists are huge
        v = f.contents()
        if isinstance(v, list) and len(v) > 16:
            v = f'list[{len(v)}] {v[:8]}...'
        lines.append(f'{k} = {v}')
    lines.append(f'## tensors ({len(r.tensors)}; blocks >= {max_blocks} elided)')
    for t in r.tensors:
        if t.name.startswith('blk.') and int(t.name.split('.')[1]) >= max_blocks:
            continue
        lines.append(f'{t.name:48s} {t.tensor_type.name:8s} ne={[int(d) for d in t.shape]}')
    return '\n'.join(lines)


def describe(source: TensorSource) -> str:
    return source.config.summary()
