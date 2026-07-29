import asyncio
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription


##


@dc.dataclass(frozen=True)
class BashParams:
    command: str

    _: dc.KW_ONLY

    timeout_s: float | None = None


class BashTool(ToolClass[BashParams]):
    name: ta.Final = 'bash'

    params_cls: ta.Final = BashParams

    description: ta.Final = ToolDescription(
        'Executes a bash command in the current working directory. Returns stdout and stderr.',
        dict(
            command='The bash command to execute.',
            timeout_s='An optional timeout in seconds.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: BashParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')

        proc = await asyncio.create_subprocess_exec(
            check.not_none(shutil.which('bash')),
            '-c',
            params.command,
            cwd=cwd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(  # noqa
                proc.communicate(),
                timeout=params.timeout_s,
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise

        return check.not_none(stdout).decode('utf-8')
