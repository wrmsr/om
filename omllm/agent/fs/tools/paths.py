import os.path

from ..common import fs_glob_root
from ..ops import FsOps


##


async def validate_tool_path(fs: FsOps, path: str) -> str:
    if not os.path.isabs(path):
        raise ValueError('Path must be absolute')

    resolved_path = await fs.resolve_path(path)
    if resolved_path != path:
        raise ValueError('Path must be absolute and canonical')

    return resolved_path


async def validate_tool_glob(fs: FsOps, pattern: str) -> str:
    """The resolved root of a pattern - the part of it before any glob magic - which is what to ask about first."""

    if not os.path.isabs(pattern):
        raise ValueError('Pattern must begin with an absolute path')

    return await fs.resolve_path(fs_glob_root(pattern))
