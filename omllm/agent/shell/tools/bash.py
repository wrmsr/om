import asyncio
import shutil

from omcore import check
from omcore import lang

from ...tools.reflect import reflect_tool
from ...types.tools import Tool
from ...types.tools import ToolContext


##


async def bash(
        ctx: ToolContext,
        command: str,
        *,
        timeout_s: float | None = None,
) -> str:
    """
    Executes a bash command in the current working directory. Returns stdout and stderr.

    Args:
        command: The bash command to execute.
        timeout_s: An optional timeout in seconds.
    """

    if ctx.env is None or (cwd := ctx.env.cwd) is None:
        raise ValueError('No working directory configured')

    proc = await asyncio.create_subprocess_exec(
        check.not_none(shutil.which('bash')),
        '-c',
        command,
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        start_new_session=True,
    )

    try:
        stdout, stderr = await asyncio.wait_for(  # noqa
            proc.communicate(),
            timeout=timeout_s,
        )
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise

    return check.not_none(stdout).decode('utf-8')


@lang.cached_function
def bash_tool() -> Tool:
    return reflect_tool(bash)
