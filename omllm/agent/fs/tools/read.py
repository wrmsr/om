import io
import itertools
import os.path

from omcore import lang

from ...tools.reflect import reflect_tool
from ...types.tools import Tool
from ...types.tools import ToolContext


##


DEFAULT_MAX_NUM_LINES = 2_000

MAX_LINE_LENGTH = 2_000


async def read(
        ctx: ToolContext,
        file_path: str,
        *,
        line_offset: int = 0,
        num_lines: int = DEFAULT_MAX_NUM_LINES,
) -> str:
    """
        Reads a file from the local filesystem. You can access any file directly by using this tool.

        Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that
        path is valid. It is okay to read a file that does not exist; an error will be returned.

        Usage:
        - The file_path parameter must be an absolute path, not a relative path.
        - By default, it reads up to 2000 lines starting from the beginning of the file.
        - You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to
          read the whole file by not providing these parameters.
        - Any lines longer than 2000 characters will be truncated with "...".
        - Invalid unicode characters will be replaced with the unicode replacement character "\\ufffd".
        - Results are returned using cat -n format, with line numbers starting at 1 and suffixed with a pipe character
          "|".
        - This tool cannot read binary files, including images.

        Args:
            file_path - The absolute path to the file to read.
            line_offset - The line number to start reading from (0-based).
            num_lines - The number of lines to read (defaults to 2000).
    """

    if os.path.abspath(os.path.realpath(file_path)) != file_path:
        raise ValueError('Path must be absolute')
    if ctx.env is None or (cwd := ctx.env.cwd) is None:
        raise ValueError('No working directory configured')
    if os.path.commonpath((cwd, file_path)) != cwd:
        raise ValueError('Path not under configured working directory')
    if not os.path.exists(file_path):
        raise ValueError('Path does not exist')
    if not os.path.isfile(file_path):
        raise ValueError('Path is not a file')

    out = io.StringIO()
    out.write('<file>\n')

    zp = len(str(line_offset + num_lines))
    n = line_offset
    has_trunc = False  # noqa
    with open(file_path, errors='replace') as f:  # noqa
        fi = iter(f)

        for line in itertools.islice(fi, line_offset, line_offset + num_lines):
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
            f'\n(File has more lines. Use "line_offset" parameter to read beyond line {line_offset + num_lines}.)\n',
        )

    return out.getvalue()


@lang.cached_function
def read_tool() -> Tool:
    return reflect_tool(read)
