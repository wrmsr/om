import io
import itertools
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
from .details import ReadToolResultDetails
from .paths import validate_tool_path


##


ABSOLUTE_MAX_NUM_LINES: ta.Final = 10_000
DEFAULT_MAX_NUM_LINES: ta.Final = 2_000

MAX_LINE_LENGTH: ta.Final = 2_000


@dc.dataclass(frozen=True)
class ReadToolParams:
    file_path: str

    _: dc.KW_ONLY

    line_offset: int = 0
    num_lines: int = DEFAULT_MAX_NUM_LINES


class ReadTool(ToolClass[ReadToolParams]):
    name: ta.Final = 'read'

    params_cls: ta.Final = ReadToolParams

    description: ta.Final = ToolDescription(
        """
            Reads a file from the configured workspace filesystem. You can access any permitted file directly by using
            this tool.

            If the User provides a path to a file assume that path is valid. It is okay to read a file that does not
            exist; an error will be returned.

            Usage:
            - The file_path parameter must be an absolute path, not a relative path.
            - By default, it reads up to 2000 lines starting from the beginning of the file.
            - You can optionally specify a line offset and limit (especially handy for long files), but it's recommended
              to read the whole file by not providing these parameters.
            - Any lines longer than 2000 characters will be truncated with "...".
            - Invalid unicode characters will be replaced with the unicode replacement character "\\ufffd".
            - Results are returned using cat -n format, with line numbers starting at 1 and suffixed with a pipe
              character "|".
            - This tool cannot read binary files, including images.
        """,
        dict(
            file_path='The absolute path to the file to read.',
            line_offset='The line number to start reading from (0-based).',
            num_lines='The number of lines to read (defaults to 2000).',
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

    def summarize(self, ctx: ToolContext, params: ReadToolParams) -> str:
        return params.file_path

    async def execute(self, ctx: ToolContext, params: ReadToolParams) -> ToolResult:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        file_path = await validate_tool_path(self._fs, params.file_path, cwd)
        if params.num_lines > ABSOLUTE_MAX_NUM_LINES:
            raise ValueError(f'Number of lines exceeds maximum of {ABSOLUTE_MAX_NUM_LINES}')

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(file_path, 'r'),
        )

        try:
            st = await self._fs.stat(file_path)
        except FileNotFoundError:
            raise ValueError('Path does not exist') from None
        if not st.is_file:
            raise ValueError('Path is not a file')

        file = await self._fs.read_file(file_path)

        out = io.StringIO()
        out.write('<file>\n')

        zp = len(str(params.line_offset + params.num_lines))
        n = params.line_offset
        with io.TextIOWrapper(io.BytesIO(file.data), errors='replace') as f:
            fi = iter(f)

            for line in itertools.islice(fi, params.line_offset, params.line_offset + params.num_lines):
                out.write(f'{str(n + 1).zfill(zp):}|')
                line = line.removesuffix('\n')
                if len(line) > MAX_LINE_LENGTH:
                    out.write(line[:MAX_LINE_LENGTH])
                    out.write('...')
                else:
                    out.write(line)
                out.write('\n')
                n += 1

            # tl = n
            # if (ml := lang.ilen(fi)):
            #     check.state(n == num_lines)
            #     tl += ml

            try:
                next(fi)
            except StopIteration:
                has_more = False
            else:
                has_more = True

        out.write(f'</file>\n')

        if has_more:
            out.write(
                f'\n(File has more lines. Use "line_offset" parameter to read beyond line '
                f'{params.line_offset + params.num_lines}.)\n',
            )

        return ToolResult(
            content=llm.TextContent(out.getvalue()),
            details=ReadToolResultDetails(
                path=file_path,
                line_offset=params.line_offset,
                num_lines=n - params.line_offset,
                has_more=has_more,
            ),
        )
