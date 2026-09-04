"""
TODO:
 - rename 'shell', include user shell in tool desc
 - safe env subset
 - return json of {'stdout': stdout, 'stderr': stderr}
"""
import codecs
import os
import shutil
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .... import llm
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.progress import OutputToolProgressUpdate
from ...types.progress import ToolProgressSink
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult
from ..ops import ExecOps
from ..ops import ExecOutputSink
from ..ops import ExecParams
from ..ops import format_exec_output
from ..permissions import ExecPermissionTarget
from .details import ExecToolResultDetails


##


class _ProgressExecOutputSink(ExecOutputSink):
    """Relays a command's output to the tool's progress sink as text, decoding each stream on its own."""

    def __init__(self, progress: ToolProgressSink) -> None:
        super().__init__()

        self._progress = progress

        self._decoders: dict[int, codecs.IncrementalDecoder] = {}

    async def write(self, fd: int, data: bytes) -> None:
        try:
            decoder = self._decoders[fd]
        except KeyError:
            decoder = self._decoders[fd] = codecs.getincrementaldecoder('utf-8')(errors='replace')

        if not (text := decoder.decode(data)):
            return

        await self._progress.report(OutputToolProgressUpdate(
            text,
            stream='stderr' if fd == 2 else 'stdout',
        ))


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

    async def execute(self, ctx: ToolContext, params: BashToolParams) -> ToolResult:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if (scope := ctx.env.processes) is None:
            raise ValueError('No process scope configured')

        cmd = [
            check.not_none(shutil.which('bash')),
            '-c',
            params.command,
        ]

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            ExecPermissionTarget(cmd),
        )

        result = await self._exec.exec(
            scope,
            ExecParams(
                cmd,
                cwd=cwd,
                env=dict(os.environ),
                timeout_s=params.timeout_s,
            ),
            # Output is followed as it arrives only when someone is there to see it.
            output=_ProgressExecOutputSink(progress) if (progress := ctx.progress) is not None else None,
        )

        return ToolResult(
            content=llm.TextContent(format_exec_output(result, timeout_s=params.timeout_s)),
            details=ExecToolResultDetails(
                rc=result.rc,
                stdout=(result.stdout or b'').decode('utf-8', 'replace'),
                stderr=(result.stderr or b'').decode('utf-8', 'replace'),
                timed_out=result.timed_out,
                truncated=result.truncated,
            ),
        )
