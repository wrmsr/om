import io

import pytest

from ..images import get_image_png_bytes


##


def test_png_roundtrip():
    image_module = pytest.importorskip('PIL.Image')
    with image_module.new('RGBA', (5, 3), (12, 34, 56, 78)) as original:
        png = get_image_png_bytes(original)
        assert png.startswith(b'\x89PNG\r\n\x1a\n')
        with image_module.open(io.BytesIO(png)) as decoded:
            assert decoded.mode == original.mode
            assert decoded.size == original.size
            assert decoded.tobytes() == original.tobytes()
        assert original.getpixel((0, 0)) == (12, 34, 56, 78)
