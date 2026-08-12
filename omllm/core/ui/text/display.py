import abc
import typing as ta

from omcore import lang

from .types import CanText
from .types import Text


##


class TextDisplayer(lang.Abstract):
    @abc.abstractmethod
    def display_text(self, text: CanText) -> ta.Awaitable[None]:
        raise NotImplementedError


class NopTextDisplayer(TextDisplayer):
    async def display_text(self, text: CanText) -> None:
        pass


class PrintTextDisplayer(TextDisplayer):
    def __init__(
            self,
            *,
            file: lang.SupportsWrite[str] | None = None,
    ) -> None:
        super().__init__()

        self._file = file

    async def display_text(self, text: CanText) -> None:
        print(Text.str_of(text), end='', file=self._file)
