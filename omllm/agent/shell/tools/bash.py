"""
TODO:
 - rename 'shell', include user shell in tool desc
 - safe env subset
"""
import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...permissions.shell import ShellPermissionTarget
from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import ShellExecuteParams
from ..ops import ShellOps


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

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            shell: ShellOps,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._shell = shell

    async def execute(self, ctx: ToolContext, params: BashParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')

        await self._permissions.check_allowed(ctx, ShellPermissionTarget(params.command))

        result = await self._shell.shell_execute(ShellExecuteParams(
            [
                check.not_none(shutil.which('bash')),
                '-c',
                params.command,
            ],
            cwd=cwd,
            env=dict(os.environ),
        ))

        return check.not_none(result.stdout).decode('utf-8')
