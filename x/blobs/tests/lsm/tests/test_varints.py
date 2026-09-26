import pytest

from ..varints import decode_uvarint
from ..varints import encode_uvarint


def test_round_trip():
    for n in [0, 1, 127, 128, 255, 300, 16383, 16384, 2 ** 32, 2 ** 63 - 1]:
        b = encode_uvarint(n)
        assert decode_uvarint(b + b'xx', 0) == (n, len(b))
    assert encode_uvarint(0) == b'\x00'
    assert encode_uvarint(300) == b'\xac\x02'


def test_errors():
    with pytest.raises(ValueError):  # noqa
        encode_uvarint(-1)
    with pytest.raises(ValueError):  # noqa
        decode_uvarint(b'\x80', 0)
    with pytest.raises(ValueError):  # noqa
        decode_uvarint(b'\xff' * 11, 0)
