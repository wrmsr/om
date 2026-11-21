"""
Injector wiring for backends: each loaded backend runs inside its own isolated managed injector, owning its own
`contextlib.AsyncExitStack`. A `BackendBinder` can bind whatever internal services a backend needs (HTTP clients,
executors, in-process model weights/runtimes, tokenizers) alongside the backend itself, and
`make_opt_async_managed_provider` enters the backend if it is an async or sync context manager so all resources unwind
together on unload or shutdown.
"""
import abc
import contextlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ... import llm
from ...core import registry as reg
from ...core.apikeys import ApiKeyResolver


T = ta.TypeVar('T')
BackendT = ta.TypeVar('BackendT', bound=llm.Backend)


##


def make_opt_async_managed_provider(
        fac: ta.Callable[..., T],
) -> ta.Callable[..., ta.Awaitable[T]]:
    """
    Like `inj.make_async_managed_provider`, but enters the produced backend only if it is an async or sync context
    manager (`llm.manage_backend`). Plain backends are returned as-is.
    """

    kt = inj.build_kwargs_target(fac)

    async def _provide(
            ai: inj.AsyncInjector,
            aes: contextlib.AsyncExitStack,
    ) -> T:
        obj = await ai.inject(kt)
        return await aes.enter_async_context(llm.manage_backend(obj))

    return _provide


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class BackendModelOverrides:
    base_url: str | None = None
    model_id: str | None = None


class BackendBinder(lang.Abstract):
    """Produces the injector elements for one `(cls, model)` backend instance inside its dedicated backend injector."""

    @abc.abstractmethod
    def bind_backend(
            self,
            cls: type[llm.Backend],
            model: llm.Model,
    ) -> inj.Elements:
        raise NotImplementedError


def bind_backend_binder(name: str, to_key: ta.Any) -> inj.Elemental:
    return inj.map_binder[str, BackendBinder]().bind(name, to_key)


class RegistryBackendBinder(BackendBinder):
    """Resolves standard HTTP/provider backends from the global manifest registry inside each backend's injector."""

    def __init__(
            self,
            *,
            api_key_resolver: ApiKeyResolver | None = None,
            overrides_by_model_key: ta.Mapping[llm.ModelKey, BackendModelOverrides] | None = None,
    ) -> None:
        super().__init__()

        self._api_key_resolver = api_key_resolver
        self._overrides_by_model_key = dict(overrides_by_model_key or {})

    def bind_backend(
            self,
            cls: type[llm.Backend],
            model: llm.Model,
    ) -> inj.Elements:
        backend_name = model.backend_

        try:
            backend_impl_cls: ta.Any = reg.get_registry_cls(cls, backend_name)
        except KeyError as e:
            if cls is llm.StreamBackend:
                try:
                    reg.get_registry_cls(llm.ImmediateBackend, backend_name)
                except KeyError:
                    pass
                else:
                    raise agn.BackendTypeUnsupportedError(
                        f'Backend {backend_name!r} does not support {cls.__name__}',
                    ) from e
            raise

        overrides = self._overrides_by_model_key.get(model.key) if model.key is not None else None
        api_key_resolver = self._api_key_resolver

        def build(bound_model: llm.Model) -> llm.Backend:
            api_key = (
                api_key_resolver.resolve_first_api_key(bound_model.api_keys or [])
                if api_key_resolver is not None
                else None
            )
            return backend_impl_cls(
                bound_model,
                **lang.opt_kw(
                    api_key=api_key,
                    base_url=overrides.base_url if overrides is not None else None,
                    model_id=overrides.model_id if overrides is not None else None,
                ),
            )

        return inj.as_elements(
            inj.bind(
                cls,
                singleton=True,
                to_async_fn=make_opt_async_managed_provider(build),
            ),
        )


class ScriptedBackendBinder(BackendBinder):
    """Binds `ScriptedStreamBackend` or `ScriptedImmediateBackend` inside its own backend injector."""

    def __init__(
            self,
            *,
            script: llm.BackendScript | None = None,
    ) -> None:
        super().__init__()

        self._script = script

    def bind_backend(
            self,
            cls: type[llm.Backend],
            model: llm.Model,
    ) -> inj.Elements:
        impl_cls: type[llm.ScriptedStreamBackend | llm.ScriptedImmediateBackend]
        if cls is llm.StreamBackend:
            impl_cls = llm.ScriptedStreamBackend
        elif cls is llm.ImmediateBackend:
            impl_cls = llm.ScriptedImmediateBackend
        else:
            raise agn.BackendTypeUnsupportedError(f'Scripted backend does not support {cls.__name__}')

        script = self._script

        def build(bound_model: llm.Model) -> llm.Backend:
            return impl_cls(bound_model, script)

        return inj.as_elements(
            inj.bind(
                cls,
                singleton=True,
                to_async_fn=make_opt_async_managed_provider(build),
            ),
        )


class DispatchingBackendBinder(BackendBinder):
    """Routes `bind_backend` by `model.backend_` to specialized binders, falling back to `default`."""

    def __init__(
            self,
            *,
            by_name: ta.Mapping[str, BackendBinder] | None = None,
            default: BackendBinder | None = None,
    ) -> None:
        super().__init__()

        self._by_name = dict(by_name or {})
        self._default = default

    def bind_backend(
            self,
            cls: type[llm.Backend],
            model: llm.Model,
    ) -> inj.Elements:
        name = model.backend_
        if (binder := self._by_name.get(name)) is not None:
            return binder.bind_backend(cls, model)
        if self._default is not None:
            return self._default.bind_backend(cls, model)
        raise KeyError(name)


##


class InjectorBackendOpener(agn.BackendOpener):
    """
    Opens each backend inside its own isolated managed injector (`inj.create_asyncio_managed_injector`).

    All managed singletons bound by the `BackendBinder` and the backend itself (when context-managed) live on that
    backend injector's `AsyncExitStack` and unwind in LIFO order when the returned context exits.
    """

    def __init__(
            self,
            *,
            binder: BackendBinder,
            extra_elements: ta.Sequence[inj.Elemental] = (),
    ) -> None:
        super().__init__()

        self._binder = binder
        self._extra_elements = tuple(extra_elements)

    @contextlib.asynccontextmanager
    async def open_backend(
            self,
            cls: type[BackendT],
            model: llm.Model,
    ) -> ta.AsyncIterator[BackendT]:
        els = inj.as_elements(
            inj.bind(llm.Model, to_const=model),
            *self._extra_elements,
            self._binder.bind_backend(cls, model),
        )

        async with inj.create_asyncio_managed_injector(els) as injector:
            yield check.isinstance(await injector[cls], cls)
