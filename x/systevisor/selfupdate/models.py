# @om-lite
# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta


SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION = 1


class SystevisorSelfUpdatePhase(enum.Enum):
    IDLE = 'idle'
    PROBING = 'probing'
    PREPARED = 'prepared'
    EXECUTING = 'executing'
    FAILED = 'failed'


class SystevisorHandoffFdKind(enum.Enum):
    PROCESS_PIDFD = 'process_pidfd'
    PROCESS_STDOUT = 'process_stdout'
    PROCESS_STDERR = 'process_stderr'
    PID_FILE = 'pid_file'
    ACTIVATION_SOCKET = 'activation_socket'


@dc.dataclass(frozen=True)
class SystevisorHandoffFd:
    kind: SystevisorHandoffFdKind
    owner: str
    fd: int
    device: int
    inode: int
    mode: int
    status_flags: int


@dc.dataclass(frozen=True)
class SystevisorSelfUpdateProbeRequest:
    schema_version: int
    source_path: str
    source_sha256: str
    config: ta.Mapping[str, ta.Any]
    config_digest: str


@dc.dataclass(frozen=True)
class SystevisorSelfUpdateProbeResult:
    schema_version: int
    accepted: bool
    source_sha256: str
    message: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSelfUpdateState:
    state_schema_version: int
    phase: SystevisorSelfUpdatePhase
    operation_id: ta.Optional[str]
    source_path: ta.Optional[str]
    source_sha256: ta.Optional[str]
    requested_at: ta.Optional[float]
    probe_run_id: ta.Optional[int]
    deadline_at: ta.Optional[float]
    message: ta.Optional[str]


@dc.dataclass(frozen=True)
class SystevisorHandoffManifest:
    schema_version: int
    source_path: str
    source_sha256: str
    previous_source_path: str
    previous_source_sha256: str
    created_at: float
    manager_pid: int
    operation_id: str
    mode: str
    startup_collection: ta.Optional[str]
    config_paths: ta.Sequence[str]
    recursive: bool
    state_directory: ta.Optional[str]
    config: ta.Mapping[str, ta.Any]
    config_digest: str
    source_paths: ta.Sequence[str]
    provenance: ta.Sequence[ta.Mapping[str, ta.Any]]
    engine: ta.Mapping[str, ta.Any]
    processes: ta.Sequence[ta.Mapping[str, ta.Any]]
    logs: ta.Sequence[ta.Mapping[str, ta.Any]]
    event_bus: ta.Mapping[str, ta.Any]
    operations: ta.Mapping[str, ta.Any]
    manager_runtime: ta.Mapping[str, ta.Any]
    inherited_sockets: ta.Sequence[ta.Mapping[str, ta.Any]]
    cgroups: ta.Sequence[ta.Mapping[str, ta.Any]]
    fds: ta.Sequence[SystevisorHandoffFd]
