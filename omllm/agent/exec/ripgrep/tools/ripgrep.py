import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .....core import processes
from ....fs.permissions import FsPermissionTarget
from ....permissions.types import PermissionDecider
from ....tools.classes import ToolClass
from ....types.tools import ToolContext
from ....types.tools import ToolDescription
from ...ops import ExecOps
from ...ops import ExecParams
from ...ops import format_exec_output
from ...permissions import ExecPermissionTarget


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
        """\
        Executes ripgrep with the given arguments in current working directory. Returns stdout and stderr.

        If you are familiar with ripgrep, prefer to use this over invoking regular 'grep' or similar tools via shell
        execution.
        """,
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
            sandbox: bool = False,  # FIXME: really dog?
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._exec = exec
        self._sandbox = sandbox

    async def execute(self, ctx: ToolContext, params: RipgrepToolParams) -> str:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if (scope := ctx.env.processes) is None:
            raise ValueError('No process scope configured')

        #

        from ..args.parsing import RgArgvParser

        parser = RgArgvParser()
        parsed = parser.parse(params.args)  # noqa

        #

        await self._permissions.check_allowed(ctx, FsPermissionTarget(cwd, 'r'))

        cmd = [
            check.not_none(shutil.which('rg')),
            *params.args,
        ]

        await self._permissions.check_allowed(ctx, ExecPermissionTarget(cmd))

        options: list[processes.ProcessOption] = []
        if self._sandbox:
            # ripgrep only needs to read the search tree - confine it to the cwd, no writes, no network.
            options.append(processes.platform_sandbox(processes.SandboxPolicy(
                read_roots=[cwd],
            )))

        result = await self._exec.exec(scope, ExecParams(
            cmd,
            cwd=cwd,
            env=dict(os.environ),
            timeout_s=params.timeout_s,
            options=options,
        ))

        return format_exec_output(result, timeout_s=params.timeout_s)
