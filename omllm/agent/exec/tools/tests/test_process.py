import tempfile

import pytest

from .....core import processes
from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ....types.tools import ToolEnvironment
from ..process import ProcessKillTool
from ..process import ProcessKillToolParams
from ..process import ProcessListTool
from ..process import ProcessListToolParams
from ..process import ProcessReadTool
from ..process import ProcessReadToolParams
from ..process import ProcessSpawnTool
from ..process import ProcessSpawnToolParams
from ..process import ProcessWriteTool
from ..process import ProcessWriteToolParams


def _tools():
    allow = StaticPermissionDecider(PermissionState.ALLOW)
    return (
        ProcessSpawnTool(permissions=allow),
        ProcessReadTool(),
        ProcessWriteTool(),
        ProcessKillTool(),
        ProcessListTool(),
    )


@pytest.mark.asyncs('asyncio')
async def test_process_tools_interactive():
    spawn, read, write, kill, lst = _tools()
    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            ctx = ToolContext(args={}, env=ToolEnvironment(cwd=td, processes=m.root))

            out = await spawn.execute(ctx, ProcessSpawnToolParams(command='cat', name='echoer'))
            assert 'Started background process' in out
            pid = next(iter(m.root.processes))

            # list shows it, running, with its label
            lout = await lst.execute(ctx, ProcessListToolParams())
            assert pid in lout and 'echoer' in lout and 'running' in lout

            # write -> read echoes it back; cursor advances
            await write.execute(ctx, ProcessWriteToolParams(id=pid, data='hello\n'))
            r1 = await read.execute(ctx, ProcessReadToolParams(id=pid, cursor=0, wait_s=2.0))
            assert 'hello' in r1
            cursor = int(r1.rsplit('next_cursor=', 1)[1].rstrip(']'))
            assert cursor > 0

            # reading from the new cursor with no new output -> just a status note, still running
            r2 = await read.execute(ctx, ProcessReadToolParams(id=pid, cursor=cursor, wait_s=0.1))
            assert 'hello' not in r2
            assert 'running' in r2

            # more input continues from the cursor
            await write.execute(ctx, ProcessWriteToolParams(id=pid, data='world\n'))
            r3 = await read.execute(ctx, ProcessReadToolParams(id=pid, cursor=cursor, wait_s=2.0))
            assert 'world' in r3 and 'hello' not in r3

            # kill -> terminated, gone from the scope
            kout = await kill.execute(ctx, ProcessKillToolParams(id=pid))
            assert 'Terminated' in kout
            assert pid not in m.root.processes

            with pytest.raises(ValueError, match='No such process'):
                await read.execute(ctx, ProcessReadToolParams(id=pid))


@pytest.mark.asyncs('asyncio')
async def test_process_read_exited():
    spawn, read, _, kill, _ = _tools()
    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            ctx = ToolContext(args={}, env=ToolEnvironment(cwd=td, processes=m.root))

            await spawn.execute(ctx, ProcessSpawnToolParams(command='echo one; echo two >&2; exit 4'))
            pid = next(iter(m.root.processes))

            # follow the process like a model would: read from the advancing cursor until it reports exit.
            seen = ''
            cursor = 0
            for _ in range(50):
                r = await read.execute(ctx, ProcessReadToolParams(id=pid, cursor=cursor, wait_s=2.0))
                seen += r
                cursor = int(r.rsplit('next_cursor=', 1)[1].rstrip(']'))
                if 'exited' in r:
                    break
            assert 'one' in seen and 'two' in seen
            assert 'exited (rc=4)' in seen

            # an exited (unreaped) process is still listed until cleaned up, then process_kill reaps it
            await kill.execute(ctx, ProcessKillToolParams(id=pid))
            assert pid not in m.root.processes


@pytest.mark.asyncs('asyncio')
async def test_process_tools_via_executor():
    # exercises the ToolClass param-reflection path (incl. the empty-params list tool)
    spawn, read, _, _, lst = _tools()
    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            ctx_env = ToolEnvironment(cwd=td, processes=m.root)

            res = await spawn.tool().executor(ToolContext(args={'command': 'sleep 5'}, env=ctx_env))
            assert res.error is None
            pid = next(iter(m.root.processes))

            res = await read.tool().executor(ToolContext(args={'id': pid, 'wait_s': 0.1}, env=ctx_env))
            assert res.error is None and 'running' in res.content.text

            res = await lst.tool().executor(ToolContext(args={}, env=ctx_env))
            assert res.error is None and pid in res.content.text
