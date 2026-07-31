import math
import struct

import pytest

from ..floats import bytes_to_float
from ..floats import float_to_bytes
from ..floats import isclose


@pytest.mark.parametrize(('a', 'b'), [
    (1., 1. + 1e-10),
    (1., 1. + 1e-8),
    (0., 1e-10),
    (float('inf'), float('inf')),
    (float('-inf'), float('-inf')),
    (float('inf'), float('-inf')),
    (float('nan'), float('nan')),
])
def test_isclose_matches_stdlib(a, b):
    assert isclose(a, b) is math.isclose(a, b)


def test_isclose_rejects_negative_tolerances():
    with pytest.raises(ValueError, match='tolerances must be non-negative'):
        isclose(1., 1., rel_tol=-1.)
    with pytest.raises(ValueError, match='tolerances must be non-negative'):
        isclose(1., 1., abs_tol=-1.)


def test_float_bytes():
    assert float_to_bytes(1.5) == bytes.fromhex('3fc00000')
    assert bytes_to_float(float_to_bytes(-123.25)) == -123.25
    assert math.isnan(bytes_to_float(float_to_bytes(float('nan'))))

    with pytest.raises(struct.error):
        bytes_to_float(b'bad')
