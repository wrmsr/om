# ruff: noqa: UP006 UP007 UP045
"""
The wire shapes of the remote filesystem: the requests the host's `RemoteFsOps` makes of the agent's `RemoteFsService`,
and their results. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and marshaled with the lite
marshaler.
"""
import dataclasses as dc
import typing as ta

from omcore.lite.check import check


##


REMOTE_FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
REMOTE_FS_STAT_METHOD = 'fs.stat'
REMOTE_FS_READ_FILE_METHOD = 'fs.read_file'
REMOTE_FS_WRITE_FILE_METHOD = 'fs.write_file'
REMOTE_FS_LIST_DIR_METHOD = 'fs.list_dir'
REMOTE_FS_GLOB_METHOD = 'fs.glob'


##


@dc.dataclass(frozen=True)
class RemoteFsPathParams:
    path: str


@dc.dataclass(frozen=True)
class RemoteFsStatResult:
    path: str
    size: int
    is_dir: bool
    is_file: bool
    is_symlink: bool

    def __post_init__(self) -> None:
        check.arg(self.size >= 0)


@dc.dataclass(frozen=True)
class RemoteFsReadFileResult:
    data: bytes
    digest: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.digest)


@dc.dataclass(frozen=True)
class RemoteFsWriteFileParams:
    path: str
    content: bytes
    overwrite: bool
    expected_digest: ta.Optional[str]


@dc.dataclass(frozen=True)
class RemoteFsWriteFileResult:
    created: bool


@dc.dataclass(frozen=True)
class RemoteFsEntry:
    name: str
    path: str
    is_dir: bool
    is_file: bool
    is_symlink: bool


@dc.dataclass(frozen=True)
class RemoteFsGlobParams:
    pattern: str
    root: str
    max_results: ta.Optional[int]

    def __post_init__(self) -> None:
        if self.max_results is not None:
            check.arg(self.max_results >= 0)


@dc.dataclass(frozen=True)
class RemoteFsGlobResult:
    entries: ta.List[RemoteFsEntry]
    has_more: bool
