import functools
import inspect
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from .protocol import RpcRequest


T = ta.TypeVar('T')
P = ta.ParamSpec('P')


##


class RpcCaller(ta.Protocol):
    def call(self, method: str, params: ta.Any = None) -> ta.Any:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class RpcObjectMethod:
    attribute: str
    name: str
    function: ta.Callable[..., ta.Any]
    signature: inspect.Signature


_RPC_OBJECT_METHOD_ATTR = '__omcore_rpc_object_method__'


@ta.overload
def rpc_method(fn: ta.Callable[P, T]) -> ta.Callable[P, T]: ...


@ta.overload
def rpc_method(*, name: str | None = None) -> ta.Callable[[ta.Callable[P, T]], ta.Callable[P, T]]: ...


def rpc_method(
        fn: ta.Callable[..., T] | None = None,
        *,
        name: str | None = None,
) -> ta.Callable[..., T] | ta.Callable[[ta.Callable[..., T]], ta.Callable[..., T]]:
    """Marks an interface method as explicitly callable through RpcObjectHandler."""

    def decorate(method: ta.Callable[..., T]) -> ta.Callable[..., T]:
        rpc_name = check.non_empty_str(name if name is not None else method.__name__)
        if hasattr(method, _RPC_OBJECT_METHOD_ATTR):
            raise TypeError(f'RPC method is already decorated: {method!r}')
        setattr(method, _RPC_OBJECT_METHOD_ATTR, rpc_name)
        return method

    if fn is not None:
        return decorate(fn)
    return decorate


def _rpc_object_methods(interface: type) -> tuple[RpcObjectMethod, ...]:
    by_attribute: dict[str, RpcObjectMethod] = {}
    by_name: dict[str, RpcObjectMethod] = {}

    for cls in reversed(interface.__mro__):
        for attribute, value in cls.__dict__.items():
            if not callable(value) or not (name := getattr(value, _RPC_OBJECT_METHOD_ATTR, None)):
                continue

            signature = inspect.signature(value)
            parameters = tuple(signature.parameters.values())
            if not parameters or parameters[0].name not in {'self', 'cls'}:
                raise TypeError(f'RPC object method must have a self parameter: {interface.__qualname__}.{attribute}')

            method = RpcObjectMethod(
                attribute=attribute,
                name=check.non_empty_str(name),
                function=value,
                signature=signature,
            )
            if (old := by_name.get(method.name)) is not None and old.attribute != attribute:
                raise TypeError(f'Duplicate RPC object method name {method.name!r}')
            by_attribute[attribute] = method
            by_name[method.name] = method

    return tuple(by_attribute.values())


def _qualified_rpc_method_name(namespace: str | None, name: str) -> str:
    if namespace is None:
        return name
    return f'{check.non_empty_str(namespace)}.{name}'


##


class RpcObjectHandler(lang.Final):
    """Dispatches only explicitly decorated interface methods to an implementation object."""

    def __init__(
            self,
            interface: type[ta.Any],
            implementation: T,
            *,
            namespace: str | None = None,
    ) -> None:
        super().__init__()

        check.isinstance(implementation, interface)
        methods = _rpc_object_methods(interface)
        if not methods:
            raise TypeError(f'RPC object interface has no decorated methods: {interface!r}')

        self._interface = interface
        self._implementation = implementation
        self._methods = {
            _qualified_rpc_method_name(namespace, method.name): (
                method,
                check.callable(getattr(implementation, method.attribute)),
            )
            for method in methods
        }

    def __call__(self, request: RpcRequest) -> ta.Any:
        try:
            method, implementation_method = self._methods[request.method]
        except KeyError:
            raise ValueError(f'Unknown RPC object method: {request.method!r}') from None

        params = check.isinstance(request.params, dict)
        if set(params) != {'args', 'kwargs'}:
            raise TypeError('RPC object params must contain exactly args and kwargs')
        args = check.isinstance(params['args'], list)
        kwargs = check.isinstance(params['kwargs'], dict)
        if not all(isinstance(key, str) for key in kwargs):
            raise TypeError('RPC object keyword names must be strings')

        method.signature.bind(self._implementation, *args, **kwargs)
        return implementation_method(*args, **kwargs)


class RpcObjectProxy(lang.Final):
    """Builds an interface subclass whose decorated methods call an RpcCaller."""

    @classmethod
    def of(
            cls,
            interface: type[ta.Any],
            caller: RpcCaller,
            *,
            namespace: str | None = None,
    ) -> ta.Any:
        methods = _rpc_object_methods(interface)
        if not methods:
            raise TypeError(f'RPC object interface has no decorated methods: {interface!r}')

        def init(self) -> None:
            object.__setattr__(self, '_rpc_object_caller', caller)

        namespace_dict: dict[str, ta.Any] = {
            '__init__': init,
            '__module__': interface.__module__,
        }

        for method in methods:
            def make_proxy_method(method: RpcObjectMethod) -> ta.Callable[..., ta.Any]:
                @functools.wraps(method.function)
                def proxy_method(self, *args: ta.Any, **kwargs: ta.Any) -> ta.Any:
                    method.signature.bind(self, *args, **kwargs)
                    return self._rpc_object_caller.call(
                        _qualified_rpc_method_name(namespace, method.name),
                        {
                            'args': list(args),
                            'kwargs': kwargs,
                        },
                    )

                proxy_method.__isabstractmethod__ = False  # type: ignore[attr-defined]
                return proxy_method

            namespace_dict[method.attribute] = make_proxy_method(method)

        proxy_type = type(f'{interface.__name__}RpcObjectProxy', (interface,), namespace_dict)
        return proxy_type()
