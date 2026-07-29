import abc
import typing as ta

from omcore import lang

from .text import CanUiText
from .text import UiText


##


class UiTextDisplayer(lang.Abstract):
    @abc.abstractmethod
    def display_ui_text(self, text: CanUiText) -> ta.Awaitable[None]:
        pass


class NopUiTextDisplayer(UiTextDisplayer):
    async def display_ui_text(self, text: CanUiText) -> None:
        pass


class PrintUiTextDisplayer(UiTextDisplayer):
    async def display_ui_text(self, text: CanUiText) -> None:
        print(UiText.str_of(text))
