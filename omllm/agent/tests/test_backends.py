import asyncio
import contextlib
import types
import typing as ta

import pytest

from omcore import inject as inj
from omcore import lang
from omcore.asyncs.asynclite import all as asl

from ... import llm
from ..backends import BackendManagerClosedError
from ..backends import BackendOpener
from ..backends import BackendTypeUnsupportedError
from ..backends import DictBackendManager
from ..backends import ManagedBackendManager
from ..inject.backends import BackendBinder
from ..inject.backends import DispatchingBackendBinder
from ..inject.backends import InjectorBackendOpener
from ..inject.backends import ScriptedBackendBinder
from ..inject.backends import make_opt_async_managed_provider


##


def _model(name: str, backend: str = 'fake') -> llm.Model:
    return llm.Model(
        key=llm.ModelKey('test', name),
        name=name,
        backend=backend,
    )


class _ManagedAsyncBackend(llm.StreamBackend, lang.SelfAsyncContextManaged):
    def __init__(self, model: llm.Model, events: list[str]) -> None:
        super().__init__()

        self._model = model
        self._events = events
        self._entered = False
        self._exited = False

    @property
    def is_entered(self) -> bool:
        return self._entered

    @property
    def is_exited(self) -> bool:
        return self._exited

    @property
    def model(self) -> llm.Model:
        return self._model

    async def stream(self, context: llm.Context, options: llm.Options | None = None) -> llm.AiStream:
        raise NotImplementedError

    async def __aenter__(self) -> ta.Self:
        self._entered = True
        self._events.append(f'enter:{self._model.key_.id}')
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None,
    ) -> None:
        self._exited = True
        self._events.append(f'exit:{self._model.key_.id}')


class _ImmediateOnlyBackend(llm.ImmediateBackend):
    def __init__(self, model: llm.Model) -> None:
        super().__init__()

        self._model = model

    @property
    def model(self) -> llm.Model:
        return self._model

    async def immediate(self, context: llm.Context, options: llm.Options | None = None) -> llm.AiMessage:
        return llm.AiMessage([llm.TextContent('ok')], stop_reason='stop')


class _FuncOpener(BackendOpener):
    def __init__(self, fn: ta.Callable[[type[llm.Backend], llm.Model], ta.AsyncContextManager[llm.Backend]]) -> None:
        super().__init__()

        self._fn = fn

    def open_backend(self, cls: type[ta.Any], model: llm.Model) -> ta.AsyncContextManager[ta.Any]:
        return self._fn(cls, model)


##


@pytest.mark.asyncs('asyncio')
async def test_managed_backend_manager_lazy_load_reuse_and_unload():
    lifecycle: list[str] = []
    opens: list[tuple[type[llm.Backend], str]] = []
    m1 = _model('m1')
    m2 = _model('m2')

    @contextlib.asynccontextmanager
    async def open_fn(cls: type[llm.Backend], model: llm.Model) -> ta.AsyncIterator[llm.Backend]:
        opens.append((cls, model.key_.id))
        async with _ManagedAsyncBackend(model, lifecycle) as be:
            yield be

    async with ManagedBackendManager(
        opener=_FuncOpener(open_fn),
        events=asl.asyncio.Events(),
        default_model=m1,
    ) as mgr:
        assert not mgr.loaded_models

        # Default model loads lazily and prefers StreamBackend for ImmediateBackend requests.
        async with mgr.acquire_backend(llm.ImmediateBackend) as b1:  # type: ignore[type-abstract]
            assert isinstance(b1, _ManagedAsyncBackend)
            assert lifecycle == ['enter:m1']
            assert mgr.active_leases(m1) == 1
            assert list(mgr.loaded_models) == [m1]

            # Concurrent lease for StreamBackend shares the exact same instance.
            async with mgr.acquire_backend(llm.StreamBackend, m1) as b1_stream:  # type: ignore[type-abstract]
                assert b1_stream is b1
                assert mgr.active_leases(m1) == 2

                # Unload skips backends with active leases.
                assert not await mgr.unload(m1)
                assert await mgr.unload_idle() == 0

            assert mgr.active_leases(m1) == 1

        # Remains warm after release.
        assert mgr.active_leases(m1) == 0
        assert lifecycle == ['enter:m1']
        assert opens == [(llm.StreamBackend, 'm1')]

        # Second model loads alongside the first.
        async with mgr.acquire_backend(llm.ImmediateBackend, m2) as b2:  # type: ignore[type-abstract]
            assert isinstance(b2, _ManagedAsyncBackend)
            assert b2.model == m2
            assert list(mgr.loaded_models) == [m1, m2]

            # Unload idle unloads m1 while leaving leased m2 alive.
            assert await mgr.unload_idle() == 1
            assert lifecycle == ['enter:m1', 'enter:m2', 'exit:m1']
            assert list(mgr.loaded_models) == [m2]

        assert lifecycle == ['enter:m1', 'enter:m2', 'exit:m1']

    # Exiting the manager tears down remaining backends.
    assert mgr.is_closed
    assert lifecycle == ['enter:m1', 'enter:m2', 'exit:m1', 'exit:m2']

    with pytest.raises(BackendManagerClosedError):
        async with mgr.acquire_backend(llm.ImmediateBackend):  # type: ignore[type-abstract]
            pass


