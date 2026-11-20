import asyncio
import contextlib
import sys
import typing as ta

from omcore import check
from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source
from omcore.rpc.asyncio import AsyncioRpcConnections

from ...agent.remote.client import RemoteAgentClient
from ...agent.remote.payload import get_remote_agent_payload_src


##


@contextlib.asynccontextmanager
async def local_remote_agent(
        workdir: str,
        *,
        scratch: str,
        task_path: str,
) -> ta.AsyncIterator[RemoteAgentClient]:
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        '-m',
        f'{__package__}.landlock',
        workdir,
        scratch,
        task_path,
        pyremote_build_bootstrap_source('omllm-eval'),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    stdin = check.not_none(proc.stdin)
    stdout = check.not_none(proc.stdout)
    client: RemoteAgentClient | None = None
    try:
        async with asyncio.timeout(30.):
            await PyremoteBootstrapDriver([
                get_remote_agent_payload_src(),
                'remote_agent_main()',
            ]).async_run(stdout, stdin)
            client = RemoteAgentClient(AsyncioRpcConnections.of_streams(stdout, stdin))
            await client.start()

        yield client

    finally:
        try:
            if client is not None:
                await client.aclose(timeout_s=5.)
        finally:
            stdin.close()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.)
            except TimeoutError:
                proc.kill()
                await proc.wait()
