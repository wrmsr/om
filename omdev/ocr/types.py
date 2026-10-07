import abc

from omcore import lang


with lang.auto_proxy_import(globals()):
    from PIL import Image


##


class OcrBackend(lang.Abstract):
    @abc.abstractmethod
    def is_available(self) -> bool:
        """A shallow prerequisite check, not an import or execution probe."""

        raise NotImplementedError

    @abc.abstractmethod
    def ocr(self, image: Image.Image) -> str:
        raise NotImplementedError