@pytest.mark.asyncs('asyncio')
async def test_managed_backend_manager_coalesces_same_model_and_parallelizes_distinct_models():
    m1 = _model('m1')
    m2 = _model('m2')
    m1_started = asyncio.Event()
    m1_release = asyncio.Event()
    m2_started = asyncio.Event()
    open_counts: dict[str, int] = {'m1': 0, 'm2': 0}

    @contextlib.asynccontextmanager
    async def open_fn(cls: type[llm.Backend], model: llm.Model) -> ta.AsyncIterator[llm.Backend]:
        mid = model.key_.id
        open_counts[mid] += 1
        if mid == 'm1':
            m1_started.set()
            await m1_release.wait()
        else:
            m2_started.set()
        yield _ManagedAsyncBackend(model, [])

    async with ManagedBackendManager(
        opener=_FuncOpener(open_fn),
        events=asl.asyncio.Events(),
    ) as mgr:
        async def acquire_once(m: llm.Model) -> llm.Backend:
            async with mgr.acquire_backend(llm.ImmediateBackend, m) as be:  # type: ignore[type-abstract]
                return be

        t1 = asyncio.create_task(acquire_once(m1))
        await m1_started.wait()

        # Second caller for m1 coalesces behind t1; distinct model m2 loads without waiting on m1!
        t1_dup = asyncio.create_task(acquire_once(m1))
        t2 = asyncio.create_task(acquire_once(m2))

        b2 = await t2
        assert m2_started.is_set()
        assert b2.model == m2

        m1_release.set()
        b1_a, b1_b = await asyncio.gather(t1, t1_dup)
        assert b1_a is b1_b
        assert open_counts == {'m1': 1, 'm2': 1}


@pytest.mark.asyncs('asyncio')
async def test_managed_backend_manager_load_failure_does_not_poison_future_attempts():
    m1 = _model('flaky')
    attempts = 0
    started = asyncio.Event()
    release = asyncio.Event()

    @contextlib.asynccontextmanager
    async def open_fn(cls: type[llm.Backend], model: llm.Model) -> ta.AsyncIterator[llm.Backend]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            started.set()
            await release.wait()
            raise RuntimeError('oom')
        yield _ManagedAsyncBackend(model, [])

    async with ManagedBackendManager(
        opener=_FuncOpener(open_fn),
        events=asl.asyncio.Events(),
    ) as mgr:
        async def go() -> llm.Backend:
            async with mgr.acquire_backend(llm.ImmediateBackend, m1) as be:  # type: ignore[type-abstract]
                return be

        t1 = asyncio.create_task(go())
        await started.wait()
        t2 = asyncio.create_task(go())
        await asyncio.sleep(0)
        release.set()

        r1, r2 = await asyncio.gather(t1, t2, return_exceptions=True)
        assert isinstance(r1, RuntimeError) and str(r1) == 'oom'
        assert isinstance(r2, RuntimeError) and str(r2) == 'oom'
        assert attempts == 1

        # Next attempt succeeds cleanly.
        be = await go()
        assert be.model == m1
        assert attempts == 2


@pytest.mark.asyncs('asyncio')
async def test_managed_backend_manager_falls_back_to_immediate_when_stream_unsupported():
    m = _model('imm')
    seen_cls: list[type[llm.Backend]] = []

    @contextlib.asynccontextmanager
    async def open_fn(cls: type[llm.Backend], model: llm.Model) -> ta.AsyncIterator[llm.Backend]:
        seen_cls.append(cls)
        if cls is llm.StreamBackend:
            raise BackendTypeUnsupportedError('immediate only')
        yield _ImmediateOnlyBackend(model)

    async with ManagedBackendManager(
        opener=_FuncOpener(open_fn),
        events=asl.asyncio.Events(),
        default_model=m,
    ) as mgr:
        async with mgr.acquire_backend(llm.ImmediateBackend) as b1:  # type: ignore[type-abstract]
            assert isinstance(b1, _ImmediateOnlyBackend)

        # Second acquire hits cached ImmediateBackend directly without retrying StreamBackend.
        async with mgr.acquire_backend(llm.ImmediateBackend) as b2:  # type: ignore[type-abstract]
            assert b2 is b1

        assert seen_cls == [llm.StreamBackend, llm.ImmediateBackend]

        # Explicit StreamBackend request still fails cleanly.
        with pytest.raises(BackendTypeUnsupportedError):
            async with mgr.acquire_backend(llm.StreamBackend, m):  # type: ignore[type-abstract]
                pass


