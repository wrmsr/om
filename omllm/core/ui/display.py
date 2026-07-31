import abc
import typing as ta

from omcore import lang

from .text import CanText
from .text import Text


##


class TextDisplayer(lang.Abstract):
    @abc.abstractmethod
    def display_text(self, text: CanText) -> ta.Awaitable[None]:
        raise NotImplementedError


class NopTextDisplayer(TextDisplayer):
    async def display_text(self, text: CanText) -> None:
        pass


class PrintTextDisplayer(TextDisplayer):
    async def display_text(self, text: CanText) -> None:
        print(Text.str_of(text))
