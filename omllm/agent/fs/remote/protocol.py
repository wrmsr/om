# ruff: noqa: UP006 UP007 UP045
"""
The wire shapes of the remote filesystem: the requests the host's `RemoteFsOps` makes of the agent's `RemoteFsService`,
and their results. Lite: shared with the remote agent amalgam, so Python 3.8 compatible and marshaled with the lite
marshaler.

File content crosses the connection in chunks, so a file's size is bounded by memory rather than by the rpc's frame
limit. A read starts with `fs.read_file`, which returns either the whole file or its first chunk and a handle through
which `fs.read_chunk` fetches the rest; the agent releases the handle with the last chunk, or on `fs.read_abort`. A
write which fits one chunk is a single `fs.write_file`; a larger one is staged with `fs.write_begin` and
`fs.write_chunk`, then made visible atomically by `fs.write_commit` (or discarded by `fs.write_abort`), with exactly the
semantics of the single call.
"""
import dataclasses as dc
import typing as ta

from omcore.lite.check import check


##


REMOTE_FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
REMOTE_FS_STAT_METHOD = 'fs.stat'
REMOTE_FS_LIST_DIR_METHOD = 'fs.list_dir'
REMOTE_FS_GLOB_METHOD = 'fs.glob'

REMOTE_FS_READ_FILE_METHOD = 'fs.read_file'
REMOTE_FS_READ_CHUNK_METHOD = 'fs.read_chunk'
REMOTE_FS_READ_ABORT_METHOD = 'fs.read_abort'

REMOTE_FS_WRITE_FILE_METHOD = 'fs.write_file'
REMOTE_FS_WRITE_BEGIN_METHOD = 'fs.write_begin'
REMOTE_FS_WRITE_CHUNK_METHOD = 'fs.write_chunk'
REMOTE_FS_WRITE_COMMIT_METHOD = 'fs.write_commit'
REMOTE_FS_WRITE_ABORT_METHOD = 'fs.write_abort'

# No piece of file content on the wire exceeds this, so that no frame approaches the rpc's limit once base64 encoded.
# The agent refuses larger ones.
REMOTE_FS_MAX_CHUNK_BYTES = 8 * 1024 * 1024


##
# Paths


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


##
# Handles


@dc.dataclass(frozen=True)
class RemoteFsHandleParams:
    handle: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)


@dc.dataclass(frozen=True)
class RemoteFsHandleResult:
    handle: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)


##
# Reads


@dc.dataclass(frozen=True)
class RemoteFsReadFileParams:
    path: str
    max_bytes: int

    def __post_init__(self) -> None:
        check.arg(0 < self.max_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsReadFileResult:
    """The file's first `max_bytes`: all of it, with its digest, or else the rest follows through `handle`."""

    data: bytes
    digest: ta.Optional[str]
    handle: ta.Optional[str]

    def __post_init__(self) -> None:
        check.arg((self.digest is None) != (self.handle is None))
        if self.digest is not None:
            check.non_empty_str(self.digest)
        if self.handle is not None:
            check.non_empty_str(self.handle)


@dc.dataclass(frozen=True)
class RemoteFsReadChunkParams:
    handle: str
    max_bytes: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)
        check.arg(0 < self.max_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsReadChunkResult:
    """More of the file. A digest means that was the last of it, and its handle is gone."""

    data: bytes
    digest: ta.Optional[str]

    def __post_init__(self) -> None:
        if self.digest is not None:
            check.non_empty_str(self.digest)


##
# Writes


@dc.dataclass(frozen=True)
class RemoteFsWriteFileParams:
    path: str
    content: bytes
    overwrite: bool
    expected_digest: ta.Optional[str]

    def __post_init__(self) -> None:
        check.arg(len(self.content) <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsWriteFileResult:
    created: bool


@dc.dataclass(frozen=True)
class RemoteFsWriteChunkParams:
    handle: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)
        check.arg(len(self.data) <= REMOTE_FS_MAX_CHUNK_BYTES)


@dc.dataclass(frozen=True)
class RemoteFsWriteCommitParams:
    handle: str
    overwrite: bool
    expected_digest: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.handle)
