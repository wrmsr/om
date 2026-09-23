import asyncio

import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from ...types.events import ProcessEvent
from ...types.events import ProcessExitedEvent
from ...types.events import ProcessReapedEvent
from ...types.events import ProcessSpawnedEvent
from ...types.events import ScopeOpenedEvent
from ...types.ids import ProcessId
from ..events import ProcessEventDrain


class _Harness:
    def __init__(self, subscriber) -> None:
        super().__init__()

        self.tasks: set[asyncio.Task] = set()
        self.drain = ProcessEventDrain(
            publish=subscriber,
            spawn_task=self._spawn_task,
            asynclite=asl.asyncio.All(),
        )

    def _spawn_task(self, coro) -> None:
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def join(self) -> None:
        while self.tasks:
            await asyncio.gather(*list(self.tasks), return_exceptions=True)
            await asyncio.sleep(0)


def _event(name: str) -> ScopeOpenedEvent:
    return ScopeOpenedEvent(scope_path=(name,))


def _name(event: ProcessEvent) -> str:
    return check.isinstance(event, ScopeOpenedEvent).scope_path[0]


@pytest.mark.asyncs('asyncio')
async def test_events_are_delivered_in_order_even_when_a_subscriber_suspends():
    delivered = []

    async def subscriber(event):
        if _name(event) == 'slow':
            await asyncio.sleep(.02)
        delivered.append(_name(event))

    h = _Harness(subscriber)
    h.drain.enable()
    h.drain.publish_soon(_event('slow'))
    h.drain.publish_soon(_event('fast'))
    await h.join()
    assert delivered == ['slow', 'fast']
    assert not h.drain.busy


@pytest.mark.asyncs('asyncio')
async def test_events_queued_before_enable_are_delivered_first():
    delivered = []

    async def subscriber(event):
        delivered.append(_name(event))

    h = _Harness(subscriber)
    h.drain.publish_soon(_event('early'))
    await h.drain.publish_now(_event('also early'))
    await h.join()
    assert delivered == []
    assert h.drain.busy

    h.drain.enable()
    await h.drain.publish_now(_event('late'))
    assert delivered == ['early', 'also early', 'late']
    assert not h.drain.busy


@pytest.mark.asyncs('asyncio')
async def test_publish_now_from_within_a_subscriber_does_not_deadlock():
    delivered = []

    async def subscriber(event):
        delivered.append(_name(event))
        if _name(event) == 'outer':
            await h.drain.publish_now(_event('inner'))

    h = _Harness(subscriber)
    h.drain.enable()
    await asyncio.wait_for(h.drain.publish_now(_event('outer')), 5.)
    await h.join()
    assert delivered == ['outer', 'inner']


@pytest.mark.asyncs('asyncio')
async def test_a_failing_subscriber_does_not_stop_later_events():
    delivered = []

    async def subscriber(event):
        if _name(event) == 'bad':
            raise ValueError('bad')
        delivered.append(_name(event))

    h = _Harness(subscriber)
    h.drain.enable()
    h.drain.publish_soon(_event('bad'))
    h.drain.publish_soon(_event('good'))
    await h.join()
    assert delivered == ['good']


@pytest.mark.asyncs('asyncio')
async def test_held_events_wait_for_their_process_to_be_announced():
    delivered = []

    async def subscriber(event):
        delivered.append(event)

    def lifecycle(cls, process_id, **kwargs):
        return cls(process_id=ProcessId(process_id), pid=1, scope_path=('root',), **kwargs)

    h = _Harness(subscriber)
    h.drain.enable()
    h.drain.hold(ProcessId('p1'))

    exited = lifecycle(ProcessExitedEvent, 'p1', returncode=0)
    other = lifecycle(ProcessExitedEvent, 'p2', returncode=1)
    h.drain.publish_soon(exited)
    h.drain.publish_soon(other)
    await h.join()
    assert delivered == [other]

    spawned = lifecycle(ProcessSpawnedEvent, 'p1', argv=('true',))
    h.drain.release(ProcessId('p1'), leading=spawned)
    await h.drain.flush()
    assert delivered == [other, spawned, exited]

    # Nothing is parked any more, and releasing again is a no-op.
    reaped = lifecycle(ProcessReapedEvent, 'p1', returncode=0)
    h.drain.publish_soon(reaped)
    h.drain.release(ProcessId('p1'))
    await h.drain.flush()
    assert delivered == [other, spawned, exited, reaped]
