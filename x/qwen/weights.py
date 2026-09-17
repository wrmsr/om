"""
Weight loading for Qwen3.5-family text models (model_type `qwen3_5`, GGUF arch `qwen35`).

Two on-disk formats are supported, both produced by Ollama:

  1. GGUF                 -- manifest layer `application/vnd.ollama.image.model`
                             (or any *.gguf path you pass directly)
  2. Ollama tensor blobs  -- manifest layers `application/vnd.ollama.image.tensor`
                             (one packed-safetensors blob per tensor, HF names,
                             optionally MLX affine-quantized) plus
                             `application/vnd.ollama.image.json` blobs holding
                             config.json / tokenizer.json.

Whatever the source, `TensorSource.get(name)` returns a float32 numpy array under a single canonical naming/layout
scheme so that `model.py` never has to know where the weights came from. The canonical scheme is HuggingFace's
text-model layout with *effective* values:

    embed_tokens.weight                              [vocab, hidden]
    norm.weight                                      [hidden]     (already includes the +1)
    lm_head.weight                                   [vocab, hidden]   (absent => tied)
    layers.{i}.input_layernorm.weight                (already includes the +1)
    layers.{i}.post_attention_layernorm.weight       (already includes the +1)
    layers.{i}.self_attn.q_proj.weight               [n_head*2*head_dim, hidden]  per head: [q | gate]
    layers.{i}.self_attn.k_proj.weight               [n_kv*head_dim, hidden]
    layers.{i}.self_attn.v_proj.weight               [n_kv*head_dim, hidden]
    layers.{i}.self_attn.o_proj.weight               [hidden, n_head*head_dim]
    layers.{i}.self_attn.q_norm.weight / k_norm.weight   [head_dim]  (already includes the +1)
    layers.{i}.linear_attn.in_proj_qkv.weight        [2*key_dim + value_dim, hidden]   [q | k | v]
    layers.{i}.linear_attn.in_proj_z.weight          [value_dim, hidden]
    layers.{i}.linear_attn.in_proj_b.weight          [n_v_heads, hidden]
    layers.{i}.linear_attn.in_proj_a.weight          [n_v_heads, hidden]
    layers.{i}.linear_attn.conv1d.weight             [conv_dim, kernel]
    layers.{i}.linear_attn.A                         [n_v_heads]   == -exp(A_log)
    layers.{i}.linear_attn.dt_bias                   [n_v_heads]
    layers.{i}.linear_attn.norm.weight               [head_v_dim]  (NO +1; gated norm)
    layers.{i}.linear_attn.out_proj.weight           [hidden, value_dim]
    layers.{i}.mlp.gate_proj.weight / up_proj.weight [inter, hidden]
    layers.{i}.mlp.down_proj.weight                  [hidden, inter]

V-head order for the linear-attention tensors is HF *grouped* order ([G0v0..G0v{r-1}, G1v0..] where G = key head), so
q/k broadcast to V heads with repeat_interleave. The GGUF converter stores them *tiled*; the GGUF source undoes that.
"""
import dataclasses as dc
import json
import os
import pathlib
import struct

import numpy as np


##


MT_GGUF = 'application/vnd.ollama.image.model'
MT_TENSOR = 'application/vnd.ollama.image.tensor'
MT_JSON = 'application/vnd.ollama.image.json'


##
# Config


@dc.dataclass()
class Qwen35Config:
    vocab_size: int
    hidden_size: int
    num_layers: int
    intermediate_size: int
    rms_eps: float
    # full attention
    num_heads: int
    num_kv_heads: int
    head_dim: int
    rope_theta: float
    rope_dim: int  # partial rotary: number of dims rotated (64 for head_dim 256)
    # gated delta net
    num_k_heads: int
    num_v_heads: int
    head_k_dim: int
    head_v_dim: int
    conv_kernel: int
    layer_types: list[str]  # "linear" | "full", len == num_layers
    context_length: int = 262144
    rope_scaling: dict | None = None
    tied_embeddings: bool = False
    extra: dict = dc.field(default_factory=dict)

    @property
    def key_dim(self) -> int:
        return self.num_k_heads * self.head_k_dim

    @property
    def value_dim(self) -> int:
        return self.num_v_heads * self.head_v_dim

    @property
    def conv_dim(self) -> int:
        return 2 * self.key_dim + self.value_dim

    def summary(self) -> str:
        n_lin = sum(t == 'linear' for t in self.layer_types)
        return (
            f'hidden={self.hidden_size} layers={self.num_layers} ({n_lin} linear / {self.num_layers - n_lin} full) '
            f'ffn={self.intermediate_size} vocab={self.vocab_size}\n'
            f'  attn: {self.num_heads}q/{self.num_kv_heads}kv x {self.head_dim}, rope_dim={self.rope_dim} theta={self.rope_theta:g}\n'
            f'  gdn : {self.num_k_heads}k/{self.num_v_heads}v x {self.head_k_dim}, conv={self.conv_kernel}\n'
            f'  tied_embeddings={self.tied_embeddings} rope_scaling={self.rope_scaling}'
        )


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


