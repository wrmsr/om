import abc
import contextlib
import types
import typing as ta

from omcore import check
from omcore import collections as col
from omcore import lang
from omcore.asyncs.asynclite import all as asl

from .. import llm


BackendT = ta.TypeVar('BackendT', bound=llm.Backend)

_ModelCacheKey: ta.TypeAlias = llm.ModelKey | tuple[str, int]
_CacheKey: ta.TypeAlias = tuple[type[llm.Backend], _ModelCacheKey]


##


class BackendTypeUnsupportedError(LookupError):
    """Raised when a backend family exists for a model, but does not implement the requested backend interface."""


class BackendManagerClosedError(RuntimeError):
    """Raised when attempting to acquire a backend from a closed `ManagedBackendManager`."""


##


class BackendManager(lang.Abstract):
    @abc.abstractmethod
    def acquire_backend(
            self,
            cls: type[BackendT],
            model: llm.Model | None = None,
    ) -> ta.AsyncContextManager[BackendT]:
        """
        Acquires a lease on a loaded backend of type `cls` for `model` (or the manager's default when `model` is
        None). The backend stays alive at least until the context exits, and may be shared across concurrent leases
        and kept warm after release.
        """

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
            default: llm.Backend | None = None,
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

        for ck, dct2 in dct.items():
            if None not in dct2:
                if default is not None and isinstance(default, ck):
                    dct2[None] = default
                elif len(dct2) == 1:
                    dct2[None] = check.single(dct2.values())

        if not no_auto_downcast:
            if llm.ImmediateBackend not in dct and llm.StreamBackend in dct:
                dct[llm.ImmediateBackend] = dct[llm.StreamBackend]  # type: ignore[type-abstract]
            elif (
                    llm.ImmediateBackend in dct and
                    llm.StreamBackend in dct
            ):
                # Merge StreamBackends into the ImmediateBackend view so a single dict manager can hold a mix of
                # stream and immediate models while callers ask for ImmediateBackend.
                merged: ta.MutableMapping[llm.Model | None, llm.Backend] = col.IdentityKeyDict()
                for k, v in dct[llm.StreamBackend].items():  # type: ignore[type-abstract]
                    merged[k] = v
                for k, v in dct[llm.ImmediateBackend].items():  # type: ignore[type-abstract]
                    if k is None and k in merged and default is not None and isinstance(default, llm.StreamBackend):
                        continue
                    merged[k] = v
                if None not in merged and default is not None and isinstance(default, llm.ImmediateBackend):
                    merged[None] = default
                dct[llm.ImmediateBackend] = merged  # type: ignore[type-abstract]

        return cls(dct)

    def _lookup(self, cls: type[BackendT], model: llm.Model | None) -> BackendT:
        dct2 = self._dct[cls]
        try:
            be = dct2[model]
        except KeyError:
            if model is not None and model.key is not None:
                for k, v in dct2.items():
                    if k is not None and k.key == model.key:
                        be = v
                        break
                else:
                    raise
            else:
                raise
        return check.isinstance(be, cls)

    @contextlib.asynccontextmanager
    async def acquire_backend(
            self,
            cls: type[BackendT],
            model: llm.Model | None = None,
    ) -> ta.AsyncIterator[BackendT]:
        yield self._lookup(cls, model)


##


class BackendOpener(lang.Abstract):
    """
    Opens one backend instance for `(cls, model)`, owning whatever resources are scoped to that backend's lifetime
    (its own injector, HTTP pools, loaded in-process model weights, etc.) for the duration of the returned async
    context manager.
    """

    @abc.abstractmethod
    def open_backend(
            self,
            cls: type[BackendT],
            model: llm.Model,
    ) -> ta.AsyncContextManager[BackendT]:
        raise NotImplementedError


##


class _LoadedBackendEntry:
    def __init__(
            self,
            *,
            key: _CacheKey,
            model: llm.Model,
            backend: llm.Backend,
            stack: contextlib.AsyncExitStack,
    ) -> None:
        super().__init__()

        self.key = key
        self.model = model
        self.backend = backend
        self.stack = stack
        self.leases = 0


class _PendingBackendLoad:
    def __init__(self, event: asl.Event) -> None:
        super().__init__()

        self.event = event
        self.entry: _LoadedBackendEntry | None = None
        self.error: Exception | None = None


