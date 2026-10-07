import asyncio
import time

import pytest

from ....core import processes
from ....core.processes.remote.tests.support import ScriptedRemoteAgent
from ....core.rpc.channels import AsyncioStreamRpcChannel
from ..client import RemoteAgentClient


@pytest.mark.asyncs('asyncio')
async def test_close_with_an_unresponsive_agent_is_bounded():
    # An agent that never answers process.close must not be able to hold the client's close past its timeout: the
    # connection is severed instead, which fails the pending teardown and poisons its handle.
    agent = ScriptedRemoteAgent()
    agent.hang_close = True
    client = RemoteAgentClient(AsyncioStreamRpcChannel(agent.client_reader, agent.client_writer))
    await agent.start()
    await client.start()
    process = await client.processes.root.spawn(processes.ProcessSpec(['sleep', '9']))

    t0 = time.monotonic()
    await asyncio.wait_for(client.aclose(timeout_s=.2), 10.)
    assert time.monotonic() - t0 < 5.
    assert agent.closes == [process.id]
    assert process.state is processes.ProcessState.POISONED
    assert client.processes.closed
    await agent.aclose()
