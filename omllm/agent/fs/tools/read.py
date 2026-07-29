import io
import itertools
import os.path
import typing as ta

from omcore import dataclasses as dc

from ...permissions import PermissionGranter
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription


##


DEFAULT_MAX_NUM_LINES = 2_000

MAX_LINE_LENGTH = 2_000


@dc.dataclass(frozen=True)
class ReadParams:
    file_path: str

    _: dc.KW_ONLY

    line_offset: int = 0
    num_lines: int = DEFAULT_MAX_NUM_LINES


class ReadTool(ToolClass[ReadParams]):
    name: ta.Final = 'read'

    params_cls: ta.Final = ReadParams

    description: ta.Final = ToolDescription(
        """
            Reads a file from the local filesystem. You can access any file directly by using this tool.

            Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that
            path is valid. It is okay to read a file that does not exist; an error will be returned.

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
            permission_granter: PermissionGranter,
    ) -> None:
        super().__init__()

        self._permission_granter = permission_granter

    async def execute(self, ctx: ToolContext, params: ReadParams) -> str:
        if os.path.abspath(os.path.realpath(params.file_path)) != params.file_path:
            raise ValueError('Path must be absolute')
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, params.file_path)) != cwd:
            raise ValueError('Path not under configured working directory')
        if not os.path.exists(params.file_path):
            raise ValueError('Path does not exist')
        if not os.path.isfile(params.file_path):
            raise ValueError('Path is not a file')

        if not await self._permission_granter.grant_permission(f'Read file: {params.file_path!r}'):
            raise RuntimeError('Permission denied')

        out = io.StringIO()
        out.write('<file>\n')

        zp = len(str(params.line_offset + params.num_lines))
        n = params.line_offset
        has_trunc = False  # noqa
        with open(params.file_path, errors='replace') as f:  # noqa
            fi = iter(f)

            for line in itertools.islice(fi, params.line_offset, params.line_offset + params.num_lines):
                out.write(f'{str(n + 1).zfill(zp):}|')
                line = line.removesuffix('\n')
                if len(line) > MAX_LINE_LENGTH:
                    has_trunc = True  # noqa
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

        return out.getvalue()
