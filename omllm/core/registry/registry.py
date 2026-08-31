# ruff: noqa: SLF001 UP007
"""
TODO:
 - queue register_types + late load manifests ? less urgent than late loading marshal lol
"""
import threading
import typing as ta

from omcore import check
from omcore import lang
from omcore import reflect as rfl

from .manifests import RegistryManifest
from .manifests import RegistryTypeManifest


RegistryTypeSelector: ta.TypeAlias = ta.Union[
    str,
    rfl.Type,
    type,
]


##


class Registry:
    def __init__(
            self,
            registry_type_manifests: ta.Iterable[RegistryTypeManifest],
            registry_manifests: ta.Iterable[RegistryManifest],
    ) -> None:
        super().__init__()

        self._lock = threading.RLock()

        self._registry_type_manifests = list(registry_type_manifests)
        self._registry_manifests = list(registry_manifests)

        entries_by_name_by_type: dict[str, dict[str, Registry.Entry]] = {}
        for rm in self._registry_manifests:
            e = self.Entry(_rm=rm)
            ed = entries_by_name_by_type.setdefault(e.type_name, {})
            for n in (rm.name, *(rm.aliases or ())):
                check.not_in(n, ed)
                ed[n] = e
        self._entries_by_name_by_type = entries_by_name_by_type

        self._types_by_name: dict[str, Registry.Type] = {}
        self._types_by_cls: dict[ta.Any, Registry.Type] = {}
        self._types_by_rtk: dict[rfl.TypeKey, Registry.Type] = {}

        for rtm in self._registry_type_manifests:
            rt = self.Type(
                _o=self,
                _rtm=rtm,
            )

            check.not_in(rt.name, self._types_by_name)

            self._types_by_name[rt.name] = rt

    #

    class Entry:
        def __init__(
                self,
                *,
                _rm: RegistryManifest,
        ) -> None:
            super().__init__()

            self._rm = _rm

            type_name = check.not_none(self._rm.type)
            if type_name.startswith('$.'):
                type_name = f'{_rm.module.split(".", maxsplit=1)[0]}.{type_name[2:]}'
            self._type_name = type_name

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}({self.name!r})'

        @property
        def name(self) -> str:
            return self._rm.name

        @property
        def type_name(self) -> str:
            return self._type_name

        _resolved: ta.Any

        def resolve(self) -> ta.Any:
            try:
                return self._resolved
            except AttributeError:
                pass
            self._resolved = resolved = self._rm.resolve()
            return resolved

    #

    class Type:
        def __init__(
                self,
                *,
                _o: Registry,
                _rtm: RegistryTypeManifest,
        ) -> None:
            super().__init__()

            self._o: ta.Final = _o
            self._rtm: ta.Final = _rtm

            self._name = '.'.join([_rtm.module, _rtm.attr])
            self._entries = _o._entries_by_name_by_type.get(self._name, {})

            self._cls: type | None = None

        def __repr__(self) -> str:
            return f'{self.__class__.__name__}({self.name!r})'

        @property
        def name(self) -> str:
            return self._name

        @property
        def entries(self) -> ta.Mapping[str, Registry.Entry]:
            return self._entries

        #

        __cls: lang.Maybe[ta.Any] = lang.nothing()
        __rty: rfl.Type

        def _maybe_set_cls(self, cls: ta.Any) -> None:
            check.not_none(cls)
            check.not_isinstance(cls, rfl.TypeInfo)

            if self.__cls.present:
                return

            rty = rfl.reflect_type(cls)

            check.not_in(cls, self._o._types_by_cls)
            check.not_in(rty.type_key(), self._o._types_by_rtk)

            self._o._types_by_cls[cls] = self
            self._o._types_by_rtk[rty.type_key()] = self

            self.__cls = lang.just(cls)
            self.__rty = rty
            self.__rtk = rty.type_key()

        def cls(self) -> ta.Any:
            if (cls := self.__cls).present:
                return cls.must()

            with self._o._lock:
                if (cls := self.__cls).present:
                    return cls.must()

                cls = check.not_none(self._rtm).resolve()

                self._maybe_set_cls(cls)
                return cls

        def rty(self) -> rfl.Type:
            self.cls()
            return self.__rty

        #

        def lookup(self, name: str) -> ta.Any:
            if not (entries := self._entries):
                raise KeyError(name)

            e = entries[name]
            return e.resolve()

    #

    def get_type(self, selector: RegistryTypeSelector) -> Type:
        if isinstance(selector, str):
            return self._types_by_name[selector]

        elif isinstance(selector, rfl.Type):
            return self._types_by_rtk[selector.type_key()]

        elif isinstance(selector, type):
            try:
                return self._types_by_cls[selector]

            except KeyError:
                name = '.'.join([selector.__module__, selector.__qualname__])
                return self._types_by_name[name]

        else:
            raise TypeError(selector)
