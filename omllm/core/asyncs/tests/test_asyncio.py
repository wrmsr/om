"""The group contract, as the asyncio runner keeps it."""
import asyncio
import typing as ta

import pytest

from omcore import check

from ..asyncio import AsyncioGroupRunner
from ..base import AsyncGroupCancelledError
from ..base import AsyncGroupFailedError
from ..base import AsyncGroupMemberCancelledError


##


class _Gate:
    """A member which waits to be released, recording what it sees on the way out."""

    def __init__(self, name):
        super().__init__()

        self.name = name
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.seen = []

    async def __call__(self):
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.seen.append(('cancelled', check.not_none(asyncio.current_task()).cancelling() > 0))
            raise
        self.seen.append('done')
        return self.name


@pytest.mark.asyncs('asyncio')
async def test_members_run_concurrently_and_results_keep_their_order():
    a, b = _Gate('a'), _Gate('b')

    task = asyncio.create_task(AsyncioGroupRunner().run([a, b]))
    await a.started.wait()
    await b.started.wait()

    # Finishing in the other order changes nothing about where the results land.
    b.release.set()
    await asyncio.sleep(0)
    a.release.set()

    assert await task == ['a', 'b']


@pytest.mark.asyncs('asyncio')
async def test_empty_group():
    assert await AsyncioGroupRunner().run([]) == []


@pytest.mark.asyncs('asyncio')
async def test_cancelling_the_caller_cancels_every_member_first():
    a, b = _Gate('a'), _Gate('b')

    task = asyncio.create_task(AsyncioGroupRunner().run([a, b]))
    await a.started.wait()
    await b.started.wait()
    task.cancel()

    with pytest.raises(AsyncGroupCancelledError) as ei:
        await task

    # Each member saw its own cancellation - a real one, of its own task - and none had completed.
    assert a.seen == [('cancelled', True)]
    assert b.seen == [('cancelled', True)]
    assert [o.present for o in ei.value.outcomes] == [False, False]

    # And it is the backend's cancellation too: the task ended cancelled.
    assert isinstance(ei.value, asyncio.CancelledError)
    assert task.cancelled()


@pytest.mark.asyncs('asyncio')
async def test_cancellation_reports_what_had_completed():
    a, b = _Gate('a'), _Gate('b')

    task = asyncio.create_task(AsyncioGroupRunner().run([a, b]))
    await a.started.wait()
    await b.started.wait()
    a.release.set()
    await asyncio.sleep(0)
    task.cancel()

    with pytest.raises(AsyncGroupCancelledError) as ei:
        await task

    assert a.seen == ['done']
    assert b.seen == [('cancelled', True)]
    [oa, ob] = ei.value.outcomes
    assert oa.must() == 'a'
    assert not ob.present


@pytest.mark.asyncs('asyncio')
async def test_a_member_raising_cancels_the_rest_and_comes_out_as_a_group():
    a = _Gate('a')

    async def boom():
        await a.started.wait()
        raise RuntimeError('boom')

    fns: list[ta.Callable[[], ta.Awaitable[ta.Any]]] = [a, boom]
    with pytest.raises(AsyncGroupFailedError) as ei:
        await AsyncioGroupRunner().run(fns)

    assert [type(e) for e in ei.value.exceptions] == [RuntimeError]
    assert a.seen == [('cancelled', True)]
    assert [o.present for o in ei.value.outcomes] == [False, False]


@pytest.mark.asyncs('asyncio')
async def test_a_failure_reports_what_had_completed():
    a, b = _Gate('a'), _Gate('b')

    async def boom():
        await a.started.wait()
        await b.started.wait()
        await asyncio.sleep(0)
        raise RuntimeError('boom')

    async def run():
        return await AsyncioGroupRunner().run([a, boom, b])

    task = asyncio.create_task(run())
    await b.started.wait()
    a.release.set()

    with pytest.raises(AsyncGroupFailedError) as ei:
        await task

    # It is an ExceptionGroup, and splits as one, keeping its outcomes.
    assert isinstance(ei.value, ExceptionGroup)
    [oa, ob2, ob] = ei.value.outcomes
    assert oa.must() == 'a'
    assert not ob2.present
    assert not ob.present
    assert a.seen == ['done']
    assert b.seen == [('cancelled', True)]
    matched, rest = ei.value.split(RuntimeError)
    assert isinstance(matched, AsyncGroupFailedError)
    assert matched.outcomes == ei.value.outcomes
    assert rest is None


@pytest.mark.asyncs('asyncio')
async def test_a_member_cancelled_from_under_it_is_its_own_failure():
    fut = asyncio.get_running_loop().create_future()
    b = _Gate('b')

    async def stray():
        await fut

    async def run():
        return await AsyncioGroupRunner().run([stray, b])

    task = asyncio.create_task(run())
    await b.started.wait()
    fut.cancel()
    b.release.set()

    # The caller was not cancelled, so nothing propagates as a cancellation: the stray member is reported as failed
    # and the other ran to completion.
    with pytest.raises(AsyncGroupFailedError) as ei:
        await task
    [e] = ei.value.exceptions
    assert isinstance(e, AsyncGroupMemberCancelledError)
    assert e.index == 0
    assert b.seen == ['done']
    assert [o.present for o in ei.value.outcomes] == [False, True]
    assert not task.cancelled()
