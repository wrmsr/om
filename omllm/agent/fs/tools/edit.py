"""
TODO:
 - must read file before editing
 - must re-read file if file has been modified
 - loosened replacer helpers
 - accept diff format impl
 - injectable confirmation, diff format
"""
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
class EditToolParams:
    file_path: str
    old_string: str
    new_string: str

    _: dc.KW_ONLY

    replace_all: bool = False


class EditTool(ToolClass[EditToolParams]):
    name: ta.Final = 'edit'

    params_cls: ta.Final = EditToolParams

    description: ta.Final = ToolDescription(
        """
            Edits the given file by replacing the string given by the 'old_string' parameter with the string given by
            the 'new_string' parameter.

            The file must exist, must be a valid text file, and must be given as an absolute path.

            If the 'replace_all' parameter is false (the default) then 'new_string' must be present exactly once in the
            file, otherwise the operation will fail. If 'replace_all' is true then all instances of 'old_string' will be
            replaced by 'new_string', but the operation will fail if there are no instances of 'old_string' present in
            the file.

            For the operation to succeed, both 'old_string' and 'new_string' must be EXACT, including all exact
            indentation and other whitespace. This *includes* trailing newlines - this operates on the file as a single
            string, not a list of lines.
        """,
        dict(
            file_path='The path of the file to edit. Must be an absolute path.',
            old_string=(
                'The old string to be replaced. May not be empty, and must be exact, including all exact whitespace.'
            ),
            new_string='The new string to replace the old string with.',
            replace_all=(
                "If false (the default) then exactly one instance of 'old_string' must be present in the file to be "
                "replaced. If true then all instances of 'old_string' will be replaced by 'new_string', but at least "
                "one instance of 'old_string' must be present in the file."
            ),
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

    async def execute(self, ctx: ToolContext, params: EditToolParams) -> str:
        if os.path.abspath(os.path.realpath(params.file_path)) != params.file_path:
            raise ValueError('Path must be absolute')
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, params.file_path)) != cwd:
            raise ValueError('Path not under configured working directory')

        if not params.old_string:
            raise ValueError('The requested edit to was given an empty "old_string" parameter.')

        await self._permissions.check_allowed(ctx, FsPermissionTarget(params.file_path, 'w'))

        old_file_b = await self._fs.read_file(params.file_path)
        old_file = old_file_b.decode('utf-8')

        n = old_file.count(params.old_string)
        if not n:
            raise ValueError('The requested file to edit to did not contain the given "old_string" parameter.')

        if not params.replace_all and n != 1:
            raise ValueError('The requested file to edit contained the given "old_string" parameter multiple times.')

        new_file = old_file.replace(params.old_string, params.new_string)
        new_file_b = new_file.encode('utf-8')

        # FIXME: confirm lol

        await self._fs.write_file(params.file_path, new_file_b)

        return 'The file has been edited successfully.'
