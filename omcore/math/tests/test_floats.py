import math
import struct

import pytest

from ..floats import bytes_to_float
from ..floats import float_to_bytes


def test_float_bytes():
    assert float_to_bytes(1.5) == bytes.fromhex('3fc00000')
    assert bytes_to_float(float_to_bytes(-123.25)) == -123.25
    assert math.isnan(bytes_to_float(float_to_bytes(float('nan'))))

    with pytest.raises(struct.error):
        bytes_to_float(b'bad')
