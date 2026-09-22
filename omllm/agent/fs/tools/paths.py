import os.path

from ..ops import FsOps
from ..ops import glob_root
from ..ops import path_is_under


##


async def validate_tool_path(fs: FsOps, path: str, cwd: str) -> str:
    if not os.path.isabs(path):
        raise ValueError('Path must be absolute')

    resolved_path = await fs.resolve_path(path)
    if resolved_path != path:
        raise ValueError('Path must be absolute and canonical')

    resolved_cwd = await fs.resolve_path(cwd)
    if not path_is_under(resolved_path, resolved_cwd):
        raise ValueError('Path not under configured working directory')

    return resolved_path


async def validate_tool_glob(fs: FsOps, pattern: str, cwd: str) -> tuple[str, str]:
    root_path = await fs.resolve_path(glob_root(pattern))
    resolved_cwd = await fs.resolve_path(cwd)
    if not path_is_under(root_path, resolved_cwd):
        raise ValueError('Pattern not under configured working directory')

    return root_path, resolved_cwd
