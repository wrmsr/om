import abc
import typing as ta

from omcore import lang
from omcore import marshal as msh

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
        if not entries:
            return

        self._entries.extend(entries)


##


class JsonlSessionStorage(SessionStorage):
    def __init__(
            self,
            *,
            file_path: str,
    ) -> None:
        super().__init__()

        self._file_path = file_path

    async def add_entry(self, *entries: SessionEntry) -> None:
        if not entries:
            return

        mvs = [  # noqa
            msh.marshal(e, SessionEntry)
            for e in entries
        ]

        raise NotImplementedError
