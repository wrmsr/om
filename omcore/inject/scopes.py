import abc
import contextvars
import types
import typing as ta

from .. import check
from .. import dataclasses as dc
from .. import lang
from .bindings import Binding
from .elements import Element
from .errors import ScopeAlreadyOpenError
from .errors import ScopeNotOpenError
from .keys import Key
from .keys import as_key
from .providers import Provider
from .types import Scope


if ta.TYPE_CHECKING:
    from . import injector as _injector
    from . import sync as _sync
else:
    _injector = lang.proxy_import('.injector', __package__)
    _sync = lang.proxy_import('.sync', __package__)


##


SCOPE_ALIASES: dict[str, Scope] = {}


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class ScopeBinding(Element, lang.Final):
    scope: Scope = dc.xfield(coerce=check.of_isinstance(Scope))


def bind_scope(sc: Scope) -> Element:
    return ScopeBinding(sc)


##


class Singleton(Scope, lang.Singleton, lang.Final):
    pass


SCOPE_ALIASES['singleton'] = Singleton()


##


class ThreadScope(Scope, lang.Singleton, lang.Final):
    pass


SCOPE_ALIASES['thread'] = ThreadScope()


##


class DelimitedScopeStateStore(lang.Abstract):
    """
    Holds a DelimitedScope's current opening state - one store per (scope, injector) pair, minted by the scope's
    Context policy at injector creation, with the state itself opaque to the store. Conspicuously ContextVar-shaped,
    the open/close pair standing in for set/reset so the already-open check can be atomic where it needs to be.
    """

    @abc.abstractmethod
    def get(self) -> ta.Any | None:
        raise NotImplementedError

    @abc.abstractmethod
    def open(self, state: ta.Any) -> ta.Any:
        """
        Installs the given opening state and returns a token for close, raising ScopeAlreadyOpenError if one is
        already installed here.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def close(self, token: ta.Any) -> None:
        raise NotImplementedError


class DelimitedScopeContext(lang.Abstract):
    """
    Policy for where a DelimitedScope's openings live. The default (a `context` of None) is injector-global: one
    opening at a time, seen by every thread and task. A contextual policy instead keys openings by execution context,
    letting concurrent actors each open the same scope on one shared injector - see ContextVarScopeContext.
    """

    @abc.abstractmethod
    def make_state_store(self, scope: DelimitedScope) -> DelimitedScopeStateStore:
        raise NotImplementedError


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class DelimitedScope(Scope, lang.Final):
    tag: ta.Any = dc.xfield(coerce=check.not_none)
    context: DelimitedScopeContext | None = dc.xfield(
        default=None,
        coerce=check.of_isinstance((DelimitedScopeContext, None)),
    )

    class Manager(lang.Abstract):
        @abc.abstractmethod
        def __call__(self, seeds: ta.Mapping[Key, ta.Any] | None = None) -> ta.AsyncContextManager[None]:
            raise NotImplementedError


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class ContextVarScopeContext(DelimitedScopeContext, lang.Final):
    """
    Openings live in the given contextvars.ContextVar: concurrent actors - asyncio tasks, threads - each open and see
    their own opening of the same scope on one shared injector. Propagation follows contextvars: work spawned within
    an opening inherits it (asyncio child tasks, asyncio.to_thread), a raw thread does not, an opening must be
    entered and exited in the same context, and escaping work that outlives its opening sees ScopeNotOpenError.

    The var is app infrastructure, owned and provided by the user - created at module level, per contextvars best
    practice. Its contents are opaque: an immutable snapshot map keyed by per-(scope, injector) store, so one var may
    back any number of contextual scopes on any number of injectors - or each scope may have its own - with complete
    mutual isolation either way.
    """

    var: contextvars.ContextVar = dc.xfield(coerce=check.of_isinstance(contextvars.ContextVar))

    class _Store(DelimitedScopeStateStore, lang.Final):
        """
        The var's value is treated as an immutable snapshot - every open/close sets a freshly-copied map - since
        captured contexts share the value by reference: a task spawned mid-opening must keep seeing its snapshot,
        unaffected by the opener's later close. Keys are the stores themselves: per-(scope, injector) by
        construction, and referencing nothing injector-ward - so a captured snapshot pins only the state it is
        entitled to, never the injector.
        """

        def __init__(self, scope: DelimitedScope, var: contextvars.ContextVar) -> None:
            super().__init__()

            self._scope = scope
            self._var = var

        def get(self) -> ta.Any | None:
            if (m := self._var.get(None)) is None:
                return None
            return m.get(self)

        def open(self, state: ta.Any) -> ta.Any:
            # Context-local, so check-then-set cannot race:
            m = self._var.get(None)
            if m is not None and m.get(self) is not None:
                raise ScopeAlreadyOpenError(self._scope)
            self._var.set({**(m or {}), self: state})
            return state

        def close(self, token: ta.Any) -> None:
            # Explicit removal rather than token-reset: a reset would clobber any opening made on a shared var after
            # this one, non-LIFO interleavings included. Closing where this exact opening is not visible (a foreign
            # context that never inherited it) fails loudly.
            m = self._var.get(None)
            if m is None or m.get(self) is not token:
                raise ScopeNotOpenError(self._scope)
            self._var.set({k: v for k, v in m.items() if k is not self})

    def make_state_store(self, scope: DelimitedScope) -> DelimitedScopeStateStore:
        return ContextVarScopeContext._Store(scope, self.var)


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
class ScopeSeededProvider(Provider):
    ss: DelimitedScope = dc.xfield(coerce=check.of_isinstance(DelimitedScope))
    key: Key = dc.xfield(coerce=check.of_isinstance(Key))


def bind_scope_seed(k: ta.Any, ss: DelimitedScope) -> Element:
    k = as_key(k)
    return Binding(k, ScopeSeededProvider(ss, k))


##


class _AsyncScopeEntry:
    """Manual (non-generator) async contextmanager: provides the scope's Manager and delegates to its entry."""

    __slots__ = (
        '_i',
        '_ss',
        '_seeds',
        '_inner',
    )

    def __init__(
            self,
            i: _injector.AsyncInjector,
            ss: DelimitedScope,
            seeds: ta.Mapping[Key, ta.Any] | None,
    ) -> None:
        self._i = i
        self._ss = ss
        self._seeds = seeds
        self._inner: ta.AsyncContextManager[None] | None = None

    async def __aenter__(self) -> None:
        mgr = await self._i.provide(as_key(DelimitedScope.Manager, tag=self._ss))
        self._inner = inner = mgr(self._seeds)
        return await inner.__aenter__()

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None,
    ) -> ta.Any:
        return await check.not_none(self._inner).__aexit__(exc_type, exc_val, exc_tb)


def async_enter_scope(
        i: _injector.AsyncInjector,
        ss: DelimitedScope,
        seeds: ta.Mapping[Key, ta.Any] | None = None,
) -> ta.AsyncContextManager[None]:
    return _AsyncScopeEntry(i, ss, seeds)


def enter_scope(
        i: _sync.Injector,
        ss: DelimitedScope,
        seeds: ta.Mapping[Key, ta.Any] | None = None,
) -> ta.ContextManager[None]:
    return lang.sync_async_with(async_enter_scope(
        i[_injector.AsyncInjector],
        ss,
        seeds,
    ))
