import contextlib
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...asyncs.asynclite import all as asl
from ..errors import CyclicDependencyError
from ..injector import AsyncInjector
from ..keys import Key
from .bindings import BindingImpl
from .concurrency import ConcurrencyIdentity


if ta.TYPE_CHECKING:
    from . import injector as _injector
else:
    _injector = lang.proxy_import('.injector', __package__)


##


class _ProvisionWaitRegistry(lang.Final):
    """
    Global registry of cross-context provision waits, used to detect deadlocking dependency cycles spanning multiple
    provisioning contexts before those contexts block on each other. It must be global as cycles may span injectors
    and scopes. Only waits made through it are visible to detection - a wait-for path routing through IO or external
    synchronization is not, and remains backstopped only by wait timeouts.
    """

    def __init__(self) -> None:
        super().__init__()

        self._mtx = threading.Lock()  # guards _waits, held only for bookkeeping and walks - never while waiting
        self._waits: dict[ConcurrencyIdentity, _ProvisionWaitRegistry._Wait] = {}

    @dc.dataclass(frozen=True, eq=False)
    class _Wait:
        key: Key
        promise: asl.Promise
        target_owner: ConcurrencyIdentity

    def _detect(
            self,
            owner: ConcurrencyIdentity,
            key: Key,
            target_owner: ConcurrencyIdentity,
    ) -> None:
        # Callers must hold _mtx. Since every wait-edge addition performs this check under the mutex, whichever
        # context adds the closing edge of a cycle is guaranteed to observe it.
        chain: list[Key] = [key]
        seen: set[ConcurrencyIdentity] = {owner}
        cur = target_owner
        while True:
            if cur == owner:
                raise CyclicDependencyError(key, chain=tuple(chain))
            if cur in seen:
                return
            seen.add(cur)
            # A done promise's wait is already unwinding - treating it as absent keeps the walk conservative against
            # false positives from stale edges.
            if (w := self._waits.get(cur)) is None or w.promise.is_done():
                return
            chain.append(w.key)
            cur = w.target_owner

    @contextlib.contextmanager
    def waiting(
            self,
            owner: ConcurrencyIdentity,
            key: Key,
            promise: asl.Promise,
            target_owner: ConcurrencyIdentity,
    ) -> ta.Iterator[None]:
        with self._mtx:
            self._detect(owner, key, target_owner)
            check.not_in(owner, self._waits)  # an owner blocks on at most one wait at a time
            self._waits[owner] = _ProvisionWaitRegistry._Wait(key, promise, target_owner)

        try:
            yield
        finally:
            with self._mtx:
                del self._waits[owner]


_PROVISION_WAIT_REGISTRY = _ProvisionWaitRegistry()


##


DEFAULT_PROVISION_WAIT_TIMEOUT_S: float = 60. * 60.


class OnceProvisionMap(lang.Final):
    """
    Per-binding once-provisioning: the first arrival constructs, concurrent arrivals wait on a Promise. No lock is ever
    held across construction, so the wait-for graph can only follow dependency edges - which form a dag for any legal
    (acyclic) binding graph - making cross-context waits deadlock-free. Illegal cyclic graphs raced across contexts are
    caught eagerly by the wait registry rather than deadlocking. Failed construction attempts are not cached: each
    waiter of a failed attempt retries, potentially becoming the next constructor and raising its own error. Promises
    are only allocated when a second context actually arrives mid-construction - the uncontended path allocates
    nothing but the entry itself.
    """

    def __init__(self) -> None:
        super().__init__()

        self._mtx = threading.Lock()  # guards _dct and entry promise slots - must never be held across construction
        self._dct: dict[BindingImpl, OnceProvisionMap._Entry | OnceProvisionMap._Done] = {}

    @dc.dataclass(eq=False)
    class _Entry:
        owner: ConcurrencyIdentity
        promise: asl.Promise | None = None  # lazily created by the first waiter, under the map's mutex

    @dc.dataclass(frozen=True, eq=False)
    class _Done:
        v: ta.Any

    def has(self, binding: BindingImpl) -> bool:
        """
        Whether the binding has an entry - terminal or in-flight. Lets frozen scopes distinguish 'still servable'
        from 'would require new construction'.
        """

        with self._mtx:
            return binding in self._dct

    async def provide(self, binding: BindingImpl, injector: AsyncInjector) -> ta.Any:
        # Unlocked fast path for the common already-constructed case.
        if isinstance(e := self._dct.get(binding), OnceProvisionMap._Done):
            return e.v

        ii = check.isinstance(injector, _injector.AsyncInjectorImpl)
        owner = ii._concurrency.current_identity()  # noqa

        while True:
            p: asl.Promise | None = None
            with self._mtx:
                e = self._dct.get(binding)
                if isinstance(e, OnceProvisionMap._Done):
                    return e.v
                if e is None:
                    e = OnceProvisionMap._Entry(owner)
                    self._dct[binding] = e
                    mine = True
                else:
                    mine = False
                    if (p := e.promise) is None:
                        p = e.promise = ii._concurrency.make_promise()  # noqa

            if mine:
                # Note: on both completion paths the promise slot must be read under the same lock acquisition that
                # retires the entry - read separately, a waiter could create a promise just after the read and before
                # the retirement, and it would never be completed.
                try:
                    v = await binding.provider.provide(injector)
                except BaseException as ex:
                    with self._mtx:
                        if self._dct.get(binding) is e:
                            del self._dct[binding]
                        p = e.promise
                    if p is not None:
                        p.set_error(ex)
                    raise
                # The entry is swapped for a minimal terminal record - the promise (if any waiter forced one), its
                # synchronization machinery, and the owner identity all become garbage once in-flight waiters drain.
                with self._mtx:
                    self._dct[binding] = OnceProvisionMap._Done(v)
                    p = e.promise
                if p is not None:
                    p.set_value(v)
                return v

            p = check.not_none(p)  # always set on the waiter path

            try:
                if p.is_done():
                    return await p.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)

                # The registry raises CyclicDependencyError before waiting if this wait would close a cycle of
                # cross-context waits - including the single-hop case of a fresh request from the same thread and task
                # re-arriving mid-construction (eg. a Late invoked within its own constructor).
                with _PROVISION_WAIT_REGISTRY.waiting(owner, binding.key, p, e.owner):
                    return await p.wait(timeout=DEFAULT_PROVISION_WAIT_TIMEOUT_S)

            except asl.PromiseWaitTimeoutError:
                raise
            except BaseException:  # noqa
                if not p.is_done():
                    raise  # this waiter itself was interrupted (eg. task cancellation) - not a failed construction
                # That construction attempt failed - loop and retry, potentially becoming the next constructor.
