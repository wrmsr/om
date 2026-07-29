import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


class QuitSignal(lang.Abstract):
    @abc.abstractmethod
    def quit(self) -> ta.Awaitable[None]:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class RaiseQuitSignal(QuitSignal):
    exc: BaseException | type[BaseException]

    async def quit(self) -> None:
        raise self.exc
