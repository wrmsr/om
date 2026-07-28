import io
import os.path

from omcore import lang

from ...tools.reflect import reflect_tool
from ...types.tools import Tool
from ...types.tools import ToolContext


##


async def ls(
        ctx: ToolContext,
        dir_path: str,
) -> str:
    """
    Lists the contents of the specified dir.

    Args:
        dir_path: The dir to list the contents of. Must be an absolute path.
    """

    if os.path.abspath(os.path.realpath(dir_path)) != dir_path:
        raise ValueError('Path must be absolute')
    if ctx.env is None or (cwd := ctx.env.cwd) is None:
        raise ValueError('No working directory configured')
    if os.path.commonpath((cwd, dir_path)) != cwd:
        raise ValueError('Path not under configured working directory')
    if not os.path.exists(dir_path):
        raise ValueError('Path does not exist')
    if not os.path.isdir(dir_path):
        raise ValueError('Path is not a directory')

    out = io.StringIO()
    out.write('<dir>\n')
    for e in sorted(os.scandir(dir_path), key=lambda e: e.name):  # noqa
        out.write(f'{e.name}{"/" if e.is_dir() else ""}\n')
    out.write('</dir>\n')

    return out.getvalue()


@lang.cached_function
def ls_tool() -> Tool:
    return reflect_tool(ls)
