import threading
import typing as ta

from .. import lang
from .api.configs import ConfigRegistry
from .api.configs import LazyInit
from .api.configs import LazyInitFn
from .api.configs import ModuleImport
from .api.marshaling import Marshaling
from .api.options import Option
from .api.runtime import Runtime
from .api.values import Value


if ta.TYPE_CHECKING:
    from .standard import factories as _sf
else:
    _sf = lang.proxy_import('.standard.factories', __package__)


T = ta.TypeVar('T')


##


_GLOBAL_LOCK = threading.RLock()


@lang.cached_function(lock=_GLOBAL_LOCK)
def global_config_registry() -> ConfigRegistry:
    return ConfigRegistry(lock=_GLOBAL_LOCK)


@lang.cached_function(lock=_GLOBAL_LOCK)
def global_runtime() -> Runtime:
    return Runtime(
        config_registry=global_config_registry(),

        marshaler_factory=_sf.new_standard_marshaler_factory(),
        unmarshaler_factory=_sf.new_standard_unmarshaler_factory(),
    )


class _GlobalMarshaling(Marshaling, lang.Final):
    def get_runtime(self) -> Runtime:
        return global_runtime()


@lang.cached_function(lock=_GLOBAL_LOCK)
def global_marshaling() -> Marshaling:
    return _GlobalMarshaling()


##


def marshal(
        obj: ta.Any,
        ty: ta.Any | None = None,
        *options: Option,
) -> Value:
    return global_marshaling().marshal(obj, ty, *options)


@ta.overload
def unmarshal(
        v: Value,
        ty: type[T],
        *options: Option,
) -> T:
    ...


@ta.overload
def unmarshal(
        v: Value,
        ty: ta.Any,
        *options: Option,
) -> ta.Any:
    ...


def unmarshal(v, ty, *options):
    return global_marshaling().unmarshal(v, ty, *options)


##


def register_global_lazy_init(
        fn: LazyInitFn,
) -> None:
    global_config_registry().update(
        None,
        LazyInit(fn),
    )


def register_global_module_import(
        name: str,
        package: str | None = None,
) -> None:
    global_config_registry().update(
        None,
        LazyInit(ModuleImport(name, package)),
    )
