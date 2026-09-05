import glob
import io
import os.path
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
from .details import GlobToolResultDetails


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


MAX_MATCHES = 100


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
        self._fs = fs  # FIXME: use lol

    async def execute(self, ctx: ToolContext, params: GlobToolParams) -> ToolResult:
        root_path = glob_root(params.pattern)
        if ctx.env is None or (cwd := ctx.env.cwd) is None:
            raise ValueError('No working directory configured')
        if os.path.commonpath((cwd, root_path)) != cwd:
            raise ValueError('Pattern not under configured working directory')

        await self._permissions.check_allowed(
            PermissionRequestor(tool_context=ctx),
            FsPermissionTarget(root_path, 'r'),
        )

        if not os.path.exists(root_path):
            raise ValueError('Path does not exist')

        out = io.StringIO()
        out.write('<glob>\n')
        num_matches = 0
        has_more = False
        for p in safe_glob(params.pattern, cwd):
            num_matches += 1
            if num_matches >= MAX_MATCHES:
                has_more = True
                out.write('</glob>\n')
                out.write('Too many matches, please refine your search or use the `ls` tool.\n')
                break
            out.write(f'{p}{"/" if os.path.isdir(p) else ""}\n')
        out.write('</glob>\n')

        return ToolResult(
            content=llm.TextContent(out.getvalue()),
            details=GlobToolResultDetails(
                pattern=params.pattern,
                root_path=root_path,
                num_matches=num_matches,
                has_more=has_more,
            ),
        )
