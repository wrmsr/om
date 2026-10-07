import sys
import typing as ta

from omcore import lang

from ..images import get_image_png_bytes
from ..types import OcrBackend


with lang.auto_proxy_import(globals()):
    from PIL import Image

    from ...capi.darwin import vn


##


class DarwinOcrBackend(OcrBackend):
    def __init__(
            self,
            *,
            languages: ta.Sequence[str] | None = None,
            fast: bool = False,
            no_language_correction: bool = False,
    ) -> None:
        super().__init__()

        if isinstance(languages, str):
            raise TypeError(languages)
        self._languages = tuple(languages) if languages is not None else None
        self._fast = fast
        self._no_language_correction = no_language_correction

    def is_available(self) -> bool:
        return getattr(sys, 'platform') == 'darwin'

    def ocr(self, image: Image.Image) -> str:
        return vn.recognize_text(
            get_image_png_bytes(image),
            languages=self._languages,
            fast=self._fast,
            no_language_correction=self._no_language_correction,
        )
