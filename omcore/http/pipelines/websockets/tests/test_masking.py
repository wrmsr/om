# ruff: noqa: PT009 PT027
# @om-lite
import unittest

from ..frames import IoPipelineWebsocketFrames


def _mask_xor_reference(data, key):
    out = bytearray(len(data))
    k0, k1, k2, k3 = key
    for i, b in enumerate(data):
        j = i & 3
        kb = k0 if j == 0 else k1 if j == 1 else k2 if j == 2 else k3
        out[i] = b ^ kb
    return bytes(out)


class TestMaskXor(unittest.TestCase):
    KEYS = (
        b'\x00\x00\x00\x00',
        b'\xff\xff\xff\xff',
        b'\x124Vx',
        b'\x01\x02\x03\x04',
    )

    def test_matches_reference(self) -> None:
        for n in (*range(70), 125, 126, 127, 4096, 65536 + 3):
            data = bytes((i * 31 + 7) & 0xff for i in range(n))
            for key in self.KEYS:
                self.assertEqual(
                    IoPipelineWebsocketFrames.mask_xor(data, key),
                    _mask_xor_reference(data, key),
                    (n, key),
                )

    def test_roundtrip(self) -> None:
        data = bytes((i * 17 + 3) & 0xff for i in range(1000))
        for key in self.KEYS:
            masked = IoPipelineWebsocketFrames.mask_xor(data, key)
            self.assertEqual(IoPipelineWebsocketFrames.mask_xor(masked, key), data)

    def test_bad_key_length(self) -> None:
        with self.assertRaises(ValueError):
            IoPipelineWebsocketFrames.mask_xor(b'abc', b'\x01\x02\x03')
        with self.assertRaises(ValueError):
            IoPipelineWebsocketFrames.mask_xor(b'abc', b'\x01\x02\x03\x04\x05')
