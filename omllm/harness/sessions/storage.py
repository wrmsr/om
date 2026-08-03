import abc
import typing as ta

from omcore import lang

from .entries import SessionEntry


##


class SessionStorage(lang.Abstract):
    @abc.abstractmethod
    def add_entry(self, *entries: SessionEntry) -> ta.Awaitable[None]:
        raise NotImplementedError


##


class InMemorySessionStorage(SessionStorage):
    def __init__(self) -> None:
        super().__init__()

        self._entries: list[SessionEntry] = []

    async def add_entry(self, *entries: SessionEntry) -> None:
        self._entries.extend(entries)
