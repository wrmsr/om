import glob
import io
import os.path
import typing as ta

from omcore import dataclasses as dc

from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionRequestor
from ...tools.classes import ToolClass
from ...types.tools import ToolContext
from ...types.tools import ToolDescription
from ..ops import FsOps
from ..permissions import FsPermissionTarget


##


_GLOB_MAGIC = frozenset('*?[')


def glob_root(pattern: str) -> str:
    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)

    drive, tail = os.path.splitdrive(pattern)

    # For POSIX this starts as '/'. This also does the sensible thing for drive-qualified paths on Windows.
    root = drive + os.sep

    for part in tail.lstrip(os.sep).split(os.sep):
        if any(c in part for c in _GLOB_MAGIC):
            break

        root = os.path.join(root, part)

    return root


def path_is_under(path: str, root: str) -> bool:
    path = os.path.realpath(path)
    root = os.path.realpath(root)

    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        # E.g. different drives on Windows.
        return False


def validate_glob(pattern: str, permitted_root: str) -> str:
    root = glob_root(pattern)

    if not path_is_under(root, permitted_root):
        raise ValueError(f'glob root {root!r} is outside permitted root {permitted_root!r}')

    return root


def safe_glob(pattern: str, permitted_root: str) -> ta.Generator[str]:
    validate_glob(pattern, permitted_root)

    permitted_root = os.path.realpath(permitted_root)

    for path in glob.iglob(pattern, recursive=True):
        real_path = os.path.realpath(path)

        if not path_is_under(real_path, permitted_root):
            continue

        yield path


##


@dc.dataclass(frozen=True)
class GlobToolParams:
    pattern: str


class GlobTool(ToolClass[GlobToolParams]):
    name: ta.Final = 'glob'

    params_cls: ta.Final = GlobToolParams

    description: ta.Final = ToolDescription(
        'Find files and directories matching the given glob pattern.',
        dict(
            pattern='The glob pattern to find matches for. Must begin with an absolute path.',
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

    async def execute(self, ctx: ToolContext, params: GlobToolParams) -> str:
        root = glob_root(params.pattern)
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, root)) != cwd:
            raise ValueError('Pattern not under configured working directory')

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(root, 'r'),
        )

        if not os.path.exists(root):
            raise ValueError('Path does not exist')

        out = io.StringIO()
        out.write('<glob>\n')
        for p in safe_glob(params.pattern, cwd):
            out.write(f'{p}{"/" if os.path.isdir(p) else ""}\n')
        out.write('</glob>\n')

        return out.getvalue()
