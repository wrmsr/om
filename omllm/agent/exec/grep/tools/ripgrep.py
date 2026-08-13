import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ....permissions.exec import ExecPermissionTarget
from ....permissions.fs import FsPermissionTarget
from ....permissions.types import PermissionDecider
from ....tools.classes import ToolClass
from ....types.tools import ToolContext
from ....types.tools import ToolDescription
from ...ops import ExecOps
from ...ops import ExecParams


##


@dc.dataclass(frozen=True)
class RipgrepToolParams:
    args: ta.Sequence[str]

    _: dc.KW_ONLY

    timeout_s: float | None = None


class RipgrepTool(ToolClass[RipgrepToolParams]):
    name: ta.Final = 'ripgrep'

    params_cls: ta.Final = RipgrepToolParams

    description: ta.Final = ToolDescription(
        'Executes ripgrep with the given arguments in current working directory. Returns stdout and stderr.',
        dict(
            args='The arguments to pass to ripgrep.',
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

    async def execute(self, ctx: ToolContext, params: RipgrepToolParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')

        await self._permissions.check_allowed(ctx, FsPermissionTarget(cwd, 'r'))

        cmd = [
            check.not_none(shutil.which('ripgrep')),
            *params.args,
        ]

        await self._permissions.check_allowed(ctx, ExecPermissionTarget(cmd))

        result = await self._exec.exec(ExecParams(
            cmd,
            cwd=cwd,
            env=dict(os.environ),
        ))

        return check.not_none(result.stdout).decode('utf-8')
