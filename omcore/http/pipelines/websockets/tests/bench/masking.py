# ruff: noqa: UP006 UP045
# @om-lite
"""Websocket payload masking: the big-int xor trick vs the naive per-byte python loop it replaced."""
from ......io.streambufs.tests.bench.harness import bench
from ......io.streambufs.tests.bench.harness import report
from ...frames import IoPipelineWebsocketFrames


##


def _mask_xor_naive(data: bytes, key: bytes) -> bytes:
    out = bytearray(len(data))
    k0, k1, k2, k3 = key
    for i, b in enumerate(data):
        j = i & 3
        kb = k0 if j == 0 else k1 if j == 1 else k2 if j == 2 else k3
        out[i] = b ^ kb
    return bytes(out)


_KEY = b'\x124Vx'


def _main() -> None:
    for n in (125, 4096, 65536, 1024 * 1024):
        data = bytes((i * 31 + 7) & 0xff for i in range(n))

        if IoPipelineWebsocketFrames.mask_xor(data, _KEY) != _mask_xor_naive(data, _KEY):
            raise RuntimeError('mask_xor mismatch')

        results = [
            bench('naive_byte_loop', lambda: _mask_xor_naive(data, _KEY), bytes_per_op=n),
            bench('int_xor', lambda: IoPipelineWebsocketFrames.mask_xor(data, _KEY), bytes_per_op=n),
        ]
        report(f'mask_xor: {n} B payload', results, baseline='naive_byte_loop')


if __name__ == '__main__':
    _main()
