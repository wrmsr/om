import pytest

from ..codes import BG8_216
from ..codes import BG8_GRAYSCALE
from ..codes import CSI
from ..codes import FG8_216
from ..codes import FG8_GRAYSCALE
from ..codes import FG8_HIGH_INTENSITY
from ..codes import FG8_STANDARD


@pytest.mark.parametrize(('control', 'size', 'offset'), [
    (FG8_STANDARD, 8, 0),
    (FG8_HIGH_INTENSITY, 8, 8),
    (FG8_216, 216, 16),
    (BG8_216, 216, 16),
    (FG8_GRAYSCALE, 24, 232),
    (BG8_GRAYSCALE, 24, 232),
])
def test_indexed_color_palette_bounds(control, size, offset):
    assert control(0).startswith(CSI)
    assert f';{offset}m' in control(0)
    assert f';{offset + size - 1}m' in control(size - 1)

    with pytest.raises(ValueError, match='-1'):
        control(-1)
    with pytest.raises(ValueError, match=str(size)):
        control(size)
