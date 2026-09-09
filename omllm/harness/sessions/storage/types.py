import abc
import typing as ta

from omcore import lang

from ..entries import SessionEntry


##


class SessionStorage(lang.SelfAsyncContextManaged, lang.Abstract):
    @abc.abstractmethod
    def add_entry(self, *entries: SessionEntry) -> ta.Awaitable[None]:
        raise NotImplementedError