class ManagedBackendManager(BackendManager, lang.SelfAsyncContextManaged):
    """
    Lazy, multi-model, lease-tracked backend manager meant to be shared across multiple agents in one host process.

    Backends are opened on demand through a `BackendOpener`, cached warm across leases so expensive backends (such as
    in-process torch/tinygrad models) are loaded once and shared across concurrent agents, and unloaded explicitly via
    `unload()` / `unload_idle()` or en masse on `aclose()` / `__aexit__`. Concurrent acquires for the same model
    coalesce onto a single load while distinct models load independently.

    Belongs to one event loop and is not thread-safe.
    """

    def __init__(
            self,
            *,
            opener: BackendOpener,
            events: asl.Events,
            default_model: llm.Model | None = None,
            no_prefer_stream: bool = False,
    ) -> None:
        super().__init__()

        self._opener = opener
        self._events = events
        self._default_model = default_model
        self._no_prefer_stream = no_prefer_stream

        self._loaded: dict[_CacheKey, _LoadedBackendEntry] = {}
        self._pending: dict[_CacheKey, _PendingBackendLoad] = {}
        self._closed = False

    @property
    def default_model(self) -> llm.Model | None:
        return self._default_model

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def loaded_models(self) -> tuple[llm.Model, ...]:
        seen: set[_ModelCacheKey] = set()
        out: list[llm.Model] = []
        for entry in self._loaded.values():
            mk = entry.key[1]
            if mk not in seen:
                seen.add(mk)
                out.append(entry.model)
        return tuple(out)

    def active_leases(self, model: llm.Model | llm.ModelKey) -> int:
        mk = model if isinstance(model, llm.ModelKey) else self._model_cache_key(model)
        return sum(entry.leases for entry in self._loaded.values() if entry.key[1] == mk)

    @staticmethod
    def _model_cache_key(model: llm.Model) -> _ModelCacheKey:
        if (mk := model.key) is not None:
            return mk
        return ('id', id(model))

    async def _acquire_key(
            self,
            key: _CacheKey,
            target_cls: type[llm.Backend],
            model: llm.Model,
    ) -> _LoadedBackendEntry:
        while True:
            if self._closed:
                raise BackendManagerClosedError

            if (entry := self._loaded.get(key)) is not None:
                entry.leases += 1
                return entry

            if (pending := self._pending.get(key)) is not None:
                await pending.event.wait()
                if pending.error is not None:
                    raise pending.error
                # Re-check state in the loop: the loaded entry may be present now, or a cancelled leader handed off.
                continue

            pending = _PendingBackendLoad(self._events.make_event())
            self._pending[key] = pending

            stack = contextlib.AsyncExitStack()
            try:
                backend = await stack.enter_async_context(self._opener.open_backend(target_cls, model))
                check.isinstance(backend, target_cls)

                if self._closed:
                    raise BackendManagerClosedError

                entry = _LoadedBackendEntry(
                    key=key,
                    model=model,
                    backend=backend,
                    stack=stack,
                )
                entry.leases = 1
                self._loaded[key] = entry
                pending.entry = entry
                return entry

            except Exception as e:
                pending.error = e
                await stack.aclose()
                raise

            except BaseException:
                await stack.aclose()
                raise

            finally:
                if self._pending.get(key) is pending:
                    del self._pending[key]
                pending.event.set()

    async def _acquire_entry(
            self,
            cls: type[llm.Backend],
            model: llm.Model,
    ) -> _LoadedBackendEntry:
        model_key = self._model_cache_key(model)

        if cls is llm.ImmediateBackend and not self._no_prefer_stream:
            imm_key: _CacheKey = (llm.ImmediateBackend, model_key)
            if (imm := self._loaded.get(imm_key)) is not None:
                if self._closed:
                    raise BackendManagerClosedError
                imm.leases += 1
                return imm

            try:
                return await self._acquire_key(
                    (llm.StreamBackend, model_key),  # type: ignore[type-abstract]
                    llm.StreamBackend,  # type: ignore[type-abstract]
                    model,
                )
            except BackendTypeUnsupportedError:
                return await self._acquire_key(
                    imm_key,
                    llm.ImmediateBackend,  # type: ignore[type-abstract]
                    model,
                )

        return await self._acquire_key((cls, model_key), cls, model)

    @contextlib.asynccontextmanager
    async def acquire_backend(
            self,
            cls: type[BackendT],
            model: llm.Model | None = None,
    ) -> ta.AsyncIterator[BackendT]:
        resolved_model = model if model is not None else self._default_model
        if resolved_model is None:
            raise ValueError('No model specified and no default model configured')

        entry = await self._acquire_entry(cls, resolved_model)
        try:
            yield check.isinstance(entry.backend, cls)
        finally:
            entry.leases -= 1

    #

    async def unload(self, model: llm.Model | llm.ModelKey) -> bool:
        """
        Unloads idle cached backends for `model`, exiting their stacks in LIFO order. Entries with active leases are
        left loaded. Returns True if at least one backend was unloaded.
        """

        mk = model if isinstance(model, llm.ModelKey) else self._model_cache_key(model)
        to_close: list[_LoadedBackendEntry] = []

        for key in list(self._loaded):
            if key[1] != mk:
                continue
            entry = self._loaded[key]
            if entry.leases == 0:
                del self._loaded[key]
                to_close.append(entry)

        if not to_close:
            return False

        async with contextlib.AsyncExitStack() as close_stack:
            for entry in to_close:
                close_stack.push_async_callback(entry.stack.aclose)

        return True

    async def unload_idle(self) -> int:
        """Unloads all cached backends with zero active leases, exiting their stacks in LIFO order."""

        to_close: list[_LoadedBackendEntry] = []

        for key in list(self._loaded):
            entry = self._loaded[key]
            if entry.leases == 0:
                del self._loaded[key]
                to_close.append(entry)

        if not to_close:
            return 0

        async with contextlib.AsyncExitStack() as close_stack:
            for entry in to_close:
                close_stack.push_async_callback(entry.stack.aclose)

        return len(to_close)

    async def aclose(self) -> None:
        self._closed = True

        to_close = list(self._loaded.values())
        self._loaded.clear()

        if not to_close:
            return

        async with contextlib.AsyncExitStack() as close_stack:
            for entry in to_close:
                close_stack.push_async_callback(entry.stack.aclose)

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None,
    ) -> None:
        await self.aclose()
