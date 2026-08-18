# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta

from omcore.lite.dataclasses import install_dataclass_kw_only_init


class SystevisorUnitKind(enum.Enum):
    SERVICE = 'service'
    ONESHOT = 'oneshot'


class SystevisorRestartMode(enum.Enum):
    NEVER = 'never'
    UNEXPECTED = 'unexpected'
    ALWAYS = 'always'


class SystevisorSignalScope(enum.Enum):
    PROCESS = 'process'
    SESSION = 'session'


class SystevisorStdinMode(enum.Enum):
    DEVNULL = 'devnull'
    INHERIT = 'inherit'
    FILE = 'file'


class SystevisorOutputMode(enum.Enum):
    CAPTURE = 'capture'
    FILE = 'file'
    INHERIT = 'inherit'
    DEVNULL = 'devnull'
    STDOUT = 'stdout'


class SystevisorDependencyCondition(enum.Enum):
    STARTED = 'started'
    RUNNING = 'running'
    READY = 'ready'
    COMPLETED = 'completed'


class SystevisorHealthRole(enum.Enum):
    STARTUP = 'startup'
    READINESS = 'readiness'
    LIVENESS = 'liveness'


class SystevisorHealthProbeKind(enum.Enum):
    PROCESS = 'process'
    TCP = 'tcp'
    HTTP = 'http'
    COMMAND = 'command'
    LOG_ACTIVITY = 'log_activity'


class SystevisorHealthRecovery(enum.Enum):
    NONE = 'none'
    RESTART = 'restart'
    STOP = 'stop'


class SystevisorScheduleActionKind(enum.Enum):
    START = 'start'
    STOP = 'stop'
    RESTART = 'restart'
    SHUTDOWN = 'shutdown'


class SystevisorScheduleTargetKind(enum.Enum):
    UNIT = 'unit'
    COLLECTION = 'collection'
    INSTANCE = 'instance'


class SystevisorScheduleMissedPolicy(enum.Enum):
    SKIP = 'skip'
    LATEST = 'latest'
    ALL = 'all'


