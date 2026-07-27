import abc
import typing as ta

from omcore import lang

from .. import llm


BackendT = ta.TypeVar('BackendT', bound=llm.Backend)


##


class BackendManager(lang.Abstract):
    @abc.abstractmethod
    def get_backend(self, cls: type[BackendT], model: llm.Model) -> BackendT:
        raise NotImplementedError
