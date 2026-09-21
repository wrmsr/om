import abc
import typing as ta

from omcore import lang

from ..entries import SessionEntry


##


class SessionNotFoundError(Exception):
    pass


##


class SessionStorage(lang.SelfAsyncContextManaged, lang.Abstract):
    @abc.abstractmethod
    def get_entries(self) -> ta.Awaitable[ta.Sequence[SessionEntry]]:
        raise NotImplementedError

    @abc.abstractmethod
    def add_entry(self, *entries: SessionEntry) -> ta.Awaitable[None]:
        raise NotImplementedError
