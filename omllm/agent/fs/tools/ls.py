import functools
import io
import os.path
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .... import llm
from ...tools.reflect import instantiate_tool_params
from ...tools.reflect import reflect_tool_params
from ...types.tools import Tool
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult


##


@dc.dataclass(frozen=True)
class LsParams:
    dir_path: str


LS_DESCRIPTION = ToolDescription(
    'Lists the contents of the specified dir.',
    dict(
        dir_path='The dir to list the contents of. Must be an absolute path.',
    ),
)


class LsToolHandler:
    def __init__(self, params_instantiator: ta.Callable[[ToolContext], LsParams]) -> None:
        super().__init__()

        self._params_instantiator = params_instantiator

    async def invoke(self, ctx: ToolContext) -> ToolResult:
        params = self._params_instantiator(ctx)

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

        return ToolResult(
            content=llm.TextContent(out.getvalue()),
        )


@lang.cached_function
def ls_tool() -> Tool:
    tool_params = reflect_tool_params(
        LsParams,
        description=LS_DESCRIPTION,
    )

    handler = LsToolHandler(
        functools.partial(
            instantiate_tool_params,
            LsParams,
            tool_params,
        ),
    )

    return Tool(
        llm_tool=llm.Tool(
            name='ls',
            description=LS_DESCRIPTION.description,
            params=tool_params,
            type='string',
        ),
        executor=handler.invoke,
    )
