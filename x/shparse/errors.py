import abc

from omcore import dataclasses as dc
from omcore import lang


##


class Error(lang.Abstract):
    def __str__(self) -> str:
        return self.message

    @property
    @abc.abstractmethod
    def message(self) -> str:
        raise NotImplementedError


@dc.dataclass()
class GenericError(Error):
    s: str

    @property
    def message(self) -> str:
        return self.s
