import contextlib

import pytest

from ... import check
from ..base import CallbackAsyncLifecycle
from ..base import CallbackLifecycle
from ..contextmanagers import AsyncContextManagerLifecycle
from ..contextmanagers import AsyncLifecycleContextManager
from ..contextmanagers import ContextManagerLifecycle
from ..contextmanagers import LifecycleContextManager
from ..manager import AsyncLifecycleManager
from ..manager import LifecycleManager
from ..states import LifecycleStates
from ..unwrap import unwrap_async_lifecycle
from ..unwrap import unwrap_lifecycle


def test_manual_lifecycles():
    mgr = LifecycleManager()
    mgr.add(CallbackLifecycle())


def test_context_managers():
    @contextlib.contextmanager
    def foo():
        print('foo.enter')
        try:
            yield
        finally:
            print('foo.exit')

    mgr = LifecycleManager()

    f = foo()
    mgr.add(ContextManagerLifecycle(f))

    with LifecycleContextManager(check.not_none(unwrap_lifecycle(mgr))):
        print('inner')


def test_manager_dependency_order():
    events = []

    def make_lifecycle(name):
        return CallbackLifecycle(
            on_construct=lambda: events.append(f'{name}.construct'),
            on_start=lambda: events.append(f'{name}.start'),
            on_stop=lambda: events.append(f'{name}.stop'),
            on_destroy=lambda: events.append(f'{name}.destroy'),
        )

    dependency = make_lifecycle('dependency')
    dependent = make_lifecycle('dependent')

    mgr = LifecycleManager()
    mgr.add(dependent, [dependency])

    with LifecycleContextManager(check.not_none(unwrap_lifecycle(mgr))):
        events.append('running')

    assert events == [
        'dependency.construct',
        'dependent.construct',
        'dependency.start',
        'dependent.start',
        'running',
        'dependent.stop',
        'dependency.stop',
        'dependent.destroy',
        'dependency.destroy',
    ]


def test_add_dependency_to_started_lifecycle():
    events = []

    existing = CallbackLifecycle(
        on_construct=lambda: events.append('existing.construct'),
        on_start=lambda: events.append('existing.start'),
    )
    dependency = CallbackLifecycle(
        on_construct=lambda: events.append('dependency.construct'),
        on_start=lambda: events.append('dependency.start'),
    )

    mgr = LifecycleManager()
    existing_entry = mgr.add(existing)

    with LifecycleContextManager(check.not_none(unwrap_lifecycle(mgr))):
        dependency_entry = next(iter(mgr.add(existing, [dependency]).dependencies))

        assert dependency_entry.controller.state is LifecycleStates.STARTED
        assert existing_entry.controller.state is LifecycleStates.STARTED
        assert events == [
            'existing.construct',
            'existing.start',
            'dependency.construct',
            'dependency.start',
        ]


@pytest.mark.asyncs('asyncio')
async def test_async_manual_lifecycles():
    mgr = AsyncLifecycleManager()
    await mgr.add(CallbackAsyncLifecycle())


@pytest.mark.asyncs('asyncio')
async def test_async_context_managers():
    @contextlib.asynccontextmanager
    async def foo():
        print('foo.enter')
        try:
            yield
        finally:
            print('foo.exit')

    mgr = AsyncLifecycleManager()

    f = foo()
    await mgr.add(AsyncContextManagerLifecycle(f))

    async with AsyncLifecycleContextManager(check.not_none(unwrap_async_lifecycle(mgr))):
        print('inner')


@pytest.mark.asyncs('asyncio')
async def test_async_manager_dependency_order():
    events = []

    def callback(event):
        async def inner():
            events.append(event)

        return inner

    dependency = CallbackAsyncLifecycle(
        on_construct=callback('dependency.construct'),
        on_start=callback('dependency.start'),
        on_stop=callback('dependency.stop'),
        on_destroy=callback('dependency.destroy'),
    )
    dependent = CallbackAsyncLifecycle(
        on_construct=callback('dependent.construct'),
        on_start=callback('dependent.start'),
        on_stop=callback('dependent.stop'),
        on_destroy=callback('dependent.destroy'),
    )

    mgr = AsyncLifecycleManager()
    await mgr.add(dependent, [dependency])

    async with AsyncLifecycleContextManager(check.not_none(unwrap_async_lifecycle(mgr))):
        events.append('running')

    assert events == [
        'dependency.construct',
        'dependent.construct',
        'dependency.start',
        'dependent.start',
        'running',
        'dependent.stop',
        'dependency.stop',
        'dependent.destroy',
        'dependency.destroy',
    ]
