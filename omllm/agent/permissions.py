import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


class PermissionGranter(lang.Abstract):
    @abc.abstractmethod
    def grant_permission(self, message: str) -> ta.Awaitable[bool]:
        raise NotImplementedError


##


@dc.dataclass(frozen=True)
class ConstantPermissionGranter(PermissionGranter):
    granted: bool

    async def grant_permission(self, message: str) -> bool:
        return self.granted
