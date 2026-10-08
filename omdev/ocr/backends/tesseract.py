"""
Requires the tesseract executable and its language data on the host.
PNG is sent on stdin; UTF-8 text is read from stdout.
The default config selects LSTM recognition of a uniform text block. tessdata_best must be installed separately.
"""
import shlex
import shutil
import subprocess

from omcore import lang

from ..images import get_image_png_bytes
from ..types import OcrBackend


with lang.auto_proxy_import(globals()):
    from PIL import Image


##


DEFAULT_TESSERACT_CONFIG = '--oem 1 --psm 6'


class TesseractOcrBackend(OcrBackend):
    def __init__(
            self,
            *,
            config: str = DEFAULT_TESSERACT_CONFIG,
            language: str | None = None,
            executable: str = 'tesseract',
            timeout: float = 300.,
    ) -> None:
        super().__init__()

        if timeout <= 0:
            raise ValueError(timeout)
        self._config = config
        self._language = language
        self._executable = executable
        self._timeout = timeout

    def is_available(self) -> bool:
        return shutil.which(self._executable) is not None

    def ocr(self, image: Image.Image) -> str:
        png = get_image_png_bytes(image)

        cmd = [self._executable, 'stdin', 'stdout']
        if self._language is not None:
            cmd.extend(['-l', self._language])
        cmd.extend(shlex.split(self._config))
        cmd.append('txt')

        # Keep stderr on the caller's diagnostic channel, separate from the recognized text.
        return subprocess.check_output(  # noqa
            cmd,
            input=png,
            timeout=self._timeout,
        ).decode('utf-8')
