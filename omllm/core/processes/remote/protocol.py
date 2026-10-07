# ruff: noqa: UP006 UP007 UP045
"""
The wire shapes of remote process management: the requests the host's `RemoteProcessManager` makes of the agent's
`RemoteProcessService`, their results, and the notifications the agent sends back unprompted. Lite: shared with the
remote agent amalgam, so Python 3.8 compatible and marshaled with the lite marshaler.
"""
import dataclasses as dc
import typing as ta

from omcore.lite.check import check


##


REMOTE_PROCESS_SPAWN_METHOD = 'process.spawn'
REMOTE_PROCESS_SIGNAL_METHOD = 'process.signal'
REMOTE_PROCESS_CLOSE_METHOD = 'process.close'
REMOTE_PROCESS_WRITE_METHOD = 'process.write'
REMOTE_PROCESS_WRITE_EOF_METHOD = 'process.write_eof'
REMOTE_PROCESS_RESIZE_METHOD = 'process.resize'

REMOTE_PROCESS_OUTPUT_METHOD = 'process.output'
REMOTE_PROCESS_OUTPUT_END_METHOD = 'process.output_end'
REMOTE_PROCESS_EXITED_METHOD = 'process.exited'

# The agent's unprompted notifications, which the host applies inline, in wire order.
REMOTE_PROCESS_EVENT_METHODS = frozenset([
    REMOTE_PROCESS_OUTPUT_METHOD,
    REMOTE_PROCESS_OUTPUT_END_METHOD,
    REMOTE_PROCESS_EXITED_METHOD,
])


##
# Requests


@dc.dataclass(frozen=True)
class RemoteProcessStdioSpec:
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
class RemoteProcessSpawnParams:
    argv: ta.List[str]
    cwd: ta.Optional[str]
    env: ta.Optional[ta.Dict[str, str]]
    stdio: RemoteProcessStdioSpec
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.not_empty(self.argv)


@dc.dataclass(frozen=True)
class RemoteProcessSpawnResult:
    id: str
    pid: int
    created_at: float
    name: ta.Optional[str]

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.pid >= 1)
        check.arg(self.created_at >= 0.)


@dc.dataclass(frozen=True)
class RemoteProcessSignalParams:
    id: str
    signal: int
    process_group: bool

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.signal >= 1)


@dc.dataclass(frozen=True)
class RemoteProcessClosePolicySpec:
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
class RemoteProcessCloseParams:
    id: str
    policy: RemoteProcessClosePolicySpec

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessCloseResult:
    returncode: int
    state: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.state)


@dc.dataclass(frozen=True)
class RemoteProcessWriteParams:
    id: str
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessRefParams:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessResizeParams:
    id: str
    rows: int
    cols: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.rows >= 1)
        check.arg(self.cols >= 1)


##
# Notifications (agent -> host)


@dc.dataclass(frozen=True)
class RemoteProcessOutputEvent:
    id: str
    fd: int
    data: bytes

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
        check.arg(self.fd >= 1)


@dc.dataclass(frozen=True)
class RemoteProcessOutputEndEvent:
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)


@dc.dataclass(frozen=True)
class RemoteProcessExitedEvent:
    id: str
    returncode: int

    def __post_init__(self) -> None:
        check.non_empty_str(self.id)
