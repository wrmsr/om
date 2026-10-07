"""The legacy rapidocr-onnxruntime package, with the same invocation and text extraction as omdev.tools.ocr."""
from omcore import lang

from ..images import get_image_png_bytes
from ..types import OcrBackend


with lang.auto_proxy_import(globals()):
    import rapidocr_onnxruntime
    from PIL import Image


##


class RapidocrOnnxruntimeOcrBackend(OcrBackend):
    def is_available(self) -> bool:
        return lang.can_import('rapidocr_onnxruntime')

    def ocr(self, image: Image.Image) -> str:
        result, _ = rapidocr_onnxruntime.RapidOCR()(get_image_png_bytes(image))
        return '\n'.join(item[1] for item in result or ())
