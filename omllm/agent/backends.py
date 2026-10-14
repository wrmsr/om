import abc
import typing as ta

from omcore import check
from omcore import collections as col
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

    @classmethod
    def of(
            cls,
            *backends: llm.Backend,
            no_auto_downcast: bool = False,
    ) -> ta.Self:
        dct: dict[type[llm.Backend], ta.MutableMapping[llm.Model | None, llm.Backend]] = {}

        for be in backends:
            ck: type[llm.Backend]
            if isinstance(be, llm.StreamBackend):
                ck = llm.StreamBackend  # type: ignore[type-abstract]
            elif isinstance(be, llm.ImmediateBackend):
                ck = llm.ImmediateBackend  # type: ignore[type-abstract]
            else:
                raise TypeError(be)

            dct2 = dct.setdefault(ck, col.IdentityKeyDict())

            mk = be.model
            check.not_in(mk, dct2)
            dct2[mk] = be

        for dct2 in dct.values():
            if None not in dct2 and len(dct2) == 1:
                dct2[None] = check.single(dct2.values())

        if not no_auto_downcast:
            if llm.ImmediateBackend not in dct and llm.StreamBackend in dct:
                dct[llm.ImmediateBackend] = dct[llm.StreamBackend]  # type: ignore[type-abstract]

        return cls(dct)

    def get_backend(self, cls: type[BackendT], model: llm.Model | None = None) -> BackendT:
        return check.isinstance(self._dct[cls][model], cls)
