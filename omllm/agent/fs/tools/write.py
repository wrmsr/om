import typing as ta

from omcore import dataclasses as dc

from .... import llm
from ....core import ui
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequest
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ...types.tools import ToolResult
from ..common import FsFileChangedError
from ..ops import FsFile
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

    async def _read_replaced(
            self,
            requestor: PermissionRequestor,
            file_path: str,
            *,
            overwrite: bool,
    ) -> FsFile | None:
        """The file the write would replace, if any - read so the change can be shown before it is made."""

        try:
            st = await self._fs.stat(file_path)
        except FileNotFoundError:
            return None

        if not st.is_file:
            raise ValueError('Path already exists and is not a file')
        if not overwrite:
            raise ValueError('Path already exists')

        await self._permissions.check_allowed(PermissionRequest(
            requestor,
            FsPermissionTarget(file_path, 'r'),
        ))

        try:
            return await self._fs.read_file(file_path)
        except FileNotFoundError:
            return None

    @staticmethod
    def _build_change_text(file_path: str, replaced: FsFile | None, contents: str) -> ui.Text:
        if replaced is None:
            old = ''
        else:
            try:
                old = replaced.data.decode('utf-8')
            except UnicodeDecodeError:
                return ui.Text.of(f'Replacing {len(replaced.data)} bytes of non-text content in {file_path}\n')

        return ui.DiffText(
            old=old,
            new=contents,
            path=file_path,
        )

    async def execute(self, ctx: ToolContext, params: WriteToolParams) -> ToolResult:
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        file_path = await validate_tool_path(self._fs, params.file_path, cwd)

        requestor = PermissionRequestor(tool_context=ctx)

        replaced = await self._read_replaced(
            requestor,
            file_path,
            overwrite=params.overwrite,
        )

        change = self._build_change_text(file_path, replaced, params.contents)

        await self._permissions.check_allowed(PermissionRequest(
            requestor,
            FsPermissionTarget(file_path, 'w'),
            preview=change,
        ))

        # The write replaces exactly what was shown, or creates the file shown as new: anything else appearing there
        # while the decision was pending fails it.
        contents_b = params.contents.encode('utf-8')
        try:
            wr = await self._fs.write_file(
                file_path,
                contents_b,
                overwrite=replaced is not None,
                expected_digest=replaced.digest if replaced is not None else None,
            )
        except FileExistsError:
            raise ValueError('Path already exists') from None
        except IsADirectoryError:
            raise ValueError('Path already exists and is not a file') from None
        except FsFileChangedError:
            raise ValueError('The file changed before the write was made. Read it again.') from None

        return ToolResult(
            content=llm.TextContent('The file has been written successfully.'),
            details=WriteToolResultDetails(
                path=file_path,
                num_bytes=len(contents_b),
                created=wr.created,
            ),
            display=change,
        )