def parse_model_name(name: str) -> tuple[str, str, str, str]:
    """'qwen3.5:0.8b' -> (host, namespace, model, tag)."""

    host, ns, tag = 'registry.ollama.ai', 'library', 'latest'
    if ':' in name.rsplit('/', 1)[-1]:
        name, tag = name.rsplit(':', 1)
    parts = name.split('/')
    if len(parts) == 3:
        host, ns, model = parts
    elif len(parts) == 2:
        ns, model = parts
    else:
        model = parts[0]
    return host, ns, model, tag


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


_ST_DTYPES = {
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
    def __init__(self, path: pathlib.Path):
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

    def get(self, name: str) -> np.ndarray:
        info = self.header[name]
        start, end = info['data_offsets']
        buf = self._mm[self._base + start : self._base + end]
        dt = info['dtype']
        shape = tuple(info['shape'])
        if dt == 'BF16':
            return bf16_to_f32(np.frombuffer(buf, dtype=np.uint16)).reshape(shape)
        arr = np.frombuffer(buf, dtype=_ST_DTYPES[dt]).reshape(shape)
        return arr


def mlx_affine_dequant(
    w_packed: np.ndarray,
    scales: np.ndarray,
    biases: np.ndarray | None,
    bits: int,
    group_size: int,
) -> np.ndarray:
    """
    MLX `mx.quantize` affine layout: uint32 words, `32//bits` values each, first value in the low bits, groups of
    `group_size` along the last axis with one scale (+bias) each.
    """

    assert w_packed.dtype == np.uint32
    per_word = 32 // bits
    mask = (1 << bits) - 1
    shifts = (np.arange(per_word, dtype=np.uint32) * bits)[None, :]
    flat = w_packed.reshape(-1, 1)
    vals = (
        ((flat >> shifts) & mask)
        .astype(np.float32)
        .reshape(*w_packed.shape[:-1], w_packed.shape[-1] * per_word)
    )
    cols = vals.shape[-1]
    assert cols % group_size == 0, (cols, group_size)
    vals = vals.reshape(*vals.shape[:-1], cols // group_size, group_size)
    s = scales.astype(np.float32)[..., None]
    out = vals * s
    if biases is not None:
        out = out + biases.astype(np.float32)[..., None]
    return out.reshape(*w_packed.shape[:-1], cols)


##
# Tensor sources


class TensorSource:
    config: Qwen35Config
    tokenizer_spec: dict  # see tokenizer.py

    def names(self) -> list[str]:
        raise NotImplementedError

    def get(self, name: str) -> np.ndarray:
        raise NotImplementedError

    def has(self, name: str) -> bool:
        return name in set(self.names())


def _untile_v_heads(x: np.ndarray, axis: int, num_k: int, r: int, d: int) -> np.ndarray:
    """Inverse of llama.cpp's `_reorder_v_heads`: tiled [r, num_k, d] -> grouped [num_k, r, d]."""

    if r == 1:
        return x
    shape = list(x.shape)
    axis = axis % x.ndim
    new = shape[:axis] + [r, num_k, d] + shape[axis + 1 :]
    x = x.reshape(new)
    perm = list(range(x.ndim))
    perm[axis], perm[axis + 1] = perm[axis + 1], perm[axis]
    return np.ascontiguousarray(x.transpose(perm)).reshape(shape)


class GGUFSource(TensorSource):
    """GGUF produced by llama.cpp's converter (arch `qwen35`). Uses gguf-py (numpy only)."""

    def __init__(self, path: str | pathlib.Path):
        from gguf import GGUFReader  # MIT, part of llama.cpp

        self.path = pathlib.Path(path)
        self.reader = GGUFReader(str(self.path))
        self._tensors = {t.name: t for t in self.reader.tensors}
        arch = self.kv('general.architecture')
        if arch != 'qwen35':
            raise ValueError(f'unsupported GGUF architecture {arch!r} (want qwen35)')
        self.arch = arch
        self.config = self._build_config()
        self.tokenizer_spec = self._build_tokenizer_spec()
        self._canon = self._build_name_map()

    # metadata helpers

    def kv(self, key: str, default=None):
        f = self.reader.fields.get(key)
        return default if f is None else f.contents()

    def akv(self, key: str, default=None):
        return self.kv(f'{self.arch}.{key}', default)

    def _build_config(self) -> Qwen35Config:
        a = self.akv
        n_layer_all = int(a('block_count'))
        n_nextn = int(a('nextn_predict_layers', 0) or 0)
        n_layer = n_layer_all - n_nextn
        head_dim = int(a('attention.key_length'))
        n_head = a('attention.head_count')
        n_head = max(n_head) if isinstance(n_head, list) else int(n_head)
        n_kv = a('attention.head_count_kv')
        n_kv = max(n_kv) if isinstance(n_kv, list) else int(n_kv)
        recr = a('attention.recurrent_layers')
        if recr is None:
            interval = int(a('full_attention_interval', 4) or 4)
            recr = [((i + 1) % interval != 0) for i in range(n_layer)]
        layer_types = ['linear' if bool(r) else 'full' for r in list(recr)[:n_layer]]
        state = int(a('ssm.state_size'))
        n_v = int(a('ssm.time_step_rank'))
        n_k = int(a('ssm.group_count'))
        inner = int(a('ssm.inner_size'))
        assert inner == n_v * state, (inner, n_v, state)
        tokens = self.kv('tokenizer.ggml.tokens')
        vocab = int(a('vocab_size', len(tokens)) or len(tokens))
        emb = self._tensors['token_embd.weight']
        if vocab != int(emb.shape[1]):
            vocab = int(emb.shape[1])
        scaling_type = a('rope.scaling.type')
        rope_scaling = None
        if scaling_type and scaling_type != 'none':
            rope_scaling = {
                k.split('rope.scaling.')[-1]: a(k)
                for k in [
                    'rope.scaling.type',
                    'rope.scaling.factor',
                    'rope.scaling.original_context_length',
                    'rope.scaling.attn_factor',
                ]
                if a(k) is not None
            }
        return Qwen35Config(
            vocab_size=vocab,
            hidden_size=int(a('embedding_length')),
            num_layers=n_layer,
            intermediate_size=int(a('feed_forward_length')),
            rms_eps=float(a('attention.layer_norm_rms_epsilon')),
            num_heads=n_head,
            num_kv_heads=n_kv,
            head_dim=head_dim,
            rope_theta=float(a('rope.freq_base', 10000.0)),
            rope_dim=int(a('rope.dimension_count', head_dim // 4)),
            num_k_heads=n_k,
            num_v_heads=n_v,
            head_k_dim=state,
            head_v_dim=state,
            conv_kernel=int(a('ssm.conv_kernel')),
            layer_types=layer_types,
            context_length=int(a('context_length', 262144) or 262144),
            rope_scaling=rope_scaling,
            tied_embeddings='output.weight' not in self._tensors,
            extra={
                'gguf_path': str(self.path),
                'n_nextn': n_nextn,
                'file_type': self.kv('general.file_type'),
            },
        )

    def _build_tokenizer_spec(self) -> dict:
        kv = self.kv
        return {
            'kind': 'gguf',
            'model': kv('tokenizer.ggml.model'),
            'pre': kv('tokenizer.ggml.pre', 'qwen2'),
            'tokens': kv('tokenizer.ggml.tokens'),
            'token_type': kv('tokenizer.ggml.token_type'),
            'merges': kv('tokenizer.ggml.merges'),
            'eos_id': kv('tokenizer.ggml.eos_token_id'),
            'bos_id': kv('tokenizer.ggml.bos_token_id'),
            'pad_id': kv('tokenizer.ggml.padding_token_id'),
            'add_bos': bool(kv('tokenizer.ggml.add_bos_token', False)),
            'chat_template': kv('tokenizer.chat_template'),
        }

    # name mapping GGUF -> canonical

    def _build_name_map(self) -> dict[str, tuple]:
        """canonical name -> (gguf name, post-processing tag)."""

        c = self.config
        m: dict[str, tuple] = {
            'embed_tokens.weight': ('token_embd.weight', None),
            'norm.weight': ('output_norm.weight', None),
        }
        if 'output.weight' in self._tensors:
            m['lm_head.weight'] = ('output.weight', None)
        for i, lt in enumerate(c.layer_types):
            p = f'blk.{i}.'
            q = f'layers.{i}.'
            m[q + 'input_layernorm.weight'] = (p + 'attn_norm.weight', None)
            m[q + 'post_attention_layernorm.weight'] = (
                p + 'attn_post_norm.weight',
                None,
            )
            m[q + 'mlp.gate_proj.weight'] = (p + 'ffn_gate.weight', None)
            m[q + 'mlp.up_proj.weight'] = (p + 'ffn_up.weight', None)
            m[q + 'mlp.down_proj.weight'] = (p + 'ffn_down.weight', None)
            if lt == 'full':
                fused = (
                    p + 'attn_qkv.weight' in self._tensors
                    and p + 'attn_q.weight' not in self._tensors
                )
                if fused:
                    m[q + 'self_attn.q_proj.weight'] = (
                        p + 'attn_qkv.weight',
                        'fused_q',
                    )
                    m[q + 'self_attn.k_proj.weight'] = (
                        p + 'attn_qkv.weight',
                        'fused_k',
                    )
                    m[q + 'self_attn.v_proj.weight'] = (
                        p + 'attn_qkv.weight',
                        'fused_v',
                    )
                else:
                    m[q + 'self_attn.q_proj.weight'] = (p + 'attn_q.weight', None)
                    m[q + 'self_attn.k_proj.weight'] = (p + 'attn_k.weight', None)
                    m[q + 'self_attn.v_proj.weight'] = (p + 'attn_v.weight', None)
                m[q + 'self_attn.o_proj.weight'] = (p + 'attn_output.weight', None)
                m[q + 'self_attn.q_norm.weight'] = (p + 'attn_q_norm.weight', None)
                m[q + 'self_attn.k_norm.weight'] = (p + 'attn_k_norm.weight', None)
            else:
                m[q + 'linear_attn.in_proj_qkv.weight'] = (
                    p + 'attn_qkv.weight',
                    'untile_qkv_rows',
                )
                m[q + 'linear_attn.in_proj_z.weight'] = (
                    p + 'attn_gate.weight',
                    'untile_rows_dv',
                )
                m[q + 'linear_attn.in_proj_b.weight'] = (
                    p + 'ssm_beta.weight',
                    'untile_rows_1',
                )
                m[q + 'linear_attn.in_proj_a.weight'] = (
                    p + 'ssm_alpha.weight',
                    'untile_rows_1',
                )
                m[q + 'linear_attn.conv1d.weight'] = (
                    p + 'ssm_conv1d.weight',
                    'untile_conv',
                )
                m[q + 'linear_attn.A'] = (p + 'ssm_a', 'untile_rows_1')
                m[q + 'linear_attn.dt_bias'] = (p + 'ssm_dt.bias', 'untile_rows_1')
                m[q + 'linear_attn.norm.weight'] = (p + 'ssm_norm.weight', None)
                m[q + 'linear_attn.out_proj.weight'] = (
                    p + 'ssm_out.weight',
                    'untile_cols_dv',
                )
        missing = [k for k, (g, _) in m.items() if g not in self._tensors]
        if missing:
            raise KeyError(
                f'GGUF is missing expected tensors, e.g. {missing[:5]} (of {len(missing)})',
            )
        return m

    def names(self) -> list[str]:
        return list(self._canon.keys())

    def has(self, name: str) -> bool:
        return name in self._canon

    def raw(self, gguf_name: str) -> np.ndarray:
        from gguf.quants import dequantize

        t = self._tensors[gguf_name]
        arr = dequantize(t.data, t.tensor_type)
        # gguf-py hands back numpy arrays in row-major (reversed ggml ne) order, i.e. HF [out, in].
        return np.ascontiguousarray(arr, dtype=np.float32).reshape(
            tuple(reversed([int(d) for d in t.shape])),
        )

    def get(self, name: str) -> np.ndarray:
        gname, tag = self._canon[name]
        x = self.raw(gname)
        c = self.config
        r = c.num_v_heads // c.num_k_heads
        if tag is None:
            return x
        if tag.startswith('fused_'):
            nq = c.num_heads * c.head_dim * 2
            nk = c.num_kv_heads * c.head_dim
            if tag == 'fused_q':
                return x[:nq]
            if tag == 'fused_k':
                return x[nq : nq + nk]
            return x[nq + nk : nq + 2 * nk]
        if tag == 'untile_qkv_rows':
            qk = 2 * c.key_dim
            v = _untile_v_heads(x[qk:], 0, c.num_k_heads, r, c.head_v_dim)
            return np.concatenate([x[:qk], v], axis=0)
        if tag == 'untile_rows_dv':
            return _untile_v_heads(x, 0, c.num_k_heads, r, c.head_v_dim)
        if tag == 'untile_rows_1':
            return _untile_v_heads(x, 0, c.num_k_heads, r, 1)
        if tag == 'untile_cols_dv':
            return _untile_v_heads(x, 1, c.num_k_heads, r, c.head_v_dim)
        if tag == 'untile_conv':
            qk = 2 * c.key_dim
            v = _untile_v_heads(x[qk:], 0, c.num_k_heads, r, c.head_v_dim)
            return np.concatenate([x[:qk], v], axis=0)
        raise ValueError(tag)


class OllamaTensorSource(TensorSource):
    """Ollama's newer blob format: per-tensor packed safetensors with HF names."""

    _PREFIXES = ('model.language_model.', 'model.')

    def __init__(self, om: OllamaModel):
        self.om = om
        self._layers: dict[str, dict] = {}
        for l in om.layers(MT_TENSOR):
            self._layers[self._canon_name(l['name'])] = l
        cfg_layer = next(
            (l for l in om.layers(MT_JSON) if l.get('name') == 'config.json'), None,
        )
        if cfg_layer is None:
            raise FileNotFoundError('config.json layer not found in manifest')
        cfg = json.loads(om.blob(cfg_layer['digest']).read_text())
        self.hf_config = cfg
        self.config = self._build_config(cfg)
        tok_layer = next(
            (l for l in om.layers(MT_JSON) if l.get('name') == 'tokenizer.json'), None,
        )
        tcfg_layer = next(
            (l for l in om.layers(MT_JSON) if l.get('name') == 'tokenizer_config.json'),
            None,
        )
        self.tokenizer_spec = {
            'kind': 'hf',
            'tokenizer_json': (
                json.loads(om.blob(tok_layer['digest']).read_text())
                if tok_layer
                else None
            ),
            'tokenizer_config': (
                json.loads(om.blob(tcfg_layer['digest']).read_text())
                if tcfg_layer
                else None
            ),
            'eos_id': cfg.get('eos_token_id'),
        }
        self._files: dict[str, SafetensorsFile] = {}

    @classmethod
    def _canon_name(cls, name: str) -> str:
        for p in cls._PREFIXES:
            if name.startswith(p):
                name = name[len(p) :]
                break
        return name

    def _build_config(self, cfg: dict) -> Qwen35Config:
        t = cfg.get('text_config', cfg)
        rp = t.get('rope_parameters') or t.get('rope_scaling') or {}
        head_dim = t.get('head_dim') or t['hidden_size'] // t['num_attention_heads']
        prf = rp.get('partial_rotary_factor', t.get('partial_rotary_factor', 0.25))
        n_layer = t['num_hidden_layers']
        lts = t.get('layer_types')
        if lts is None:
            interval = t.get('full_attention_interval', 4)
            lts = [
                'full_attention' if (i + 1) % interval == 0 else 'linear_attention'
                for i in range(n_layer)
            ]
        layer_types = ['linear' if x == 'linear_attention' else 'full' for x in lts]
        rope_type = rp.get('rope_type', rp.get('type', 'default'))
        rope_scaling = None if rope_type in (None, 'default') else rp
        return Qwen35Config(
            vocab_size=t['vocab_size'],
            hidden_size=t['hidden_size'],
            num_layers=n_layer,
            intermediate_size=t['intermediate_size'],
            rms_eps=t.get('rms_norm_eps', 1e-6),
            num_heads=t['num_attention_heads'],
            num_kv_heads=t['num_key_value_heads'],
            head_dim=head_dim,
            rope_theta=float(rp.get('rope_theta', t.get('rope_theta', 10000.0))),
            rope_dim=int(head_dim * prf),
            num_k_heads=t['linear_num_key_heads'],
            num_v_heads=t['linear_num_value_heads'],
            head_k_dim=t['linear_key_head_dim'],
            head_v_dim=t['linear_value_head_dim'],
            conv_kernel=t['linear_conv_kernel_dim'],
            layer_types=layer_types,
            context_length=t.get('max_position_embeddings', 262144),
            rope_scaling=rope_scaling,
            tied_embeddings=bool(
                t.get('tie_word_embeddings', cfg.get('tie_word_embeddings', False)),
            ),
            extra={'format': 'ollama-tensor'},
        )

    def names(self) -> list[str]:
        out = []
        for n in self._layers:
            if n.endswith('.A_log'):
                out.append(n[: -len('A_log')] + 'A')
            else:
                out.append(n)
        return out

    def _file(self, canon: str) -> SafetensorsFile:
        l = self._layers[canon]
        d = l['digest']
        if d not in self._files:
            self._files[d] = SafetensorsFile(self.om.blob(d))
        return self._files[d]

    def _load_hf(self, canon: str) -> np.ndarray:
        f = self._file(canon)
        raw_name = self._layers[canon]['name']
        names = f.names()
        base = (
            raw_name
            if raw_name in names
            else next(n for n in names if not n.endswith(('.scale', '.bias')))
        )
        w = f.get(base)
        if w.dtype == np.uint32:  # MLX quantized
            md = f.metadata
            qt = md.get(base + '.quant_type') or md.get('quant_type') or 'int4'
            gs = int(md.get(base + '.group_size') or md.get('group_size') or 64)
            bits = {'int4': 4, 'int8': 8}.get(qt.lower())
            if bits is None:
                raise NotImplementedError(
                    f'MLX quant mode {qt!r} not supported (only affine int4/int8)',
                )
            scales = f.get(base + '.scale')
            biases = f.get(base + '.bias') if (base + '.bias') in names else None
            w = mlx_affine_dequant(w, scales, biases, bits, gs)
        return np.ascontiguousarray(w, dtype=np.float32)

    def get(self, name: str) -> np.ndarray:
        if name.endswith('.linear_attn.A'):
            return -np.exp(self._load_hf(name[:-1] + 'A_log'))
        x = self._load_hf(name)
        # HF stores zero-centred norm weights (1 + w) for every RMSNorm except the gated one.
        if name.endswith('norm.weight') and not name.endswith(
            'linear_attn.norm.weight',
        ):
            x = x + 1.0
        if name.endswith('linear_attn.conv1d.weight') and x.ndim == 3:
            x = x[:, 0, :]
        return x


##
# Entry point


def open_source(model: str) -> TensorSource:
    """`model` is an Ollama model name (qwen3.5:0.8b), a path to a .gguf, or a path to an Ollama manifest."""

    p = pathlib.Path(model).expanduser()
    if p.is_file() and p.suffix == '.gguf':
        return GGUFSource(p)
    if p.is_file():  # maybe a raw blob: sniff magic
        with open(p, 'rb') as f:
            magic = f.read(4)
        if magic == b'GGUF':
            return GGUFSource(p)
        raise ValueError(f'{p}: not a GGUF')
    om = resolve_ollama(model)
    ggufs = om.layers(MT_GGUF)
    if ggufs:
        ggufs.sort(key=lambda l: -l.get('size', 0))
        if len(ggufs) > 1:
            print(
                f"[weights] {len(ggufs)} model layers in manifest; using largest ({ggufs[0]['digest'][:19]})",
            )
        return GGUFSource(om.blob(ggufs[0]['digest']))
    if om.layers(MT_TENSOR):
        return OllamaTensorSource(om)
    raise ValueError(f'no model weights found in manifest {om.manifest_path}')


def describe(source: TensorSource) -> str:
    return source.config.summary()
