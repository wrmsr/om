"""
Test support: the remote agent as the docker connection runs it, short of docker - the generated amalgam, bootstrapped
into a separate interpreter (the Python 3.8 venv when there is one) and driven through `RemoteAgentClient`.
"""
import asyncio
import contextlib
import pathlib
import sys
import typing as ta

from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

from ....core.rpc.channels import AsyncioStreamRpcChannel
from ..client import RemoteAgentClient
from ..payload import get_remote_agent_payload_src


##


# FIXME: wow
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_PYTHON_38 = _REPO_ROOT / '.venvs' / '8' / 'bin' / 'python'
REMOTE_AGENT_PYTHON = str(_PYTHON_38) if _PYTHON_38.is_file() else sys.executable


@contextlib.asynccontextmanager
async def remote_agent(*, stderr_sink: list[str] | None = None) -> ta.AsyncIterator[RemoteAgentClient]:
    proc = await asyncio.create_subprocess_exec(
        REMOTE_AGENT_PYTHON,
        '-c',
        pyremote_build_bootstrap_source('omllm-agent-test'),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    assert proc.stderr is not None

    client: RemoteAgentClient | None = None
    try:
        await PyremoteBootstrapDriver([
            get_remote_agent_payload_src(),
            'remote_agent_main()',
        ]).async_run(proc.stdout, proc.stdin)

        client = RemoteAgentClient(AsyncioStreamRpcChannel(proc.stdout, proc.stdin))
        await client.start()
        yield client

    finally:
        if client is not None:
            await client.aclose()
        elif proc.stdin.can_write_eof():
            proc.stdin.write_eof()
        else:
            proc.stdin.close()

        try:
            returncode = await asyncio.wait_for(proc.wait(), 10.)
        except TimeoutError:
            proc.kill()
            returncode = await proc.wait()
        stderr = (await proc.stderr.read()).decode('utf-8', 'replace')
        if stderr_sink is not None:
            stderr_sink.append(stderr)
        assert returncode == 0, stderr
