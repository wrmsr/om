import asyncio

import pytest

from omcore.lite.marshal import marshal_obj

from .... import processes
from ..protocol import REMOTE_PROCESS_EXITED_METHOD
from ..protocol import REMOTE_PROCESS_OUTPUT_END_METHOD
from ..protocol import REMOTE_PROCESS_OUTPUT_METHOD
from ..protocol import RemoteProcessOutputEndEvent
from ..protocol import RemoteProcessOutputEvent
from .support import ScriptedRemoteAgent
from .support import scripted_remote_process_client


@pytest.mark.asyncs('asyncio')
async def test_cancelled_spawn_closes_the_orphan():
    # A spawn the caller gives up on has still forked a child on the agent: it gets closed as soon as its id is known.
    agent = ScriptedRemoteAgent()
    agent.spawn_gate = asyncio.Event()
    client = await scripted_remote_process_client(agent)

    spawning = asyncio.create_task(client.manager.root.spawn(processes.ProcessSpec(['sleep', '9'])))
    await agent.spawn_started.wait()
    spawning.cancel()
    with pytest.raises(asyncio.CancelledError):
        await spawning

    agent.spawn_gate.set()
    await asyncio.wait_for(agent.close_requested.wait(), 5.)
    assert agent.closes == ['p1']
    assert not client.manager.processes

    await client.aclose()
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_events_are_delivered_in_order_when_a_subscriber_suspends():
    agent = ScriptedRemoteAgent()
    client = await scripted_remote_process_client(agent)

    delivered = []

    async def on_event(event):
        if isinstance(event, processes.ProcessExitedEvent):
            await asyncio.sleep(.02)
        delivered.append(type(event).__name__)

    client.manager.subscribe(on_event)
    process = await client.manager.root.spawn(processes.ProcessSpec(['true']))
    await agent.notify(REMOTE_PROCESS_EXITED_METHOD, {'id': process.id, 'returncode': 0})
    assert await process.wait(5.) == 0
    await process.aclose()
    await client.aclose()
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
        await agent.notify(REMOTE_PROCESS_EXITED_METHOD, {'id': process_id, 'returncode': 0})
        await agent.notify(REMOTE_PROCESS_OUTPUT_END_METHOD, {'id': process_id})

    agent.before_spawn_reply = exit_first
    client = await scripted_remote_process_client(agent)

    delivered = []
    client.manager.subscribe(lambda event: delivered.append(type(event).__name__))
    process = await client.manager.root.spawn(processes.ProcessSpec(['true']))
    assert process.exited
    assert process.output_ended
    assert await process.wait(0) == 0
    await process.aclose()
    await client.aclose()
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
        await agent.notify(
            REMOTE_PROCESS_OUTPUT_METHOD,
            marshal_obj(RemoteProcessOutputEvent(id=params['id'], fd=1, data=b'last words')),
        )
        await agent.notify(REMOTE_PROCESS_OUTPUT_END_METHOD, marshal_obj(RemoteProcessOutputEndEvent(id=params['id'])))
        return {'returncode': 3, 'state': 'reaped'}

    agent.on_close = close_with_trailing_output
    client = await scripted_remote_process_client(agent)

    process = await client.manager.root.spawn(processes.ProcessSpec(['true']))
    await process.aclose()
    assert process.returncode == 3
    assert process.output_ended
    assert process.spool.read_available().data(1) == b'last words'

    await client.aclose()
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_timed_out_waits_leave_no_task_behind():
    agent = ScriptedRemoteAgent()
    client = await scripted_remote_process_client(agent)
    process = await client.manager.root.spawn(processes.ProcessSpec(['sleep', '9']))

    await asyncio.sleep(0)
    before = len(asyncio.all_tasks())
    for _ in range(3):
        with pytest.raises(processes.ProcessTimeoutError):
            await process.wait(.01)
        assert not await process.wait_output_ended(.01)
    await asyncio.sleep(0)
    assert len(asyncio.all_tasks()) == before

    await client.aclose()
    await agent.aclose()


@pytest.mark.asyncs('asyncio')
async def test_remote_builtin_errors_come_back_typed():
    # What the agent raises as a builtin with the same meaning on both sides is raised here as that builtin, as the
    # local manager would have - not as a generic remote error.
    agent = ScriptedRemoteAgent()
    agent.write_error = BrokenPipeError('stdin is closed')
    agent.signal_error = ProcessLookupError('gone')
    client = await scripted_remote_process_client(agent)
    process = await client.manager.root.spawn(processes.ProcessSpec(
        ['cat'],
        stdio=processes.ProcessStdio(stdin='pipe'),
    ))

    with pytest.raises(BrokenPipeError, match='stdin is closed'):
        await process.write(b'x')
    with pytest.raises(ProcessLookupError, match='gone'):
        await process.signal(15)
    assert agent.signals == [{'id': process.id, 'signal': 15, 'process_group': True}]

    await client.aclose()
    await agent.aclose()
