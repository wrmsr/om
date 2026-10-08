import os.path

import pytest

from ..cli import _get_image_data
from ..cli import _make_parser
from ..cli import _run_ocr
from ..cli import _select_backend_name
from ..types import OcrBackend


##


def test_default_and_options():
    args = _make_parser().parse_args([])
    assert args.backend == 'rapidocr'
    assert args.file is None
    assert args.tesseract_config == '--oem 1 --psm 6'

    args = _make_parser().parse_args([
        '-b', 'rapidocr-torch',
        '--torch-device', 'mps',
        '--vision-language', 'en-US',
        '--vision-language', 'fr-FR',
        '@',
    ])
    assert args.torch_device == 'mps'
    assert args.vision_language == ['en-US', 'fr-FR']
    assert args.file == '@'


@pytest.mark.parametrize(('name', 'expected'), [
    ('rapidocr', 'rapidocr-onnx-uv'),
    ('rapidocr-onnx', 'rapidocr-onnx-uv'),
    ('rapidocr-torch', 'rapidocr-torch-uv'),
])
def test_uv_selection(name, expected):
    assert _select_backend_name(name, uv=True) == expected
    assert _select_backend_name(name, uv=False) == name


def test_invalid_uv_selection():
    with pytest.raises(ValueError):  # noqa
        _select_backend_name('darwin', uv=True)


def test_filename_expansion():
    assert _get_image_data('~/ocr.png') == os.path.expanduser('~/ocr.png')


def test_image_lifetime(tmp_path):
    image_module = pytest.importorskip('PIL.Image')
    filename = os.path.join(str(tmp_path), 'image.png')
    with image_module.new('RGB', (6, 4), (10, 20, 30)) as image:
        image.save(filename)

    class Backend(OcrBackend):
        def is_available(self):
            return True

        def ocr(self, image):
            assert image.getpixel((0, 0)) == (10, 20, 30)
            assert image.size == (6, 4)
            return 'recognized'

    assert _run_ocr(filename, Backend()) == 'recognized'
