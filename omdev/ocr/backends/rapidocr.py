"""
The modern rapidocr package, with an explicitly selected ONNX Runtime or native Torch engine for all three stages.
PP-OCRv4 mobile models are selected explicitly rather than inheriting changing package defaults.
"""
import os.path
import typing as ta

from omcore import lang

from ..images import get_image_png_bytes
from ..types import OcrBackend
from .uv import DEFAULT_UV_PYTHON
from .uv import DEFAULT_UV_TIMEOUT
from .uv import UvOcrBackend


with lang.auto_proxy_import(globals()):
    import rapidocr  # type: ignore[import-not-found,unused-ignore]
    from PIL import Image


##


DEFAULT_UV_DEPS = (
    'pillow>=12.3.0,<13',
    'omegaconf>=2.3.0,<3',
    'rapidocr>=3.9.2,<4',
)

DEFAULT_UV_MODEL_ROOT_DIR = '~/.cache/omdev/ocr/rapidocr'


##


def _get_params(
        engine: str,
        device: str,
        *,
        model_root_dir: str | None = None,
) -> dict[str, ta.Any]:
    if engine not in ('onnxruntime', 'torch'):
        raise ValueError(engine)
    if device not in ('cpu', 'cuda', 'mps') or (engine != 'torch' and device != 'cpu'):
        raise ValueError((engine, device))

    params: dict[str, ta.Any] = {}

    params['Global.log_level'] = 'WARNING'

    for stage in ('Det', 'Cls', 'Rec'):
        params[f'{stage}.engine_type'] = engine
        params[f'{stage}.ocr_version'] = 'PP-OCRv4'
        params[f'{stage}.model_type'] = 'mobile'
        params[f'{stage}.lang_type'] = 'ch'

    if model_root_dir is not None:
        params['Global.model_root_dir'] = model_root_dir

    if engine == 'torch':
        params['EngineConfig.torch.use_cuda'] = device == 'cuda'
        params['EngineConfig.torch.use_mps'] = device == 'mps'

    return params


def _convert_params(params: ta.Mapping[str, ta.Any]) -> dict[str, ta.Any]:
    enum_types = {
        'engine_type': rapidocr.EngineType,
        'ocr_version': rapidocr.OCRVersion,
        'model_type': rapidocr.ModelType,
    }
    converted = {
        key: enum_types[field](value) if (field := key.rsplit('.', 1)[-1]) in enum_types else value
        for key, value in params.items()
    }
    if 'Global.model_root_dir' in converted:
        converted['Global.model_root_dir'] = os.path.expanduser(converted['Global.model_root_dir'])  # type: ignore[arg-type,unused-ignore]  # noqa
    return converted


class RapidocrOcrBackend(OcrBackend):
    def __init__(
            self,
            *,
            engine: str = 'onnxruntime',
            device: str = 'cpu',
            model_root_dir: str | None = None,
    ) -> None:
        super().__init__()

        self._engine = engine
        self._params = _get_params(engine, device, model_root_dir=model_root_dir)

    def is_available(self) -> bool:
        return lang.can_import('rapidocr') and lang.can_import(self._engine)

    def ocr(self, image: Image.Image) -> str:
        result = rapidocr.RapidOCR(params=_convert_params(self._params))(get_image_png_bytes(image))

        return '\n'.join(result.txts if result.txts is not None else ())  # type: ignore[union-attr,unused-ignore]


##


def _uv_rapidocr_ocr(png: bytes, *, params: dict) -> str:
    import os.path

    import rapidocr

    # This small enum conversion is duplicated so the extracted worker has no dependency on its containing module.
    enum_types = {
        'engine_type': rapidocr.EngineType,
        'ocr_version': rapidocr.OCRVersion,
        'model_type': rapidocr.ModelType,
    }
    converted = {
        key: enum_types[field](value) if (field := key.rsplit('.', 1)[-1]) in enum_types else value
        for key, value in params.items()
    }
    if 'Global.model_root_dir' in converted:
        converted['Global.model_root_dir'] = os.path.expanduser(converted['Global.model_root_dir'])  # type: ignore[arg-type,unused-ignore]  # noqa

    result = rapidocr.RapidOCR(params=converted)(png)

    return '\n'.join(result.txts if result.txts is not None else ())  # type: ignore[union-attr,unused-ignore]


class UvRapidocrOcrBackend(UvOcrBackend):
    def __init__(
            self,
            *,
            engine: str = 'onnxruntime',
            device: str = 'cpu',
            model_root_dir: str | None = None,
            uv: str = 'uv',
            python: str = DEFAULT_UV_PYTHON,
            timeout: float = DEFAULT_UV_TIMEOUT,
    ) -> None:
        super().__init__(
            requirements=(
                *DEFAULT_UV_DEPS,
                engine,
            ),
            kwargs={
                'params': _get_params(
                    engine,
                    device,
                    model_root_dir=model_root_dir if model_root_dir is not None else DEFAULT_UV_MODEL_ROOT_DIR,
                ),
            },
            uv=uv,
            python=python,
            timeout=timeout,
        )

    def _get_worker(self) -> ta.Callable[..., str]:
        return _uv_rapidocr_ocr