class SystevisorScheduleConcurrencyPolicy(enum.Enum):
    ALLOW = 'allow'
    SKIP = 'skip'


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorNamespaceConfig:
    mount: bool = False
    ipc: bool = False
    uts: bool = False
    network: bool = False
    cgroup: bool = False
    hostname: ta.Optional[str] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorCgroupConfig:
    enabled: bool = False
    cpu_weight: ta.Optional[int] = None
    cpu_quota_usec: ta.Optional[int] = None
    cpu_period_usec: int = 100_000
    memory_low_bytes: ta.Optional[int] = None
    memory_high_bytes: ta.Optional[int] = None
    memory_max_bytes: ta.Optional[int] = None
    pids_max: ta.Optional[int] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorUnitResourcesConfig:
    observe: bool = True
    cgroup: SystevisorCgroupConfig = dc.field(default_factory=SystevisorCgroupConfig)
    namespaces: SystevisorNamespaceConfig = dc.field(default_factory=SystevisorNamespaceConfig)
    inherited_sockets: ta.Sequence[str] = ()


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorExecConfig:
    argv: ta.Sequence[str] = ()
    executable: ta.Optional[str] = None
    working_directory: ta.Optional[str] = None
    umask: ta.Optional[int] = None
    environment: ta.Mapping[str, str] = dc.field(default_factory=dict)
    inherit_environment: bool = True


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorIdentityConfig:
    user: ta.Optional[str] = None
    uid: ta.Optional[int] = None
    group: ta.Optional[str] = None
    gid: ta.Optional[int] = None
    supplementary_groups: ta.Sequence[str] = ()
    init_groups: bool = True
    set_home: bool = False


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorRestartConfig:
    mode: SystevisorRestartMode = SystevisorRestartMode.UNEXPECTED
    expected_exit_codes: ta.Sequence[int] = (0,)
    start_secs: float = 1.
    start_retries: int = 3
    backoff_initial_secs: float = 1.
    backoff_multiplier: float = 2.
    backoff_max_secs: float = 60.


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorStopConfig:
    signal: str = 'TERM'
    timeout_secs: float = 10.
    kill_signal: str = 'KILL'
    scope: SystevisorSignalScope = SystevisorSignalScope.PROCESS
    kill_scope: ta.Optional[SystevisorSignalScope] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorUnitSignalsConfig:
    forward: ta.Mapping[str, str] = dc.field(default_factory=dict)
    scope: SystevisorSignalScope = SystevisorSignalScope.PROCESS


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorInputConfig:
    mode: SystevisorStdinMode = SystevisorStdinMode.DEVNULL
    file: ta.Optional[str] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorOutputConfig:
    mode: SystevisorOutputMode = SystevisorOutputMode.CAPTURE
    file: ta.Optional[str] = None
    append: bool = True
    max_bytes: int = 50 * 1024 * 1024
    backups: int = 10
    back_buffer_bytes: int = 1024 * 1024
    emit_events: bool = False
    syslog: bool = False
    strip_ansi: ta.Optional[bool] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorStdioConfig:
    stdin: SystevisorInputConfig = dc.field(default_factory=SystevisorInputConfig)
    stdout: SystevisorOutputConfig = dc.field(default_factory=SystevisorOutputConfig)
    stderr: SystevisorOutputConfig = dc.field(default_factory=SystevisorOutputConfig)
    redirect_stderr: bool = False


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorDependenciesConfig:
    requires: ta.Mapping[str, SystevisorDependencyCondition] = dc.field(default_factory=dict)
    wants: ta.Sequence[str] = ()
    after: ta.Sequence[str] = ()
    before: ta.Sequence[str] = ()


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorHealthProbeConfig:
    name: str
    role: SystevisorHealthRole
    kind: SystevisorHealthProbeKind = SystevisorHealthProbeKind.PROCESS
    initial_delay_secs: float = 0.
    interval_secs: float = 10.
    timeout_secs: float = 3.
    success_threshold: int = 1
    failure_threshold: int = 3
    recovery: SystevisorHealthRecovery = SystevisorHealthRecovery.NONE
    argv: ta.Sequence[str] = ()
    url: ta.Optional[str] = None
    method: str = 'GET'
    expected_statuses: ta.Sequence[int] = (200,)
    host: ta.Optional[str] = None
    port: ta.Optional[int] = None
    channel: ta.Optional[str] = None
    max_quiet_secs: ta.Optional[float] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorUnitConfig:
    exec: SystevisorExecConfig
    kind: SystevisorUnitKind = SystevisorUnitKind.SERVICE
    replicas: int = 1
    replica_start: int = 0
    autostart: bool = True
    priority: int = 999
    identity: SystevisorIdentityConfig = dc.field(default_factory=SystevisorIdentityConfig)
    restart: SystevisorRestartConfig = dc.field(default_factory=SystevisorRestartConfig)
    stop: SystevisorStopConfig = dc.field(default_factory=SystevisorStopConfig)
    signals: SystevisorUnitSignalsConfig = dc.field(default_factory=SystevisorUnitSignalsConfig)
    stdio: SystevisorStdioConfig = dc.field(default_factory=SystevisorStdioConfig)
    dependencies: SystevisorDependenciesConfig = dc.field(default_factory=SystevisorDependenciesConfig)
    health: ta.Sequence[SystevisorHealthProbeConfig] = ()
    resources: SystevisorUnitResourcesConfig = dc.field(default_factory=SystevisorUnitResourcesConfig)
    tags: ta.Sequence[str] = ()


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorCollectionConfig:
    units: ta.Sequence[str]
    autostart: bool = False
    stop_together: bool = True
    description: ta.Optional[str] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorScheduleActionConfig:
    kind: SystevisorScheduleActionKind
    target_kind: ta.Optional[SystevisorScheduleTargetKind] = None
    target: ta.Optional[str] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorScheduleConfig:
    cron: str
    action: SystevisorScheduleActionConfig
    enabled: bool = True
    timezone: str = 'UTC'
    missed: SystevisorScheduleMissedPolicy = SystevisorScheduleMissedPolicy.SKIP
    max_catch_up: int = 1
    concurrency: SystevisorScheduleConcurrencyPolicy = SystevisorScheduleConcurrencyPolicy.SKIP


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorManagerLogConfig:
    level: str = 'INFO'
    file: ta.Optional[str] = None
    max_bytes: int = 50 * 1024 * 1024
    backups: int = 10
    stderr: bool = True
    journald: bool = False


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorObservationConfig:
    enabled: bool = True
    interval_secs: float = 5.
    retained_runs: int = 128
    emit_events: bool = False


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorCgroupManagerConfig:
    root: ta.Optional[str] = None


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorSelfUpdateConfig:
    enabled: bool = True
    probe_timeout_secs: float = 10.
    response_grace_secs: float = .1


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorManagerConfig:
    identifier: str = 'systevisor'
    foreground: bool = True
    user: ta.Optional[str] = None
    group: ta.Optional[str] = None
    umask: int = 0o22
    working_directory: ta.Optional[str] = None
    pid_file: ta.Optional[str] = None
    state_directory: ta.Optional[str] = None
    child_log_directory: ta.Optional[str] = None
    min_fds: int = 1024
    min_procs: int = 200
    cleanup_auto_logs: bool = True
    strip_ansi: bool = False
    process_title: ta.Optional[str] = 'systevisor'
    subreaper: bool = True
    reap_unknown_children: bool = True
    log: SystevisorManagerLogConfig = dc.field(default_factory=SystevisorManagerLogConfig)
    observation: SystevisorObservationConfig = dc.field(default_factory=SystevisorObservationConfig)
    cgroups: SystevisorCgroupManagerConfig = dc.field(default_factory=SystevisorCgroupManagerConfig)
    self_update: SystevisorSelfUpdateConfig = dc.field(default_factory=SystevisorSelfUpdateConfig)


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorApiConfig:
    unix_socket: ta.Optional[str] = None
    unix_socket_mode: int = 0o600
    tcp_host: ta.Optional[str] = None
    tcp_port: ta.Optional[int] = None
    event_backlog: int = 4096
    stream_queue_bytes: int = 1024 * 1024


@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class SystevisorConfig:
    schema_version: int = 1
    manager: SystevisorManagerConfig = dc.field(default_factory=SystevisorManagerConfig)
    api: SystevisorApiConfig = dc.field(default_factory=SystevisorApiConfig)
    units: ta.Mapping[str, SystevisorUnitConfig] = dc.field(default_factory=dict)
    collections: ta.Mapping[str, SystevisorCollectionConfig] = dc.field(default_factory=dict)
    schedules: ta.Mapping[str, SystevisorScheduleConfig] = dc.field(default_factory=dict)
    variables: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)
