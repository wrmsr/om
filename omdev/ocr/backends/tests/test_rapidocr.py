import enum
import os.path
import sys
import types

import pytest

from ...tests.helpers import PngImage
from .. import rapidocr
from .. import rapidocrort


##


class _EngineType(enum.Enum):
    ONNXRUNTIME = 'onnxruntime'
    TORCH = 'torch'


class _OcrVersion(enum.Enum):
    PPOCRV4 = 'PP-OCRv4'


class _ModelType(enum.Enum):
    MOBILE = 'mobile'


def _make_library(txts, calls):
    class Engine:
        def __init__(self, *, params):
            super().__init__()
            calls.append(params)

        def __call__(self, png):
            assert png == b'\x89PNG\r\n\x1a\n'
            return types.SimpleNamespace(txts=txts)

    return types.SimpleNamespace(
        EngineType=_EngineType,
        OCRVersion=_OcrVersion,
        ModelType=_ModelType,
        RapidOCR=Engine,
    )


@pytest.mark.parametrize(('engine', 'device'), [
    ('onnxruntime', 'cpu'),
    ('torch', 'cpu'),
    ('torch', 'cuda'),
    ('torch', 'mps'),
])
@pytest.mark.parametrize(('txts', 'expected'), [
    (None, ''),
    ((), ''),
    (('Open', 'Save'), 'Open\nSave'),
])
def test_modern_and_uv_parameters(
        monkeypatch,
        engine,
        device,
        txts,
        expected,
):
    calls: list = []
    library = _make_library(txts, calls)
    monkeypatch.setattr(rapidocr, 'rapidocr', library)  # noqa
    monkeypatch.setitem(sys.modules, 'rapidocr', library)

    backend = rapidocr.RapidocrOcrBackend(engine=engine, device=device)
    assert backend.ocr(PngImage()) == expected  # type: ignore
    assert rapidocr._uv_rapidocr_ocr(PngImage().data, params=rapidocr._get_params(engine, device)) == expected  # noqa
    assert calls[0] == calls[1]

    for stage in ('Det', 'Cls', 'Rec'):
        assert calls[0][f'{stage}.engine_type'] is _EngineType(engine)
        assert calls[0][f'{stage}.ocr_version'] is _OcrVersion.PPOCRV4
        assert calls[0][f'{stage}.model_type'] is _ModelType.MOBILE
        assert calls[0][f'{stage}.lang_type'] == 'ch'

    if engine == 'torch':
        assert calls[0]['EngineConfig.torch.use_cuda'] is (device == 'cuda')
        assert calls[0]['EngineConfig.torch.use_mps'] is (device == 'mps')


@pytest.mark.parametrize(('engine', 'device'), [
    ('bad', 'cpu'),
    ('onnxruntime', 'mps'),
    ('torch', 'bad'),
])
def test_invalid_configuration(engine, device):
    with pytest.raises(ValueError):  # noqa
        rapidocr.RapidocrOcrBackend(engine=engine, device=device)
    with pytest.raises(ValueError):  # noqa
        rapidocr.UvRapidocrOcrBackend(engine=engine, device=device)


@pytest.mark.parametrize(('rows', 'expected'), [
    (None, ''),
    ([], ''),
    ([(None, 'Open', .99), (None, 'Save', .98)], 'Open\nSave'),
])
def test_legacy(monkeypatch, rows, expected):
    class Engine:
        def __call__(self, png):
            assert png == PngImage().data
            return rows, [0., 0., 0.]

    monkeypatch.setattr(rapidocrort, 'rapidocr_onnxruntime', types.SimpleNamespace(RapidOCR=Engine))  # noqa
    assert rapidocrort.RapidocrOnnxruntimeOcrBackend().ocr(PngImage()) == expected  # type: ignore


def test_model_directory(monkeypatch):
    calls: list = []
    library = _make_library(None, calls)
    monkeypatch.setattr(rapidocr, 'rapidocr', library)  # noqa
    monkeypatch.setitem(sys.modules, 'rapidocr', library)

    directory = '~/ocr models'
    rapidocr.RapidocrOcrBackend(model_root_dir=directory).ocr(PngImage())  # type: ignore
    params = rapidocr._get_params('onnxruntime', 'cpu', model_root_dir=directory)  # noqa
    rapidocr._uv_rapidocr_ocr(PngImage().data, params=params)  # noqa
    assert calls[0] == calls[1]
    assert calls[0]['Global.model_root_dir'] == os.path.expanduser(directory)
    assert params['Global.model_root_dir'] == directory
