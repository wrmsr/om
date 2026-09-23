import asyncio

import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from ...types.events import ProcessEvent
from ...types.events import ScopeOpenedEvent
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
