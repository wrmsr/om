import asyncio
import time

import pytest

from ....core import processes
from ..protocol import PROCESS_EXITED_METHOD
from ..protocol import PROCESS_OUTPUT_END_METHOD
from ..protocol import PROCESS_OUTPUT_METHOD
from ..protocol import encode_remote_bytes
from .support import ScriptedRemoteAgent


@pytest.mark.asyncs('asyncio')
async def test_close_with_an_unresponsive_agent_is_bounded():
    # An agent that never answers process.close must not be able to hold the client's close past its timeout: the
    # connection is severed instead, which fails the pending teardown and poisons its handle.
    agent = ScriptedRemoteAgent()
    agent.hang_close = True
    await agent.start()
    process = await agent.client.processes.root.spawn(processes.ProcessSpec(['sleep', '9']))

    t0 = time.monotonic()
    await asyncio.wait_for(agent.client.aclose(timeout_s=.2), 10.)
    assert time.monotonic() - t0 < 5.
    assert agent.closes == [process.id]
    assert process.state is processes.ProcessState.POISONED
    assert agent.client.processes.closed
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_cancelled_spawn_closes_the_orphan():
    # A spawn the caller gives up on has still forked a child on the agent: it gets closed as soon as its id is known.
    agent = ScriptedRemoteAgent()
    agent.spawn_gate = asyncio.Event()
    await agent.start()

    spawning = asyncio.create_task(agent.client.processes.root.spawn(processes.ProcessSpec(['sleep', '9'])))
    await agent.spawn_started.wait()
    spawning.cancel()
    with pytest.raises(asyncio.CancelledError):
        await spawning

    agent.spawn_gate.set()
    await asyncio.wait_for(agent.close_requested.wait(), 5.)
    assert agent.closes == ['p1']
    assert not agent.client.processes.processes

    await agent.client.aclose()
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_events_are_delivered_in_order_when_a_subscriber_suspends():
    agent = ScriptedRemoteAgent()
    await agent.start()

    delivered = []

    async def on_event(event):
        if isinstance(event, processes.ProcessExitedEvent):
            await asyncio.sleep(.02)
        delivered.append(type(event).__name__)

    agent.client.processes.subscribe(on_event)
    process = await agent.client.processes.root.spawn(processes.ProcessSpec(['true']))
    await agent.notify(PROCESS_EXITED_METHOD, {'id': process.id, 'returncode': 0})
    assert await process.wait(5.) == 0
    await process.aclose()
    await agent.client.aclose()
    assert [n for n in delivered if n.startswith('Process')] == [
        'ProcessSpawnedEvent',
        'ProcessExitedEvent',
        'ProcessReapedEvent',
    ]
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_events_are_ordered_when_the_exit_arrives_before_the_spawn_reply():
    # A short-lived child can exit, and the agent report it, before the host has even seen the spawn reply.
    agent = ScriptedRemoteAgent()

    async def exit_first(process_id):
        await agent.notify(PROCESS_EXITED_METHOD, {'id': process_id, 'returncode': 0})
        await agent.notify(PROCESS_OUTPUT_END_METHOD, {'id': process_id})

    agent.before_spawn_reply = exit_first
    await agent.start()

    delivered = []
    agent.client.processes.subscribe(lambda event: delivered.append(type(event).__name__))
    process = await agent.client.processes.root.spawn(processes.ProcessSpec(['true']))
    assert process.exited
    assert process.output_ended
    assert await process.wait(0) == 0
    await process.aclose()
    await agent.client.aclose()
    assert [n for n in delivered if n.startswith('Process')] == [
        'ProcessSpawnedEvent',
        'ProcessExitedEvent',
        'ProcessReapedEvent',
    ]
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_output_sent_before_the_close_reply_is_in_the_spool():
    # Output is applied inline, in wire order: whatever the agent sends right before its close reply is in the spool by
    # the time the close completes.
    agent = ScriptedRemoteAgent()

    async def close_with_trailing_output(params):
        await agent.notify(PROCESS_OUTPUT_METHOD, {
            'id': params['id'],
            'fd': 1,
            'data': encode_remote_bytes(b'last words'),
        })
        await agent.notify(PROCESS_OUTPUT_END_METHOD, {'id': params['id']})
        return {'returncode': 3, 'state': 'reaped'}

    agent.on_close = close_with_trailing_output
    await agent.start()

    process = await agent.client.processes.root.spawn(processes.ProcessSpec(['true']))
    await process.aclose()
    assert process.returncode == 3
    assert process.output_ended
    assert process.spool.read_available().data(1) == b'last words'

    await agent.client.aclose()
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_timed_out_waits_leave_no_task_behind():
    agent = ScriptedRemoteAgent()
    await agent.start()
    process = await agent.client.processes.root.spawn(processes.ProcessSpec(['sleep', '9']))

    await asyncio.sleep(0)
    before = len(asyncio.all_tasks())
    for _ in range(3):
        with pytest.raises(processes.ProcessTimeoutError):
            await process.wait(.01)
        assert not await process.wait_output_ended(.01)
    await asyncio.sleep(0)
    assert len(asyncio.all_tasks()) == before

    await agent.client.aclose()
    await agent.aclose()
