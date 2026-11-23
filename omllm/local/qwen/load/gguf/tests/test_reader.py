"""
The vendored gguf reader on files written by hand: a small valid one, a tensor of a type upstream added after the
fork was first taken, and the malformed ones upstream's reader has since learned to refuse rather than read past the
end of, or allocate for.
"""
import os.path
import struct

import numpy as np
import pytest

from ..constants import GGUF_DEFAULT_ALIGNMENT
from ..constants import GGUF_MAGIC
from ..constants import GGUF_VERSION
from ..constants import GGMLQuantizationType
from ..constants import GGUFValueType
from ..quants import dequantize
from ..reader import GGUFReader


##


def _string(s: bytes, length: int | None = None) -> bytes:
    return struct.pack('<Q', len(s) if length is None else length) + s


def _tensor_info(name: bytes, dims: tuple[int, ...], qtype: int, offset: int = 0) -> bytes:
    return b''.join([
        _string(name),
        struct.pack('<I', len(dims)),
        struct.pack(f'<{len(dims)}Q', *dims),
        struct.pack('<IQ', qtype, offset),
    ])


def _write(
        tmp_path,
        *,
        tensor_infos: bytes = b'',
        n_tensors: int = 0,
        kvs: bytes = b'',
        n_kvs: int = 0,
        data: bytes = b'',
) -> str:
    head = struct.pack('<IIQQ', GGUF_MAGIC, GGUF_VERSION, n_tensors, n_kvs) + kvs + tensor_infos
    head += b'\0' * (-len(head) % GGUF_DEFAULT_ALIGNMENT)

    path = os.path.join(str(tmp_path), f'f{len(os.listdir(str(tmp_path)))}.gguf')
    with open(path, 'wb') as f:
        f.write(head + data)
    return path


ARCH = _string(b'general.architecture') + struct.pack('<I', GGUFValueType.STRING) + _string(b'tiny')


def test_reads_a_small_file(tmp_path):
    w = np.arange(6, dtype=np.float32)
    codes = np.array([0x38, 0xB8, 0x00, 0x7E], dtype=np.uint8)  # 1, -1, 0, 448 as e4m3
    data = w.tobytes() + b'\0' * 8 + codes.tobytes()

    r = GGUFReader(_write(
        tmp_path,
        kvs=ARCH,
        n_kvs=1,
        tensor_infos=(
            _tensor_info(b'w', (3, 2), GGMLQuantizationType.F32) +
            _tensor_info(b'c', (4,), GGMLQuantizationType.F8_E4M3, 32)
        ),
        n_tensors=2,
        data=data,
    ))

    assert r.fields['general.architecture'].contents() == 'tiny'

    t, c = r.tensors
    assert (t.name, t.tensor_type, t.shape.tolist()) == ('w', GGMLQuantizationType.F32, [3, 2])
    assert np.array_equal(t.data, w.reshape(2, 3))  # (dimensions are stored innermost first)

    # a type the reader did not know before the fork was brought up to date: read as its bytes, and decodable
    assert (c.tensor_type, c.data.dtype, c.data.tolist()) == (GGMLQuantizationType.F8_E4M3, np.uint8, codes.tolist())
    assert dequantize(np.asarray(c.data).reshape(1, 4), c.tensor_type).tolist() == [[1., -1., 0., 448.]]


def test_refuses_what_does_not_fit(tmp_path):
    w = np.arange(6, dtype=np.float32).tobytes()

    def read(**kw) -> GGUFReader:
        return GGUFReader(_write(tmp_path, **kw))

    # a tensor whose data runs past the end of the file
    with pytest.raises(ValueError, match='exceeds file size'):
        read(tensor_infos=_tensor_info(b'w', (3, 2), GGMLQuantizationType.F32), n_tensors=1, data=w[:-4])

    # ... whose element count wraps 64 bits if it is multiplied in numpy
    with pytest.raises(ValueError, match='exceeds file size'):
        read(tensor_infos=_tensor_info(b'w', (1 << 33, 1 << 33), GGMLQuantizationType.F32), n_tensors=1, data=w)

    # more dimensions than a tensor has
    with pytest.raises(ValueError, match='GGML_MAX_DIMS'):
        read(tensor_infos=_tensor_info(b'w', (1, 1, 1, 2, 3), GGMLQuantizationType.F32), n_tensors=1, data=w)

    # counts and lengths no file could hold
    with pytest.raises(ValueError, match='Tensor count'):
        read(n_tensors=1 << 31)
    with pytest.raises(ValueError, match='KV count'):
        read(n_kvs=1 << 31)
    with pytest.raises(ValueError, match=r'String length .* exceeds maximum'):
        read(kvs=_string(b'k', 1 << 31), n_kvs=1)
    with pytest.raises(ValueError, match=r'String length .* exceeds remaining file size'):
        read(kvs=_string(b'k', 1000), n_kvs=1)

    array = struct.pack('<I', GGUFValueType.ARRAY) + struct.pack('<IQ', GGUFValueType.UINT8, 1 << 31)
    with pytest.raises(ValueError, match='Array length'):
        read(kvs=_string(b'a') + array, n_kvs=1)
