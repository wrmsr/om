import os.path
import typing as ta

from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import FsOps
from ..permissions import FsPermissionTarget


##


@dc.dataclass(frozen=True)
class WriteToolParams:
    file_path: str
    contents: str

    _: dc.KW_ONLY

    overwrite: bool = False


class WriteTool(ToolClass[WriteToolParams]):
    name: ta.Final = 'write'

    params_cls: ta.Final = WriteToolParams

    description: ta.Final = ToolDescription(
        """
            Writes a new file at the given absolute path with the given contents.

            If `overwrite` is not true, then the file must not already exist. If `overwrite` is true, then any file at
            the given path will be overwritten.
        """,
        dict(
            file_path='The path of the file to write. Must be an absolute path.',
            contents='The contents of the file to write.',
            overwrite='Whether or not to overwrite existing files. Defaults to False.',
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

    async def execute(self, ctx: ToolContext, params: WriteToolParams) -> str:
        if os.path.abspath(os.path.realpath(params.file_path)) != params.file_path:
            raise ValueError('Path must be absolute')
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, params.file_path)) != cwd:
            raise ValueError('Path not under configured working directory')

        await self._permissions.check_allowed(ctx, FsPermissionTarget(params.file_path, 'w'))

        if os.path.exists(params.file_path):
            if not params.overwrite:
                raise ValueError('Path already exists')
            if not os.path.isfile(params.file_path):
                raise ValueError('Path already exists and is not a file')

        with open(params.file_path, 'w') as f:  # noqa
            f.write(params.contents)

        return 'The file has been written successfully.'
