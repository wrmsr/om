"""
Install the standalone executable with: cargo install ocrs-cli --locked

PNG is sent on stdin; plain text is read from stdout. Model downloads/cache management belong to ocrs itself.
No clipboard feature, Rust extension, or in-process binding is needed.
"""
import shutil
import subprocess

from omcore import lang

from ..images import get_image_png_bytes
from ..types import OcrBackend


with lang.auto_proxy_import(globals()):
    from PIL import Image


##


class OcrsOcrBackend(OcrBackend):
    def __init__(self, *, executable: str = 'ocrs', timeout: float = 300.) -> None:
        super().__init__()

        if timeout <= 0:
            raise ValueError(timeout)
        self._executable = executable
        self._timeout = timeout

    def is_available(self) -> bool:
        return shutil.which(self._executable) is not None

    def ocr(self, image: Image.Image) -> str:
        return subprocess.check_output(
            [self._executable],
            input=get_image_png_bytes(image),
            timeout=self._timeout,
        ).decode('utf-8')
