import abc
import typing as ta

from omcore import check
from omcore import lang

from .. import llm


BackendT = ta.TypeVar('BackendT', bound=llm.Backend)


##


class BackendManager(lang.Abstract):
    @abc.abstractmethod
    def get_backend(self, cls: type[BackendT], model: llm.Model | None = None) -> BackendT:
        raise NotImplementedError


##


class DictBackendManager(BackendManager):
    def __init__(
            self,
            dct: ta.Mapping[type[llm.Backend], ta.Mapping[llm.Model | None, llm.Backend]],
    ) -> None:
        super().__init__()

        self._dct = dct

    def get_backend(self, cls: type[BackendT], model: llm.Model | None = None) -> BackendT:
        return check.isinstance(self._dct[cls][model], cls)
