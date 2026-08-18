"""
TODO:
 - rename 'shell', include user shell in tool desc
 - safe env subset
 - return json of {'stdout': stdout, 'stderr': stderr}
"""
import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import ExecOps
from ..ops import ExecParams
from ..ops import format_exec_output
from ..permissions import ExecPermissionTarget


##


@dc.dataclass(frozen=True)
class BashToolParams:
    command: str

    _: dc.KW_ONLY

    timeout_s: float | None = None


class BashTool(ToolClass[BashToolParams]):
    name: ta.Final = 'bash'

    params_cls: ta.Final = BashToolParams

    description: ta.Final = ToolDescription(
        'Executes a bash command in the current working directory. Returns stdout and stderr.',
        dict(
            command='The bash command to execute.',
            timeout_s='An optional timeout in seconds.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            exec: ExecOps,  # noqa
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._exec = exec

    async def execute(self, ctx: ToolContext, params: BashToolParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if (scope := ctx.env.processes) is None:
            raise ValueError('No process scope configured')

        cmd = [
            check.not_none(shutil.which('bash')),
            '-c',
            params.command,
        ]

        await self._permissions.check_allowed(ctx, ExecPermissionTarget(cmd))

        result = await self._exec.exec(scope, ExecParams(
            cmd,
            cwd=cwd,
            env=dict(os.environ),
            timeout_s=params.timeout_s,
        ))

        return format_exec_output(result, timeout_s=params.timeout_s)
