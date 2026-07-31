import pytest

from ..c import cdiv
from ..c import cmod


@pytest.mark.parametrize(('x', 'y', 'quotient', 'remainder'), [
    (7, 3, 2, 1),
    (-7, 3, -2, -1),
    (7, -3, -2, 1),
    (-7, -3, 2, -1),
])
def test_c_arithmetic(x, y, quotient, remainder):
    assert cdiv(x, y) == quotient
    assert cmod(x, y) == remainder
    assert x == quotient * y + remainder


def test_c_arithmetic_zero_divisor():
    assert cdiv(1, 0) == 0
    assert cmod(1, 0) == 1
