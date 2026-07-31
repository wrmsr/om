import pytest

from ..base import CallbackAsyncLifecycle
from ..base import CallbackLifecycle
from ..controller import AsyncLifecycleController
from ..controller import LifecycleController
from ..listeners import AsyncLifecycleListener
from ..listeners import LifecycleListener
from ..states import LifecycleStates


##


def test_controller_transitions_and_listeners():
    events = []

    lifecycle = CallbackLifecycle(
        on_state=lambda state: events.append(state.name),
        on_construct=lambda: events.append('construct'),
        on_start=lambda: events.append('start'),
        on_stop=lambda: events.append('stop'),
        on_destroy=lambda: events.append('destroy'),
    )

    class Listener(LifecycleListener):
        def on_starting(self, obj):
            assert obj is lifecycle
            events.append('on_starting')

        def on_started(self, obj):
            assert obj is lifecycle
            events.append('on_started')

        def on_stopping(self, obj):
            assert obj is lifecycle
            events.append('on_stopping')

        def on_stopped(self, obj):
            assert obj is lifecycle
            events.append('on_stopped')

    controller = LifecycleController(lifecycle).add_listener(Listener())
    controller.lifecycle_construct()
    controller.lifecycle_start()
    controller.lifecycle_stop()
    controller.lifecycle_destroy()

    assert controller.state is LifecycleStates.DESTROYED
    assert events == [
        'CONSTRUCTING',
        'construct',
        'CONSTRUCTED',
        'on_starting',
        'STARTING',
        'start',
        'STARTED',
        'on_started',
        'on_stopping',
        'STOPPING',
        'stop',
        'STOPPED',
        'on_stopped',
        'DESTROYING',
        'destroy',
        'DESTROYED',
    ]


def test_controller_failure_state_can_be_destroyed():
    class StartError(Exception):
        pass

    states: list = []

    def start():
        raise StartError

    controller = LifecycleController(CallbackLifecycle(
        on_state=states.append,
        on_start=start,
    ))
    controller.lifecycle_construct()

    with pytest.raises(StartError):
        controller.lifecycle_start()

    assert controller.state is LifecycleStates.FAILED_STARTING

    controller.lifecycle_destroy()
    assert controller.state is LifecycleStates.DESTROYED
    assert states == [
        LifecycleStates.CONSTRUCTING,
        LifecycleStates.CONSTRUCTED,
        LifecycleStates.STARTING,
        LifecycleStates.FAILED_STARTING,
        LifecycleStates.DESTROYING,
        LifecycleStates.DESTROYED,
    ]


@pytest.mark.asyncs('asyncio')
async def test_async_controller_transitions_and_listeners():
    events = []

    async def state(new_state):
        events.append(new_state.name)

    async def construct():
        events.append('construct')

    async def start():
        events.append('start')

    async def stop():
        events.append('stop')

    async def destroy():
        events.append('destroy')

    lifecycle = CallbackAsyncLifecycle(
        on_state=state,
        on_construct=construct,
        on_start=start,
        on_stop=stop,
        on_destroy=destroy,
    )

    class Listener(AsyncLifecycleListener):
        async def on_starting(self, obj):
            assert obj is lifecycle
            events.append('on_starting')

        async def on_started(self, obj):
            assert obj is lifecycle
            events.append('on_started')

        async def on_stopping(self, obj):
            assert obj is lifecycle
            events.append('on_stopping')

        async def on_stopped(self, obj):
            assert obj is lifecycle
            events.append('on_stopped')

    controller = AsyncLifecycleController(lifecycle).add_listener(Listener())
    await controller.lifecycle_construct()
    await controller.lifecycle_start()
    await controller.lifecycle_stop()
    await controller.lifecycle_destroy()

    assert controller.state is LifecycleStates.DESTROYED
    assert events == [
        'CONSTRUCTING',
        'construct',
        'CONSTRUCTED',
        'on_starting',
        'STARTING',
        'start',
        'STARTED',
        'on_started',
        'on_stopping',
        'STOPPING',
        'stop',
        'STOPPED',
        'on_stopped',
        'DESTROYING',
        'destroy',
        'DESTROYED',
    ]