@pytest.mark.asyncs('asyncio')
async def test_injector_backend_opener_gives_each_backend_its_own_managed_injector():
    lifecycle: list[str] = []

    class _WeightPool(lang.SelfAsyncContextManaged):
        def __init__(self, model: llm.Model) -> None:
            super().__init__()

            self.model = model

        async def __aenter__(self) -> ta.Self:
            lifecycle.append(f'pool_enter:{self.model.key_.id}')
            return self

        async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: types.TracebackType | None,
        ) -> None:
            lifecycle.append(f'pool_exit:{self.model.key_.id}')

    class _LocalBackend(llm.StreamBackend, lang.SelfAsyncContextManaged):
        def __init__(self, model: llm.Model, pool: _WeightPool) -> None:
            super().__init__()

            self._model = model
            self.pool = pool

        @property
        def model(self) -> llm.Model:
            return self._model

        async def stream(self, context: llm.Context, options: llm.Options | None = None) -> llm.AiStream:
            raise NotImplementedError

        async def __aenter__(self) -> ta.Self:
            lifecycle.append(f'be_enter:{self._model.key_.id}')
            return self

        async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: types.TracebackType | None,
        ) -> None:
            lifecycle.append(f'be_exit:{self._model.key_.id}')

    class _LocalBinder(BackendBinder):
        def bind_backend(self, cls: type[llm.Backend], model: llm.Model) -> inj.Elements:
            return inj.as_elements(
                inj.bind(
                    _WeightPool,
                    singleton=True,
                    to_async_fn=inj.make_async_managed_provider(_WeightPool),
                ),
                inj.bind(
                    cls,
                    singleton=True,
                    to_async_fn=make_opt_async_managed_provider(_LocalBackend),
                ),
            )

    opener = InjectorBackendOpener(
        binder=DispatchingBackendBinder(
            by_name={
                'local': _LocalBinder(),
                'scripted': ScriptedBackendBinder(),
            },
        ),
    )

    m_a = _model('a', backend='local')
    m_b = _model('b', backend='local')
    m_s = _model('s', backend='scripted')

    async with ManagedBackendManager(
        opener=opener,
        events=asl.asyncio.Events(),
        default_model=m_a,
    ) as mgr:
        async with mgr.acquire_backend(llm.ImmediateBackend, m_a) as be_a:  # type: ignore[type-abstract]
            async with mgr.acquire_backend(llm.ImmediateBackend, m_b) as be_b:  # type: ignore[type-abstract]
                assert isinstance(be_a, _LocalBackend)
                assert isinstance(be_b, _LocalBackend)
                # Isolated per-backend injectors: each backend has its own _WeightPool!
                assert be_a.pool is not be_b.pool
                assert be_a.pool.model == m_a
                assert be_b.pool.model == m_b

        async with mgr.acquire_backend(llm.ImmediateBackend, m_s) as be_s:  # type: ignore[type-abstract]
            assert isinstance(be_s, llm.ScriptedStreamBackend)

        # Unloading m_a tears down m_a's backend and pool in LIFO order while m_b stays live.
        assert await mgr.unload(m_a)
        assert lifecycle == [
            'pool_enter:a',
            'be_enter:a',
            'pool_enter:b',
            'be_enter:b',
            'be_exit:a',
            'pool_exit:a',
        ]

    assert lifecycle == [
        'pool_enter:a',
        'be_enter:a',
        'pool_enter:b',
        'be_enter:b',
        'be_exit:a',
        'pool_exit:a',
        'be_exit:b',
        'pool_exit:b',
    ]


@pytest.mark.asyncs('asyncio')
async def test_dict_backend_manager_multi_model_and_key_fallback():
    m1 = _model('one', backend='scripted')
    m2 = _model('two', backend='scripted')
    b1 = llm.ScriptedImmediateBackend(m1)
    b2 = llm.ScriptedImmediateBackend(m2)
    mgr = DictBackendManager.of(b1, b2, default=b1)

    async with mgr.acquire_backend(llm.ImmediateBackend) as got_default:  # type: ignore[type-abstract]
        assert got_default is b1

    # Different Model object instance with matching ModelKey resolves via key fallback.
    m2_copy = _model('two', backend='scripted')
    assert m2_copy is not m2
    async with mgr.acquire_backend(llm.ImmediateBackend, m2_copy) as got_m2:  # type: ignore[type-abstract]
        assert got_m2 is b2
