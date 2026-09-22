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
from .details import WriteToolResultDetails
from .paths import validate_tool_path


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

    def summarize(self, ctx: ToolContext, params: WriteToolParams) -> str:
        return params.file_path

    async def execute(self, ctx: ToolContext, params: WriteToolParams) -> ToolResult:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        file_path = await validate_tool_path(self._fs, params.file_path, cwd)

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(file_path, 'w'),
        )

        contents_b = params.contents.encode('utf-8')
        try:
            wr = await self._fs.write_file(
                file_path,
                contents_b,
                overwrite=params.overwrite,
            )
        except FileExistsError:
            raise ValueError('Path already exists') from None
        except IsADirectoryError:
            raise ValueError('Path already exists and is not a file') from None

        return ToolResult(
            content=llm.TextContent('The file has been written successfully.'),
            details=WriteToolResultDetails(
                path=file_path,
                num_bytes=len(contents_b),
                created=wr.created,
            ),
        )
