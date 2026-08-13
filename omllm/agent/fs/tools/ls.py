import io
import os.path
import typing as ta

from omcore import dataclasses as dc

from ...permissions.fs import FsPermissionTarget
from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import FsOps


##


@dc.dataclass(frozen=True)
class LsToolParams:
    dir_path: str


class LsTool(ToolClass[LsToolParams]):
    name: ta.Final = 'ls'

    params_cls: ta.Final = LsToolParams

    description: ta.Final = ToolDescription(
        'Lists the contents of the specified dir.',
        dict(
            dir_path='The dir to list the contents of. Must be an absolute path.',
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

    async def execute(self, ctx: ToolContext, params: LsToolParams) -> str:
        if os.path.abspath(os.path.realpath(params.dir_path)) != params.dir_path:
            raise ValueError('Path must be absolute')
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, params.dir_path)) != cwd:
            raise ValueError('Path not under configured working directory')

        dir_path = params.dir_path
        if not dir_path.endswith('/'):
            dir_path += '/'

        await self._permissions.check_allowed(ctx, FsPermissionTarget(dir_path, 'r'))

        if not os.path.exists(dir_path):
            raise ValueError('Path does not exist')
        if not os.path.isdir(dir_path):
            raise ValueError('Path is not a directory')

        out = io.StringIO()
        out.write('<dir>\n')
        for e in sorted(await self._fs.list_dir(dir_path), key=lambda e: e.name):  # noqa
            out.write(f'{e.name}{"/" if e.is_dir else ""}\n')
        out.write('</dir>\n')

        return out.getvalue()
