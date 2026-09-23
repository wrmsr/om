# ruff: noqa: UP006 UP007 UP045
"""JSON-compatible request/result/notification shapes shared by the host adapter and the remote agent payload."""
import dataclasses as dc
import typing as ta

from omcore.lite.check import check


##


FS_RESOLVE_PATH_METHOD = 'fs.resolve_path'
FS_STAT_METHOD = 'fs.stat'
FS_READ_FILE_METHOD = 'fs.read_file'
FS_WRITE_FILE_METHOD = 'fs.write_file'
FS_LIST_DIR_METHOD = 'fs.list_dir'
FS_GLOB_METHOD = 'fs.glob'

PROCESS_SPAWN_METHOD = 'process.spawn'
PROCESS_SIGNAL_METHOD = 'process.signal'
PROCESS_CLOSE_METHOD = 'process.close'
PROCESS_WRITE_METHOD = 'process.write'
PROCESS_WRITE_EOF_METHOD = 'process.write_eof'
PROCESS_RESIZE_METHOD = 'process.resize'

PROCESS_OUTPUT_METHOD = 'process.output'
PROCESS_OUTPUT_END_METHOD = 'process.output_end'
PROCESS_EXITED_METHOD = 'process.exited'


##
# Filesystem


@dc.dataclass(frozen=True)
class PathParams:
    path: str


@dc.dataclass(frozen=True)
class StatResult:
    path: str
    size: int
    is_dir: bool
    is_file: bool
    is_symlink: bool

    def __post_init__(self) -> None:
        check.arg(self.size >= 0)


@dc.dataclass(frozen=True)
class ReadFileResult:
    data: bytes
    digest: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.digest)


@dc.dataclass(frozen=True)
class WriteFileParams:
    path: str
    content: bytes
    overwrite: bool
    expected_digest: ta.Optional[str]


@dc.dataclass(frozen=True)
class WriteFileResult:
    created: bool


@dc.dataclass(frozen=True)
class FsEntry:
    name: str
    path: str
    is_dir: bool
    is_file: bool
    is_symlink: bool


@dc.dataclass(frozen=True)
class GlobParams:
    pattern: str
    root: str
    max_results: ta.Optional[int]

    def __post_init__(self) -> None:
        if self.max_results is not None:
            check.arg(self.max_results >= 0)


@dc.dataclass(frozen=True)
class GlobResult:
    entries: ta.List[FsEntry]
    has_more: bool


##
# Processes


@dc.dataclass(frozen=True)
class StdioSpec:
    kind: str
    stdin: ta.Optional[str] = None
    stdout: ta.Optional[str] = None
    stderr: ta.Optional[str] = None
    rows: ta.Optional[int] = None
    cols: ta.Optional[int] = None
    term: ta.Optional[str] = None

    def __post_init__(self) -> None:
        if self.kind == 'pipes':
            check.non_empty_str(self.stdin)
            check.non_empty_str(self.stdout)
            check.non_empty_str(self.stderr)
        elif self.kind == 'pty':
            check.arg(self.rows is not None and self.rows >= 1)
            check.arg(self.cols is not None and self.cols >= 1)
        else:
            raise ValueError(f'Invalid remote stdio kind: {self.kind!r}')


@dc.dataclass(frozen=True)
class SpawnParams:
    argv: ta.List[str]
    cwd: ta.Optional[str]
    env: ta.Optional[ta.Dict[str, str]]
    stdio: StdioSpec
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.not_empty(self.argv)


@dc.dataclass(frozen=True)
class SpawnResult:
    id: str
    pid: int
    created_at: float
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.pid >= 1)
        check.arg(self.created_at >= 0.)


@dc.dataclass(frozen=True)
class SignalParams:
    id: str
    signal: int
    process_group: bool

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.signal >= 1)


@dc.dataclass(frozen=True)
class ClosePolicySpec:
    signal: int
    grace_s: float
    kill_s: float
    close_stdin: bool
    process_group: bool
    drain_s: float

    def __post_init__(self) -> None:
        check.arg(self.signal >= 1)
        check.arg(self.grace_s >= 0.)
        check.arg(self.kill_s >= 0.)
        check.arg(self.drain_s >= 0.)


@dc.dataclass(frozen=True)
class CloseParams:
    id: str
    policy: ClosePolicySpec

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class CloseResult:
    returncode: int
    state: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.state)


@dc.dataclass(frozen=True)
class WriteParams:
    id: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ProcessRefParams:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ResizeParams:
    id: str
    rows: int
    cols: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.rows >= 1)
        check.arg(self.cols >= 1)


##
# Process notifications (agent -> host)


@dc.dataclass(frozen=True)
class OutputEvent:
    id: str
    fd: int
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.fd >= 1)


@dc.dataclass(frozen=True)
class OutputEndEvent:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class ExitedEvent:
    id: str
    returncode: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
