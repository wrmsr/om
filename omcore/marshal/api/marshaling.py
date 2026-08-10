import abc
import threading
import typing as ta

from ... import lang
from ..api._runtime import make_runtime
from .configs import ConfigRegistry
from .contexts import MarshalContext
from .contexts import MarshalFactoryContext
from .contexts import UnmarshalContext
from .contexts import UnmarshalFactoryContext
from .options import Option
from .options import build_effective_options
from .runtime import Runtime
from .types import MarshalerFactory
from .types import UnmarshalerFactory


if ta.TYPE_CHECKING:
    from .values import Value


T = ta.TypeVar('T')


##


class Marshaling(lang.Abstract):
    @abc.abstractmethod
    def get_runtime(self) -> Runtime:
        raise NotImplementedError

    def _get_warm_runtime(self) -> Runtime:
        rt = self.get_runtime()
        rt.ensure_warm()
        return rt

    ##

    def new_marshal_factory_context(
            self,
            *,
            _rt: Runtime | None = None,
    ) -> MarshalFactoryContext:
        rt = _rt if _rt is not None else self._get_warm_runtime()

        return MarshalFactoryContext(
            runtime=rt,
        )

    def new_unmarshal_factory_context(
            self,
            *,
            _rt: Runtime | None = None,
    ) -> UnmarshalFactoryContext:
        rt = _rt if _rt is not None else self._get_warm_runtime()

        return UnmarshalFactoryContext(
            runtime=rt,
        )

    ##

    def new_marshal_context(
            self,
            options: ta.Iterable[Option] | None = None,
            *,
            _rt: Runtime | None = None,
    ) -> MarshalContext:
        rt = _rt if _rt is not None else self._get_warm_runtime()

        return MarshalContext(
            runtime=rt,
            options=build_effective_options(rt.config_registry.get, options),
        )

    def new_unmarshal_context(
            self,
            options: ta.Iterable[Option] | None = None,
            *,
            _rt: Runtime | None = None,
    ) -> UnmarshalContext:
        rt = _rt if _rt is not None else self._get_warm_runtime()

        return UnmarshalContext(
            runtime=rt,
            options=build_effective_options(rt.config_registry.get, options),
        )

    #

    @ta.final
    def marshal(
            self,
            obj: ta.Any,
            ty: ta.Any | None = None,
            *options: Option,
    ) -> Value:
        rt = self._get_warm_runtime()
        mfc = self.new_marshal_factory_context(_rt=rt)
        mh = mfc.make_marshaler(ty if ty is not None else type(obj))
        mc = self.new_marshal_context(options, _rt=rt)
        return mh.marshal(mc, obj)

    @ta.overload
    def unmarshal(
            self,
            v: Value,
            ty: type[T],
            *options: Option,
    ) -> T:
        ...

    @ta.overload
    def unmarshal(  # noqa
            self,
            v: Value,
            ty: ta.Any,
            *options: Option,
    ) -> ta.Any:
        ...

    @ta.final
    def unmarshal(self, v, ty, *options):
        rt = self._get_warm_runtime()
        ufc = self.new_unmarshal_factory_context(_rt=rt)
        uh = ufc.make_unmarshaler(ty if ty is not None else type(v))
        uc = self.new_unmarshal_context(options, _rt=rt)
        return uh.unmarshal(uc, v)


#


class SimpleMarshaling(Marshaling):
    def __init__(
            self,
            *,
            config_registry: ConfigRegistry | None = None,

            marshaler_factory: MarshalerFactory | None = None,
            unmarshaler_factory: UnmarshalerFactory | None = None,
    ) -> None:
        super().__init__()

        if config_registry is None:
            config_registry = ConfigRegistry()
        self._config_registry = config_registry

        self._marshaler_factory = marshaler_factory
        self._unmarshaler_factory = unmarshaler_factory

        self._init_lock = threading.Lock()

    @property
    def config_registry(self) -> ConfigRegistry:
        return self._config_registry

    @property
    def marshaler_factory(self) -> MarshalerFactory | None:
        return self._marshaler_factory

    @property
    def unmarshaler_factory(self) -> UnmarshalerFactory | None:
        return self._unmarshaler_factory

    _runtime: Runtime

    def get_runtime(self) -> Runtime:
        try:
            return self._runtime
        except AttributeError:
            pass

        with self._init_lock:
            try:
                return self._runtime
            except AttributeError:
                pass

            rt = self._runtime = make_runtime(
                config_registry=self._config_registry,
                marshaler_factory=self._marshaler_factory,
                unmarshaler_factory=self._unmarshaler_factory,
            )
            return rt


#


class RuntimeMarshaling(Marshaling):
    """`Runtime` itself could be a `Marshaling`, but we explicitly prefer to hide and discourage direct access to it."""

    def __init__(self, runtime: Runtime) -> None:
        super().__init__()

        self._runtime = runtime

    def get_runtime(self) -> Runtime:
        return self._runtime

    @property
    def config_registry(self) -> ConfigRegistry:
        return self._runtime.config_registry

    @property
    def marshaler_factory(self) -> MarshalerFactory | None:
        return self._runtime.marshaler_factory

    @property
    def unmarshaler_factory(self) -> UnmarshalerFactory | None:
        return self._runtime.unmarshaler_factory
