# ruff: noqa: N803 N806 N812
"""
On-disk cache of finished parameters.

Loading a 27B from an Ollama GGUF costs ~2 minutes: gguf-py's numpy k-quant dequantization of every tensor, then
requantization. The result is the same every time, so `from_source(..., cache_dir=...)` keeps it: one `.npy` per array
(memory-mapped on the way back in) under

    <cache_dir>/<source identity>-<quant>-g<group>/<canonical name>[.q|.scale|.bias].npy   (+ <name>.json)

Dense tensors are stored as the float32 canonical arrays `TensorSource.get` returns (only worth it with a quantized
model: an unquantized 27B would be 108 GB of f32). Quantized tensors are stored as `quant.QWeight` (packed uint8 codes +
f32 scale/bias), backend-independent, so a cache built on torch loads on MLX. Entries are independent files, so loading
with `mtp=True` after an `mtp=False` build just adds the draft head.

On a miss the weights are quantized on the device as usual and exported back to numpy through `Ops.export_qweight`;
backends without it fall back to the (slower) numpy quantizer. Writes are atomic per entry (temp file + rename), so an
interrupted build leaves a partial but valid cache.
"""
import hashlib
import json
import os
import pathlib
import re
import typing as ta

import numpy as np

from omcore import dataclasses as dc

from .quant import QWeight


##


_SHA_RE = re.compile(r'sha256-([0-9a-f]{64})')


def source_identity(src: ta.Any) -> str:
    """
    A stable id for a TensorSource: the Ollama blob digest when the path carries one, else a hash of the file path, size
    and mtime (GGUF), else a hash of the manifest's tensor digests (Ollama tensor blobs).
    """

    path = getattr(src, 'path', None)
    if path is not None:
        path = pathlib.Path(path)
        m = _SHA_RE.search(path.name)
        if m:
            return m.group(1)[:16]
        if path.is_dir():  # an HF checkpoint: the shards' names and sizes (not path or mtime: the same download
            # on another machine must map to the same cache directory)
            shards = sorted(path.glob('*.safetensors'))
            parts = [f'{p.name}|{p.stat().st_size}' for p in shards]
            return hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]
        st = path.stat()
        h = hashlib.sha256(f'{path.resolve()}|{st.st_size}|{int(st.st_mtime)}'.encode()).hexdigest()
        return h[:16]
    om = getattr(src, 'om', None)
    if om is not None:
        layers = sorted((l.get('name', ''), l.get('digest', '')) for l in om.manifest.get('layers', []))
        return hashlib.sha256(json.dumps(layers).encode()).hexdigest()[:16]
    raise ValueError(f'cannot identify source {src!r}')


def _safe(name: str) -> str:
    return name.replace('/', '_')


@dc.dataclass()
class ParamCache:
    root: pathlib.Path
    hits: int = 0
    misses: int = 0

    @classmethod
    def open(
            cls,
            cache_dir: str | pathlib.Path,
            src: ta.Any,
            quant: str | None,
            group: int,
            variant: str = '',
    ) -> ParamCache:
        """`variant` tags the quantizer / precision policy so different recipes for one blob keep separate entries."""

        tag = f'-{variant}' if variant else ''
        root = pathlib.Path(cache_dir).expanduser() / f'{source_identity(src)}-{quant or "none"}-g{group}{tag}'
        root.mkdir(parents=True, exist_ok=True)
        return cls(root)

    def _meta_path(self, name: str) -> pathlib.Path:
        return self.root / (_safe(name) + '.json')

    def get(self, name: str) -> np.ndarray | QWeight | None:
        mp = self._meta_path(name)
        if not mp.exists():
            self.misses += 1
            return None
        meta = json.loads(mp.read_text())
        base = self.root / _safe(name)
        try:
            if meta['kind'] == 'dense':
                out: np.ndarray | QWeight = np.load(str(base) + '.npy', mmap_mode='r')
            else:
                out = QWeight(
                    np.load(str(base) + '.q.npy', mmap_mode='r'),
                    np.load(str(base) + '.scale.npy', mmap_mode='r'),
                    np.load(str(base) + '.bias.npy', mmap_mode='r'),
                    int(meta['bits']),
                    int(meta['group']),
                    tuple(meta['shape']),
                )
        except (OSError, ValueError):  # a torn entry: treat as a miss and let it be rewritten
            self.misses += 1
            return None
        self.hits += 1
        return out

    def put(self, name: str, value: np.ndarray | QWeight) -> None:
        base = self.root / _safe(name)
        if isinstance(value, QWeight):
            self._save(str(base) + '.q.npy', value.q)
            self._save(str(base) + '.scale.npy', np.asarray(value.scale, dtype=np.float32))
            self._save(str(base) + '.bias.npy', np.asarray(value.bias, dtype=np.float32))
            meta = {'kind': 'qweight', 'bits': value.bits, 'group': value.group, 'shape': list(value.shape)}
        else:
            self._save(str(base) + '.npy', np.asarray(value, dtype=np.float32))
            meta = {'kind': 'dense', 'shape': list(value.shape)}
        tmp = self._meta_path(name).with_suffix('.json.tmp')
        tmp.write_text(json.dumps(meta))
        os.replace(tmp, self._meta_path(name))  # the sidecar lands last, so a present sidecar means a complete entry

    @staticmethod
    def _save(path: str, arr: np.ndarray) -> None:
        tmp = path + '.tmp'
        with open(tmp, 'wb') as f:
            np.save(f, np.ascontiguousarray(arr))
        os.replace(tmp, path)

    def nbytes(self) -> int:
        return sum(p.stat().st_size for p in self.root.glob('*.npy'))

    def checksum(self) -> str:
        """SHA-256 over every entry (names, metadata, array bytes): equal on two machines <=> identical weights."""

        h = hashlib.sha256()
        for mp in sorted(self.root.glob('*.json')):
            h.update(mp.name.encode())
            h.update(mp.read_bytes())
            for arr in sorted(self.root.glob(mp.name[:-len('.json')] + '*.npy')):
                h.update(arr.name.encode())
                with open(arr, 'rb') as f:
                    while True:
                        chunk = f.read(1 << 24)
                        if not chunk:
                            break
                        h.update(chunk)
        return h.hexdigest()


if __name__ == '__main__':  # python -m omllm.local.qwen.paramcache CACHE_DIR/<entry>  -> its checksum
    import sys

    for d in sys.argv[1:]:
        pc = ParamCache(pathlib.Path(d))
        print(f'{pc.checksum()}  {d}  ({len(list(pc.root.glob("*.json")))} entries, {pc.nbytes() / 2**30:.2f} GiB)')
