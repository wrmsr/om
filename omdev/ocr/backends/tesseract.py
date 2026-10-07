"""
Both variants require the tesseract executable and its language data on the host; uv only installs Python packages.
The default config selects LSTM recognition of a uniform text block. tessdata_best must be installed separately.
"""
import typing as ta

from omcore import lang

from ..types import OcrBackend
from .uv import DEFAULT_UV_PYTHON
from .uv import DEFAULT_UV_TIMEOUT
from .uv import UvOcrBackend


with lang.auto_proxy_import(globals()):
    import pytesseract
    from PIL import Image


##


DEFAULT_TESSERACT_CONFIG = '--oem 1 --psm 6'


class TesseractOcrBackend(OcrBackend):
    def __init__(
            self,
            *,
            config: str = DEFAULT_TESSERACT_CONFIG,
            language: str | None = None,
            timeout: float = 300.,
    ) -> None:
        super().__init__()

        if timeout <= 0:
            raise ValueError(timeout)
        self._config = config
        self._language = language
        self._timeout = timeout

    def is_available(self) -> bool:
        return lang.can_import('pytesseract')

    def ocr(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(
            image,
            lang=self._language,
            config=self._config,
            nice=0,
            timeout=self._timeout,
        )


##


def _uv_tesseract_ocr(png: bytes, *, config: str, language: str | None, timeout: float) -> str:
    import io

    import pytesseract
    from PIL import Image

    with Image.open(io.BytesIO(png)) as image:
        return pytesseract.image_to_string(
            image,
            lang=language,
            config=config,
            nice=0,
            timeout=timeout,
        )


class UvTesseractOcrBackend(UvOcrBackend):
    def __init__(
            self,
            *,
            config: str = DEFAULT_TESSERACT_CONFIG,
            language: str | None = None,
            uv: str = 'uv',
            python: str = DEFAULT_UV_PYTHON,
            timeout: float = DEFAULT_UV_TIMEOUT,
    ) -> None:
        super().__init__(
            requirements=('pillow', 'pytesseract'),
            kwargs={'config': config, 'language': language, 'timeout': timeout},
            uv=uv,
            python=python,
            timeout=timeout,
        )

    def _get_worker(self) -> ta.Callable[..., str]:
        return _uv_tesseract_ocr
