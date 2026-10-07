import io
import sys
import types

import pytest

from .. import tesseract


##


def test_options(monkeypatch):
    calls = []

    def image_to_string(image, **kwargs):
        calls.append((image, kwargs))
        return 'Open\nSave\n'

    monkeypatch.setattr(tesseract, 'pytesseract', types.SimpleNamespace(image_to_string=image_to_string))  # Noqa
    image = object()
    backend = tesseract.TesseractOcrBackend(language='eng', timeout=12.)
    assert backend.ocr(image) == 'Open\nSave\n'  # type: ignore
    assert calls == [(image, {'lang': 'eng', 'config': '--oem 1 --psm 6', 'nice': 0, 'timeout': 12.})]


def test_uv_worker_options(monkeypatch):
    image_module = pytest.importorskip('PIL.Image')
    calls = []

    def image_to_string(image, **kwargs):
        calls.append((image.size, kwargs))
        return 'résumé\n'

    monkeypatch.setitem(sys.modules, 'pytesseract', types.SimpleNamespace(image_to_string=image_to_string))
    with image_module.new('RGB', (4, 2)) as image:
        out = io.BytesIO()
        image.save(out, format='PNG')

    assert tesseract._uv_tesseract_ocr(  # noqa
        out.getvalue(),
        config='--psm 7',
        language='eng+fra',
        timeout=20.,
    ) == 'résumé\n'
    assert calls == [((4, 2), {'lang': 'eng+fra', 'config': '--psm 7', 'nice': 0, 'timeout': 20.})]
