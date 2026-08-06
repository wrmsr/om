"""
FIXME?: lol do we cache everything it ever sees by identity?
 - yes, but, only keyed by rty - we don't really 'do' temp / weakref classes
  - maybe: still merge and cache, but only via identity IFF there's actually any identity keys in there for the thing
"""
import dataclasses as dc
import importlib
import sys
import threading
import typing as ta

from ... import check
from ... import lang
from ... import typedvalues as tv


T = ta.TypeVar('T')

ConfigT = ta.TypeVar('ConfigT', bound='Config')

type LazyInitFn = ta.Callable[[ConfigRegistry], None]


##


class Config(tv.TypedValue, lang.Abstract):
    pass


#


ConfigValues: ta.TypeAlias = tv.TypedValuesAccessor[Config]

_EMPTY_CONFIG_VALUES = tv.TypedValues[Config]()


class ConfigsGetter(ta.Protocol):
    def __call__(
        self,
        key: ta.Any = None,
        *,
        identity: bool | None = None,
    ) -> ConfigValues: ...


##


class ConfigRegistrySealedError(Exception):
    pass


class ConfigRegistry:
    def __init__(
            self,
            *,
            lock: ta.Optional[threading.RLock] = None,  # noqa
    ) -> None:
        super().__init__()

        if lock is None:
            lock = threading.RLock()
        self._lock = lock

        self.__snapshot: ConfigRegistry._Snapshot = self._Snapshot()

        self._sealed = False

    #

    @property
    def version(self) -> int:
        return self.__snapshot.version

    class Token:
        pass

    @property
    def token(self) -> object:
        return self.__snapshot.token

    @property
    def debug(self) -> ta.Mapping[ta.Any, ta.Sequence[Config]]:
        return self.__snapshot.debug

    #

    def copy(
            self,
            *,
            lock: ta.Optional[threading.RLock] = None,  # noqa
    ) -> ta.Self:
        ret: ta.Any = type(self)(lock=lock)
        ret.__snapshot = self.__snapshot  # noqa
        return ret

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _Snapshot:
        dct: ta.Mapping[ta.Any, tv.TypedValues[Config]] = dc.field(default_factory=dict)
        version: int = 0
        token: ConfigRegistry.Token = dc.field(default_factory=lambda: ConfigRegistry.Token())

        #

        @property
        def debug(self) -> ta.Mapping[ta.Any, ta.Sequence[Config]]:
            return {k: v.debug for k, v in self.dct.items()}

        #

        def update(
                self,
                key: ta.Any,
                *items: Config,
                identity: bool = False,
                discard: ta.Literal['all'] | ta.Iterable[type] | None = None,
                mode: ta.Literal['append', 'prepend', 'override', 'default'] = 'append',
        ) -> ConfigRegistry._Snapshot:
            if not items:
                return self

            if identity:
                key = lang.Identity(key)

            try:
                xv = self.dct[key]
            except KeyError:
                xv = _EMPTY_CONFIG_VALUES

            nr = xv.update(
                *items,
                discard=discard,
                mode=mode,
            )

            return ConfigRegistry._Snapshot(
                dct={**self.dct, key: nr},
                version=self.version + 1,
            )

        #

        _get_merged_cache: dict[ta.Any, tv.TypedValues[Config]] = dc.field(default_factory=dict)

        def get(
                self,
                key: ta.Any = None,
                *,
                identity: bool | None = None,
        ) -> tv.TypedValues[Config]:
            if key is None:
                check.state(identity is not True)
                identity = False

            if identity is None:
                try:
                    return self._get_merged_cache[key]
                except KeyError:
                    pass

                if (idc := self.get(key, identity=True)):
                    ret = self._get_merged_cache[key] = tv.TypedValues[Config](
                        *self.get(key, identity=False),
                        *idc,
                        override=True,
                    )
                    return ret

            if identity:
                key = lang.Identity(key)

            try:
                return self.dct[key]
            except KeyError:
                return _EMPTY_CONFIG_VALUES

    def is_sealed(self) -> bool:
        if self._sealed:
            return True
        with self._lock:
            return self._sealed

    def seal(self) -> ta.Self:
        if self._sealed:
            raise ConfigRegistrySealedError(self)
        with self._lock:
            self._seal()
        return self

    def _seal(self) -> None:
        if self._sealed:
            raise ConfigRegistrySealedError(self)

        self._sealed = True

    #

    def update(
            self,
            key: ta.Any,
            *items: Config,
            identity: bool = False,
            discard: ta.Literal['all'] | ta.Iterable[type] | None = None,
            mode: ta.Literal['append', 'prepend', 'override', 'default'] = 'append',
    ) -> ta.Self:
        check.arg(not (key is None and identity))

        if not items:
            return self

        with self._lock:
            if self._sealed:
                raise ConfigRegistrySealedError(self)

            self.__snapshot = self.__snapshot.update(
                key,
                *items,
                identity=identity,
                discard=discard,
                mode=mode,
            )

        return self

    #

    def get(
            self,
            key: ta.Any = None,
            *,
            identity: bool | None = None,
    ) -> ConfigValues:
        return self.__snapshot.get(key, identity=identity)

    #

    def call_atomically(self, fn: ta.Callable[[ta.Self], T]) -> T:
        """This API is intentionally obtuse to discourage external use of `_lock`."""

        with self._lock:
            return fn(self)


##


@dc.dataclass(frozen=True, eq=False)
class LazyInit(Config, lang.Final):
    fn: LazyInitFn


@dc.dataclass(frozen=True, eq=False)
class ModuleImport(lang.Final):
    name: str
    package: str | None = None

    def __call__(self, cr: ConfigRegistry) -> None:  # noqa
        mn = lang.resolve_import_name(self.name, self.package)

        if mn in sys.modules:
            return

        importlib.import_module(mn)
