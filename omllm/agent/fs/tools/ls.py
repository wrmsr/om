import io
import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...tools.classes import ToolClass
from ...types.tools import Tool
from ...types.tools import ToolContext
from ...types.tools import ToolDescription


##


@dc.dataclass(frozen=True)
class LsParams:
    dir_path: str


class LsTool(ToolClass[LsParams]):
    name: ta.Final = 'ls'

    params_cls: ta.Final = LsParams

    description: ta.Final = ToolDescription(
        'Lists the contents of the specified dir.',
        dict(
            dir_path='The dir to list the contents of. Must be an absolute path.',
        ),
    )

    async def execute(self, ctx: ToolContext, params: LsParams) -> str:
        if os.path.abspath(os.path.realpath(params.dir_path)) != params.dir_path:
            raise ValueError('Path must be absolute')
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, params.dir_path)) != cwd:
            raise ValueError('Path not under configured working directory')
        if not os.path.exists(params.dir_path):
            raise ValueError('Path does not exist')
        if not os.path.isdir(params.dir_path):
            raise ValueError('Path is not a directory')

        out = io.StringIO()
        out.write('<dir>\n')
        for e in sorted(os.scandir(params.dir_path), key=lambda e: e.name):  # noqa
            out.write(f'{e.name}{"/" if e.is_dir() else ""}\n')
        out.write('</dir>\n')

        return out.getvalue()


@lang.cached_function
def ls_tool() -> Tool:
    return LsTool().tool()
