import io
import os.path
import typing as ta

from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequest
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import FsOps
from ..permissions import FsPermissionTarget
from .paths import validate_tool_path


##


@dc.dataclass(frozen=True)
class LsToolParams:
    dir_path: str


class LsTool(ToolClass[LsToolParams]):
    name: ta.Final = 'ls'

    params_cls: ta.Final = LsToolParams

    description: ta.Final = ToolDescription(
        'Lists the contents of the specified dir. Directories are listed with a trailing slash.',
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

    def summarize(self, ctx: ToolContext, params: LsToolParams) -> str:
        return params.dir_path

    async def execute(self, ctx: ToolContext, params: LsToolParams) -> str:
        dir_path = await validate_tool_path(self._fs, params.dir_path)

        await self._permissions.check_allowed(PermissionRequest(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(dir_path, 'r'),
        ))

        try:
            st = await self._fs.stat(dir_path)
        except FileNotFoundError:
            raise ValueError('Path does not exist') from None
        if not st.is_dir:
            raise ValueError('Path is not a directory')

        out = io.StringIO()
        out.write('<dir>\n')
        for e in sorted(await self._fs.list_dir(dir_path), key=lambda e: os.path.basename(e.path)):  # noqa
            out.write(f'{os.path.basename(e.path)}{"/" if e.is_dir else ""}\n')
        out.write('</dir>\n')

        return out.getvalue()
