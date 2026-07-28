import abc
import typing as ta

from omcore import lang


##


class PermissionGranter(lang.Abstract):
    @abc.abstractmethod
    def grant_permission(self, message: str) -> ta.Awaitable[bool]:
        raise NotImplementedError
