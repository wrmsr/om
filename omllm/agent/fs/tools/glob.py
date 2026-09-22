import io
import typing as ta

from omcore import dataclasses as dc

from .... import llm
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult
from ..ops import FsOps
from ..permissions import FsPermissionTarget
from .details import GlobToolResultDetails
from .paths import validate_tool_glob


##


MAX_MATCHES = 100


@dc.dataclass(frozen=True)
class GlobToolParams:
    pattern: str


class GlobTool(ToolClass[GlobToolParams]):
    name: ta.Final = 'glob'

    params_cls: ta.Final = GlobToolParams

    description: ta.Final = ToolDescription(
        'Find files and directories matching the given glob pattern.',
        dict(
            pattern='The glob pattern to find matches for. Must begin with an absolute path.',
        ),
    )

    def __init__(
            self,
            *,
            permissions: PermissionDecider,
            fs: FsOps,
    ) -> None:
        super().__init__()

        self._permissions = permissions
        self._fs = fs

    def summarize(self, ctx: ToolContext, params: GlobToolParams) -> str:
        return params.pattern

    async def execute(self, ctx: ToolContext, params: GlobToolParams) -> ToolResult:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        root_path, resolved_cwd = await validate_tool_glob(self._fs, params.pattern, cwd)

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(root_path, 'r'),
        )

        try:
            await self._fs.stat(root_path)
        except FileNotFoundError:
            raise ValueError('Path does not exist') from None

        result = await self._fs.glob(
            params.pattern,
            root=resolved_cwd,
            max_results=MAX_MATCHES,
        )

        out = io.StringIO()
        out.write('<glob>\n')
        for e in result.entries:
            out.write(f'{e.path}{"/" if e.is_dir else ""}\n')
        out.write('</glob>\n')
        if result.has_more:
            out.write('Too many matches, please refine your search or use the `ls` tool.\n')

        return ToolResult(
            content=llm.TextContent(out.getvalue()),
            details=GlobToolResultDetails(
                pattern=params.pattern,
                root_path=root_path,
                num_matches=len(result.entries),
                has_more=result.has_more,
            ),
        )
