# ruff: noqa: PYI034 SLF001 UP006 UP007 UP037 UP045
import abc
import ctypes
import dataclasses as dc
import enum
import errno
import fcntl
import grp
import os
import os.path
import pwd
import resource
import signal
import types
import typing as ta

from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorExecConfig
from ..configs.models import SystevisorHealthProbeKind
from ..configs.models import SystevisorIdentityConfig
from ..configs.models import SystevisorInputConfig
from ..configs.models import SystevisorOutputConfig
from ..configs.models import SystevisorOutputMode
from ..configs.models import SystevisorSignalScope
from ..configs.models import SystevisorStdinMode
from ..configs.models import SystevisorStdioConfig
from ..configs.models import SystevisorStopConfig
from ..configs.models import SystevisorUnitConfig
from ..configs.models import SystevisorUnitResourcesConfig
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from ..core.effects import SystevisorRunHealthProbeEffect
from ..core.effects import SystevisorSignalProcessEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.identities import SystevisorHealthCheckId
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..core.identities import SystevisorUnitName
from ..core.signals import systevisor_parse_signal_name
from ..core.state import SystevisorEngineState


_SYSTEVISOR_PROCESSES_MANAGED_OUTPUT_MODES = frozenset({
    SystevisorOutputMode.CAPTURE,
    SystevisorOutputMode.FILE,
    SystevisorOutputMode.STDOUT,
})

_SYSTEVISOR_PROCESSES_EXEC_ERROR_LIMIT = 16 * 1024


class SystevisorOwnedProcessStatus(enum.Enum):
    SPAWNING = 'spawning'
    RUNNING = 'running'
    EXIT_OBSERVED = 'exit_observed'
    REAPED = 'reaped'


class SystevisorOwnedProcessPurpose(enum.Enum):
    SERVICE = 'service'
    HEALTH_COMMAND = 'health_command'
    SELF_UPDATE_PROBE = 'self_update_probe'


class SystevisorProcessOutputChannel(enum.Enum):
    STDOUT = 'stdout'
    STDERR = 'stderr'


class SystevisorProcessError(Exception):
    pass


class SystevisorProcessOwnershipError(SystevisorProcessError):
    pass


class SystevisorProcessSpawnError(SystevisorProcessError):
    pass


class SystevisorChildPidProvider(Abstract):
    @abc.abstractmethod
    def child_pids(self) -> ta.Sequence[int]:
        raise NotImplementedError


class SystevisorSystemChildPidProvider(SystevisorChildPidProvider):
    def child_pids(self) -> ta.Sequence[int]:
        if not os.path.isdir('/proc/self/task'):
            return ()
        path = f'/proc/self/task/{os.getpid()}/children'
        try:
            with open(path) as children_file:
                raw = children_file.read()
        except OSError:
            return ()
        return tuple(int(value) for value in raw.split() if value.isdigit() and int(value) > 0)


@dc.dataclass(frozen=True)
class SystevisorResolvedIdentity:
    uid: ta.Optional[int]
    gid: ta.Optional[int]
    groups: ta.Optional[ta.Sequence[int]]
    user_name: ta.Optional[str]
    home: ta.Optional[str]


@dc.dataclass(frozen=True)
class SystevisorChildContext:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    spec: SystevisorDesiredInstanceSpec
    identity: SystevisorResolvedIdentity
    environment: ta.Mapping[str, str]


class SystevisorChildModifier:
    def parent_prepare(self, context: SystevisorChildContext) -> None:
        pass

    def parent_spawned(self, context: SystevisorChildContext, pid: int) -> None:
        pass

    def parent_spawn_failed(self, context: SystevisorChildContext) -> None:
        pass

    def parent_retired(self, context: SystevisorChildContext) -> None:
        pass

    def preserved_fds(self, context: SystevisorChildContext) -> ta.Sequence[int]:
        return ()

    def reserved_child_fds(self, context: SystevisorChildContext) -> ta.Sequence[int]:
        return ()

    def child_environment(self, context: SystevisorChildContext) -> ta.Mapping[str, str]:
        return {}

    def before_identity(self, context: SystevisorChildContext) -> None:
        pass

    def after_identity(self, context: SystevisorChildContext) -> None:
        pass


@dc.dataclass
class SystevisorPreparedProcessFds:
    stdin_child_fd: ta.Optional[int]
    stdout_child_fd: ta.Optional[int]
    stdout_parent_fd: ta.Optional[int]
    stderr_child_fd: ta.Optional[int]
    stderr_parent_fd: ta.Optional[int]
    exec_error_parent_fd: int
    exec_error_child_fd: int

    def all_fds(self) -> ta.Sequence[int]:
        return tuple({
            fd
            for fd in (
                self.stdin_child_fd,
                self.stdout_child_fd,
                self.stdout_parent_fd,
                self.stderr_child_fd,
                self.stderr_parent_fd,
                self.exec_error_parent_fd,
                self.exec_error_child_fd,
            )
            if fd is not None
        })


@dc.dataclass(frozen=True)
class SystevisorPreparedProcess:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    spec: SystevisorDesiredInstanceSpec
    identity: SystevisorResolvedIdentity
    environment: ta.Mapping[str, str]
    fds: SystevisorPreparedProcessFds
    max_fd: int
    isolate_session: bool


@dc.dataclass(frozen=True)
class SystevisorOwnedProcessState:
    state_schema_version: int
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    pid: int
    pidfd: ta.Optional[int]
    session_requested: bool
    session_id: ta.Optional[int]
    birth_identity: ta.Optional[str]
    status: SystevisorOwnedProcessStatus
    stdout_fd: ta.Optional[int]
    stderr_fd: ta.Optional[int]
    exec_error_fd: ta.Optional[int]
    return_code: ta.Optional[int]
    signal_lease_count: int
    purpose: SystevisorOwnedProcessPurpose
    health_check_id: ta.Optional[SystevisorHealthCheckId]
    observe_resources: bool


@dc.dataclass
class SystevisorOwnedProcess:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    pid: int
    pidfd: ta.Optional[int]
    session_requested: bool
    session_id: ta.Optional[int]
    birth_identity: ta.Optional[str]
    status: SystevisorOwnedProcessStatus
    stdout_fd: ta.Optional[int]
    stderr_fd: ta.Optional[int]
    exec_error_fd: ta.Optional[int]
    exec_error_buffer: bytearray = dc.field(default_factory=bytearray)
    return_code: ta.Optional[int] = None
    signal_lease_count: int = 0
    exit_reported: bool = False
    purpose: SystevisorOwnedProcessPurpose = SystevisorOwnedProcessPurpose.SERVICE
    health_check_id: ta.Optional[SystevisorHealthCheckId] = None
    child_context: ta.Optional[SystevisorChildContext] = None
    observe_resources: bool = True

    def snapshot(self) -> SystevisorOwnedProcessState:
        return SystevisorOwnedProcessState(
            state_schema_version=3,
            run_id=self.run_id,
            instance_id=self.instance_id,
            pid=self.pid,
            pidfd=self.pidfd,
            session_requested=self.session_requested,
            session_id=self.session_id,
            birth_identity=self.birth_identity,
            status=self.status,
            stdout_fd=self.stdout_fd,
            stderr_fd=self.stderr_fd,
            exec_error_fd=self.exec_error_fd,
            return_code=self.return_code,
            signal_lease_count=self.signal_lease_count,
            purpose=self.purpose,
            health_check_id=self.health_check_id,
            observe_resources=self.observe_resources,
        )


@dc.dataclass(frozen=True)
class SystevisorProcessSpawned:
    state: SystevisorOwnedProcessState


@dc.dataclass(frozen=True)
class SystevisorProcessExecResult:
    run_id: SystevisorRunId
    succeeded: bool
    message: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorObservedProcessExit:
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    return_code: int


@dc.dataclass(frozen=True)
class SystevisorUnknownProcessExit:
    pid: int
    return_code: int


@dc.dataclass(frozen=True)
class SystevisorProcessRetirement:
    state: SystevisorOwnedProcessState
    stdout_fd: ta.Optional[int]
    stderr_fd: ta.Optional[int]


@dc.dataclass(frozen=True)
class SystevisorSignalDelivery:
    run_id: SystevisorRunId
    signal: int
    scope: SystevisorSignalScope
    delivered: bool


class SystevisorSignalLease:
    def __init__(
            self,
            manager: 'SystevisorProcessManager',
            process: SystevisorOwnedProcess,
            *,
            allow_observed_exit: bool,
    ) -> None:
        self._manager = manager
        self._process = process
        self._allow_observed_exit = allow_observed_exit
        self._active = True

    @property
    def run_id(self) -> SystevisorRunId:
        return self._process.run_id

    @property
    def active(self) -> bool:
        return self._active

    def release(self) -> None:
        if not self._active:
            raise SystevisorProcessOwnershipError('signal lease was already released')
        self._manager._release_signal_lease(self)
        self._active = False

    def __enter__(self) -> 'SystevisorSignalLease':
        if not self._active:
            raise SystevisorProcessOwnershipError('signal lease is not active')
        return self

    def __exit__(
            self,
            exc_type: ta.Optional[ta.Type[BaseException]],
            exc_val: ta.Optional[BaseException],
            exc_tb: ta.Optional[types.TracebackType],
    ) -> None:
        self.release()


class SystevisorProcessSignalBackend(Abstract):
    @abc.abstractmethod
    def send_process(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def send_session(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        raise NotImplementedError


class SystevisorPosixProcessSignalBackend(SystevisorProcessSignalBackend):
    def send_process(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        process = lease._process
        if process.pidfd is not None and _systevisor_processes_pidfd_send_signal(process.pidfd, signal_number):
            return True
        try:
            os.kill(process.pid, signal_number)
        except ProcessLookupError:
            return False
        return True

    def send_session(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        process = lease._process
        if process.session_id != process.pid:
            raise SystevisorProcessOwnershipError('process does not own an isolated session')
        try:
            os.killpg(process.session_id, signal_number)
        except ProcessLookupError:
            return False
        return True


def _systevisor_processes_set_cloexec(fd: int, cloexec: bool) -> None:
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    if cloexec:
        flags |= fcntl.FD_CLOEXEC
    else:
        flags &= ~fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def _systevisor_processes_make_pipe(*, parent_nonblocking: bool) -> ta.Tuple[int, int]:
    read_fd, write_fd = os.pipe()
    _systevisor_processes_set_cloexec(read_fd, True)
    _systevisor_processes_set_cloexec(write_fd, True)
    if parent_nonblocking:
        os.set_blocking(read_fd, False)
    return read_fd, write_fd


def _systevisor_processes_close_quietly(fd: ta.Optional[int]) -> None:
    if fd is None:
        return
    try:
        os.close(fd)
    except OSError:
        pass


def _systevisor_processes_read_birth_identity(pid: int) -> ta.Optional[str]:
    path = f'/proc/{pid}/stat'
    try:
        with open(path) as stat_file:
            value = stat_file.read()
    except OSError:
        return None
    close_paren = value.rfind(')')
    if close_paren < 0:
        return None
    fields_after_command = value[close_paren + 2:].split()
    if len(fields_after_command) <= 19:
        return None
    return fields_after_command[19]


def _systevisor_processes_read_pidfd_pid(fd: int) -> ta.Optional[int]:
    try:
        with open(f'/proc/self/fdinfo/{fd}') as fdinfo_file:
            lines = fdinfo_file.readlines()
    except OSError:
        return None
    for line in lines:
        key, separator, value = line.partition(':')
        if separator and key == 'Pid':
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None


def _systevisor_processes_pidfd_open(pid: int) -> ta.Optional[int]:
    pidfd_open = getattr(os, 'pidfd_open', None)
    if pidfd_open is not None:
        try:
            return ta.cast(int, pidfd_open(pid, 0))
        except OSError:
            return None

    libc = ctypes.CDLL(None, use_errno=True)
    libc_pidfd_open = getattr(libc, 'pidfd_open', None)
    if libc_pidfd_open is None:
        return None
    libc_pidfd_open.argtypes = [ctypes.c_int, ctypes.c_uint]
    libc_pidfd_open.restype = ctypes.c_int
    result = libc_pidfd_open(pid, 0)
    if result >= 0:
        return ta.cast(int, result)
    error_number = ctypes.get_errno()
    if error_number in {errno.ENOSYS, errno.EINVAL, errno.EPERM, errno.ESRCH}:
        return None
    return None


def _systevisor_processes_pidfd_send_signal(pidfd: int, signal_number: int) -> bool:
    pidfd_send_signal = getattr(signal, 'pidfd_send_signal', None)
    if pidfd_send_signal is not None:
        try:
            pidfd_send_signal(pidfd, signal_number)
        except ProcessLookupError:
            return False
        return True

    libc = ctypes.CDLL(None, use_errno=True)
    libc_pidfd_send_signal = getattr(libc, 'pidfd_send_signal', None)
    if libc_pidfd_send_signal is None:
        return False
    libc_pidfd_send_signal.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
    libc_pidfd_send_signal.restype = ctypes.c_int
    result = libc_pidfd_send_signal(pidfd, signal_number, None, 0)
    if result == 0:
        return True
    error_number = ctypes.get_errno()
    if error_number == errno.ESRCH:
        return False
    raise OSError(error_number, os.strerror(error_number))


def _systevisor_processes_resolve_identity(config: SystevisorIdentityConfig) -> SystevisorResolvedIdentity:
    passwd_entry: ta.Any = None
    if config.user is not None:
        try:
            passwd_entry = pwd.getpwnam(config.user)
        except KeyError as exc:
            raise SystevisorProcessSpawnError(f'unknown user: {config.user!r}') from exc
    elif config.uid is not None:
        try:
            passwd_entry = pwd.getpwuid(config.uid)
        except KeyError:
            passwd_entry = None

    uid = config.uid if config.uid is not None else (passwd_entry.pw_uid if passwd_entry is not None else None)
    user_name = passwd_entry.pw_name if passwd_entry is not None else config.user
    home = passwd_entry.pw_dir if passwd_entry is not None else None

    if config.group is not None:
        try:
            gid = grp.getgrnam(config.group).gr_gid
        except KeyError as exc:
            raise SystevisorProcessSpawnError(f'unknown group: {config.group!r}') from exc
    elif config.gid is not None:
        gid = config.gid
    elif passwd_entry is not None:
        gid = passwd_entry.pw_gid
    else:
        gid = None

    groups: ta.Optional[ta.Sequence[int]] = None
    if config.supplementary_groups:
        resolved_groups: ta.List[int] = []
        for group_name in config.supplementary_groups:
            try:
                resolved_groups.append(grp.getgrnam(group_name).gr_gid)
            except KeyError as exc:
                raise SystevisorProcessSpawnError(f'unknown supplementary group: {group_name!r}') from exc
        groups = tuple(dict.fromkeys(resolved_groups))
    elif config.init_groups and user_name is not None and gid is not None:
        groups = tuple(os.getgrouplist(user_name, gid))

    effective_uid = os.geteuid()
    if uid is not None and effective_uid != 0 and uid != effective_uid:
        raise SystevisorProcessSpawnError(f'cannot switch from uid {effective_uid} to uid {uid}')
    effective_gid = os.getegid()
    if gid is not None and effective_uid != 0 and gid != effective_gid:
        raise SystevisorProcessSpawnError(f'cannot switch from gid {effective_gid} to gid {gid}')

    return SystevisorResolvedIdentity(uid=uid, gid=gid, groups=groups, user_name=user_name, home=home)


def _systevisor_processes_max_fd() -> int:
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    limit = soft_limit if soft_limit != resource.RLIM_INFINITY else hard_limit
    if limit == resource.RLIM_INFINITY:
        limit = 1024 * 1024
    return int(limit)


def _systevisor_processes_open_input(spec: SystevisorDesiredInstanceSpec) -> ta.Optional[int]:
    input_config = spec.unit.stdio.stdin
    if input_config.mode is SystevisorStdinMode.INHERIT:
        return None
    if input_config.mode is SystevisorStdinMode.DEVNULL:
        return os.open(os.devnull, os.O_RDONLY)
    if input_config.mode is SystevisorStdinMode.FILE and input_config.file is not None:
        return os.open(input_config.file, os.O_RDONLY)
    raise SystevisorProcessSpawnError(f'invalid stdin config: {input_config!r}')


def _systevisor_processes_open_output(
        mode: SystevisorOutputMode,
) -> ta.Tuple[ta.Optional[int], ta.Optional[int]]:
    if mode in _SYSTEVISOR_PROCESSES_MANAGED_OUTPUT_MODES:
        parent_fd, child_fd = _systevisor_processes_make_pipe(parent_nonblocking=True)
        return child_fd, parent_fd
    if mode is SystevisorOutputMode.INHERIT:
        return None, None
    if mode is SystevisorOutputMode.DEVNULL:
        return os.open(os.devnull, os.O_WRONLY), None
    raise SystevisorProcessSpawnError(f'invalid output mode: {mode!r}')


def _systevisor_processes_prepare_fds(spec: SystevisorDesiredInstanceSpec) -> SystevisorPreparedProcessFds:
    created: ta.List[int] = []
    try:
        stdin_child_fd = _systevisor_processes_open_input(spec)
        if stdin_child_fd is not None:
            created.append(stdin_child_fd)

        stdout_child_fd, stdout_parent_fd = _systevisor_processes_open_output(spec.unit.stdio.stdout.mode)
        created.extend(fd for fd in (stdout_child_fd, stdout_parent_fd) if fd is not None)

        if spec.unit.stdio.redirect_stderr:
            stderr_child_fd = None
            stderr_parent_fd = None
        else:
            stderr_child_fd, stderr_parent_fd = _systevisor_processes_open_output(spec.unit.stdio.stderr.mode)
            created.extend(fd for fd in (stderr_child_fd, stderr_parent_fd) if fd is not None)

        exec_error_parent_fd, exec_error_child_fd = _systevisor_processes_make_pipe(parent_nonblocking=True)
        created.extend((exec_error_parent_fd, exec_error_child_fd))
        return SystevisorPreparedProcessFds(
            stdin_child_fd=stdin_child_fd,
            stdout_child_fd=stdout_child_fd,
            stdout_parent_fd=stdout_parent_fd,
            stderr_child_fd=stderr_child_fd,
            stderr_parent_fd=stderr_parent_fd,
            exec_error_parent_fd=exec_error_parent_fd,
            exec_error_child_fd=exec_error_child_fd,
        )
    except BaseException:
        for fd in created:
            _systevisor_processes_close_quietly(fd)
        raise


def _systevisor_processes_prepare(
        effect: SystevisorSpawnProcessEffect,
) -> SystevisorPreparedProcess:
    spec = effect.spec
    identity = _systevisor_processes_resolve_identity(spec.unit.identity)
    environment = dict(os.environ) if spec.unit.exec.inherit_environment else {}
    environment.update(spec.unit.exec.environment)
    if spec.unit.identity.set_home and identity.home is not None:
        environment['HOME'] = identity.home
    if identity.user_name is not None:
        environment.setdefault('USER', identity.user_name)
        environment.setdefault('LOGNAME', identity.user_name)

    fds = _systevisor_processes_prepare_fds(spec)
    return SystevisorPreparedProcess(
        run_id=effect.run_id,
        instance_id=effect.instance_id,
        spec=spec,
        identity=identity,
        environment=environment,
        fds=fds,
        max_fd=_systevisor_processes_max_fd(),
        isolate_session=(
            spec.unit.stop.scope is SystevisorSignalScope.SESSION or
            spec.unit.stop.kill_scope is SystevisorSignalScope.SESSION or
            spec.unit.signals.scope is SystevisorSignalScope.SESSION
        ),
    )


def _systevisor_processes_close_child_fds(prepared: SystevisorPreparedProcess) -> None:
    _systevisor_processes_close_quietly(prepared.fds.stdin_child_fd)
    _systevisor_processes_close_quietly(prepared.fds.stdout_child_fd)
    _systevisor_processes_close_quietly(prepared.fds.stderr_child_fd)
    _systevisor_processes_close_quietly(prepared.fds.exec_error_child_fd)


def _systevisor_processes_close_parent_fds(prepared: SystevisorPreparedProcess) -> None:
    _systevisor_processes_close_quietly(prepared.fds.stdout_parent_fd)
    _systevisor_processes_close_quietly(prepared.fds.stderr_parent_fd)
    _systevisor_processes_close_quietly(prepared.fds.exec_error_parent_fd)


def _systevisor_processes_child_dup(source_fd: ta.Optional[int], destination_fd: int) -> None:
    if source_fd is None:
        return
    if source_fd != destination_fd:
        os.dup2(source_fd, destination_fd)
    os.set_inheritable(destination_fd, True)


def _systevisor_processes_child_close_except(preserved_fds: ta.Iterable[int], max_fd: int) -> None:
    preserved = sorted({fd for fd in preserved_fds if 3 <= fd < max_fd})
    lower = 3
    for fd in preserved:
        if lower < fd:
            os.closerange(lower, fd)
        lower = fd + 1
    if lower < max_fd:
        os.closerange(lower, max_fd)


def _systevisor_processes_child_write_error(fd: int, exc: BaseException) -> None:
    message = f'{type(exc).__name__}: {exc}'.encode(
        'utf-8',
        'backslashreplace',
    )[:_SYSTEVISOR_PROCESSES_EXEC_ERROR_LIMIT]
    while message:
        try:
            written = os.write(fd, message)
        except OSError:
            return
        message = message[written:]


def _systevisor_processes_child_main(
        prepared: SystevisorPreparedProcess,
        modifiers: ta.Sequence[SystevisorChildModifier],
) -> ta.NoReturn:
    try:
        fds = prepared.fds
        _systevisor_processes_close_quietly(fds.stdout_parent_fd)
        _systevisor_processes_close_quietly(fds.stderr_parent_fd)
        _systevisor_processes_close_quietly(fds.exec_error_parent_fd)

        if prepared.isolate_session:
            os.setsid()
        if prepared.spec.unit.exec.working_directory is not None:
            os.chdir(prepared.spec.unit.exec.working_directory)
        if prepared.spec.unit.exec.umask is not None:
            os.umask(prepared.spec.unit.exec.umask)

        _systevisor_processes_child_dup(fds.stdin_child_fd, 0)
        _systevisor_processes_child_dup(fds.stdout_child_fd, 1)
        if prepared.spec.unit.stdio.redirect_stderr:
            os.dup2(1, 2)
            os.set_inheritable(2, True)
        else:
            _systevisor_processes_child_dup(fds.stderr_child_fd, 2)

        environment = dict(prepared.environment)
        context = SystevisorChildContext(
            run_id=prepared.run_id,
            instance_id=prepared.instance_id,
            spec=prepared.spec,
            identity=prepared.identity,
            environment=environment,
        )
        for modifier in modifiers:
            for key, value in modifier.child_environment(context).items():
                previous = environment.get(key)
                if previous is not None and previous != value:
                    raise SystevisorProcessSpawnError(f'child environment collision for {key!r}')
                environment[key] = value
        preserved_fds = {fds.exec_error_child_fd}
        for modifier in modifiers:
            preserved_fds.update(modifier.preserved_fds(context))
        _systevisor_processes_child_close_except(preserved_fds, prepared.max_fd)

        for modifier in modifiers:
            modifier.before_identity(context)

        identity = prepared.identity
        if identity.groups is not None and os.geteuid() == 0:
            os.setgroups(identity.groups)
        if identity.gid is not None and identity.gid != os.getegid():
            os.setgid(identity.gid)
        if identity.uid is not None and identity.uid != os.geteuid():
            os.setuid(identity.uid)

        for modifier in modifiers:
            modifier.after_identity(context)

        argv = tuple(prepared.spec.unit.exec.argv)
        executable = prepared.spec.unit.exec.executable or argv[0]
        os.execvpe(executable, argv, environment)
    except BaseException as exc:  # noqa: BLE001
        _systevisor_processes_child_write_error(prepared.fds.exec_error_child_fd, exc)
    os._exit(127)


def _systevisor_processes_child_context(prepared: SystevisorPreparedProcess) -> SystevisorChildContext:
    return SystevisorChildContext(
        run_id=prepared.run_id,
        instance_id=prepared.instance_id,
        spec=prepared.spec,
        identity=prepared.identity,
        environment=prepared.environment,
    )


def _systevisor_processes_relocate_reserved_fds(
        prepared: SystevisorPreparedProcess,
        modifiers: ta.Sequence[SystevisorChildModifier],
        context: SystevisorChildContext,
) -> None:
    reserved = {
        fd
        for modifier in modifiers
        for fd in modifier.reserved_child_fds(context)
    }
    if not reserved:
        return
    if min(reserved) < 3 or max(reserved) >= prepared.max_fd:
        raise SystevisorProcessSpawnError('child modifier reserved an invalid descriptor')
    exec_error_fd = prepared.fds.exec_error_child_fd
    if exec_error_fd in reserved:
        duplicate = fcntl.fcntl(exec_error_fd, fcntl.F_DUPFD_CLOEXEC, max(reserved) + 1)
        os.close(exec_error_fd)
        prepared.fds.exec_error_child_fd = duplicate


def _systevisor_processes_wait_result_return_code(result: ta.Any) -> int:
    if result.si_code == getattr(os, 'CLD_EXITED', 1):
        return int(result.si_status)
    return -int(result.si_status)


def _systevisor_processes_wait_status_return_code(wait_status: int) -> int:
    if os.WIFEXITED(wait_status):
        return os.WEXITSTATUS(wait_status)
    if os.WIFSIGNALED(wait_status):
        return -os.WTERMSIG(wait_status)
    raise SystevisorProcessOwnershipError(f'unexpected final wait status: {wait_status}')


class SystevisorProcessManager:
    def __init__(
            self,
            *,
            signal_backend: ta.Optional[SystevisorProcessSignalBackend] = None,
            child_modifiers: ta.Iterable[SystevisorChildModifier] = (),
            child_pid_provider: ta.Optional[SystevisorChildPidProvider] = None,
    ) -> None:
        if not all(hasattr(os, name) for name in ('waitid', 'WNOWAIT', 'P_PID', 'WEXITED', 'WNOHANG')):
            raise RuntimeError('systevisor requires waitid with WNOWAIT')
        self._signal_backend = signal_backend or SystevisorPosixProcessSignalBackend()
        self._child_modifiers = tuple(child_modifiers)
        self._child_pid_provider = child_pid_provider or SystevisorSystemChildPidProvider()
        self._reap_unknown_children = False
        self._processes_by_run: ta.Dict[SystevisorRunId, SystevisorOwnedProcess] = {}
        self._processes_by_pid: ta.Dict[int, SystevisorOwnedProcess] = {}

    def set_reap_unknown_children(self, enabled: bool) -> None:
        self._reap_unknown_children = enabled

    def needs_wait_polling(self) -> bool:
        return self.has_processes() or self._reap_unknown_children

    def snapshot_states(self) -> ta.Sequence[SystevisorOwnedProcessState]:
        return tuple(process.snapshot() for process in self._processes_by_run.values())

    def child_contexts(self) -> ta.Mapping[SystevisorRunId, SystevisorChildContext]:
        return {
            process.run_id: process.child_context
            for process in self._processes_by_run.values()
            if process.child_context is not None
        }

    def get_state(self, run_id: SystevisorRunId) -> ta.Optional[SystevisorOwnedProcessState]:
        process = self._processes_by_run.get(run_id)
        return process.snapshot() if process is not None else None

    def has_processes(self) -> bool:
        return bool(self._processes_by_run)

    def take_output_fd(
            self,
            run_id: SystevisorRunId,
            channel: SystevisorProcessOutputChannel,
    ) -> ta.Optional[int]:
        process = self._processes_by_run.get(run_id)
        if process is None:
            raise SystevisorProcessOwnershipError(f'run is not owned: {run_id}')
        if channel is SystevisorProcessOutputChannel.STDOUT:
            fd = process.stdout_fd
            process.stdout_fd = None
        elif channel is SystevisorProcessOutputChannel.STDERR:
            fd = process.stderr_fd
            process.stderr_fd = None
        else:
            raise TypeError(channel)
        return fd

    def spawn(self, effect: SystevisorSpawnProcessEffect) -> SystevisorProcessSpawned:
        if effect.run_id <= 0:
            raise SystevisorProcessOwnershipError('service run identities must be positive')
        return self._spawn(effect, SystevisorOwnedProcessPurpose.SERVICE, None)

    def spawn_health_command(
            self,
            effect: SystevisorRunHealthProbeEffect,
    ) -> ta.Tuple[SystevisorRunId, SystevisorProcessSpawned]:
        if effect.probe.kind is not SystevisorHealthProbeKind.COMMAND:
            raise TypeError(effect.probe.kind)
        run_id = SystevisorRunId(-int(effect.check_id))
        unit = dc.replace(
            effect.spec.unit,
            exec=dc.replace(
                effect.spec.unit.exec,
                argv=tuple(effect.probe.argv),
                executable=None,
            ),
            stdio=SystevisorStdioConfig(
                stdin=SystevisorInputConfig(mode=SystevisorStdinMode.DEVNULL),
                stdout=SystevisorOutputConfig(mode=SystevisorOutputMode.DEVNULL),
                stderr=SystevisorOutputConfig(mode=SystevisorOutputMode.DEVNULL),
            ),
            stop=dc.replace(effect.spec.unit.stop, scope=SystevisorSignalScope.SESSION),
        )
        spec = dc.replace(effect.spec, spec_digest=f'health-command:{effect.check_id}', unit=unit)
        spawn_effect = SystevisorSpawnProcessEffect(
            run_id=run_id,
            instance_id=effect.instance_id,
            spec=spec,
        )
        return run_id, self._spawn(
            spawn_effect,
            SystevisorOwnedProcessPurpose.HEALTH_COMMAND,
            effect.check_id,
        )

    def spawn_internal(
            self,
            run_id: SystevisorRunId,
            argv: ta.Sequence[str],
            purpose: SystevisorOwnedProcessPurpose,
    ) -> SystevisorProcessSpawned:
        if run_id >= 0:
            raise SystevisorProcessOwnershipError('internal run identities must be negative')
        if purpose is SystevisorOwnedProcessPurpose.SERVICE:
            raise SystevisorProcessOwnershipError('internal processes cannot have service purpose')
        unit = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=tuple(argv)),
            stdio=SystevisorStdioConfig(
                stdin=SystevisorInputConfig(mode=SystevisorStdinMode.DEVNULL),
                stdout=SystevisorOutputConfig(mode=SystevisorOutputMode.DEVNULL),
                stderr=SystevisorOutputConfig(mode=SystevisorOutputMode.DEVNULL),
            ),
            stop=SystevisorStopConfig(scope=SystevisorSignalScope.SESSION),
            resources=SystevisorUnitResourcesConfig(observe=False),
        )
        instance_id = SystevisorInstanceId('systevisor.self-update')
        spec = SystevisorDesiredInstanceSpec(
            instance_id=instance_id,
            unit_name=SystevisorUnitName('systevisor.self-update'),
            slot=0,
            spec_digest=f'internal:{purpose.value}:{int(run_id)}',
            unit=unit,
        )
        return self._spawn(
            SystevisorSpawnProcessEffect(run_id=run_id, instance_id=instance_id, spec=spec),
            purpose,
            None,
        )

    def handoff_issues(self) -> ta.Sequence[str]:
        issues: ta.List[str] = []
        for process in self._processes_by_run.values():
            label = f'run {int(process.run_id)} pid {process.pid}'
            if process.purpose is not SystevisorOwnedProcessPurpose.SERVICE:
                issues.append(f'{label} is an internal {process.purpose.value} process')
            if process.status is not SystevisorOwnedProcessStatus.RUNNING:
                issues.append(f'{label} is {process.status.value}')
            if process.exec_error_fd is not None:
                issues.append(f'{label} still owns an exec handshake')
            if process.signal_lease_count:
                issues.append(f'{label} has {process.signal_lease_count} active signal lease(s)')
        return tuple(issues)

    def rehydrate(
            self,
            states: ta.Iterable[SystevisorOwnedProcessState],
            engine_state: SystevisorEngineState,
    ) -> None:
        if self._processes_by_run or self._processes_by_pid:
            raise SystevisorProcessOwnershipError('process manager can only be rehydrated before use')
        processes: ta.List[SystevisorOwnedProcess] = []
        try:
            for state in states:
                if state.state_schema_version != 3:
                    raise SystevisorProcessOwnershipError(
                        f'unsupported process state schema: {state.state_schema_version}',
                    )
                if state.run_id <= 0 or state.purpose is not SystevisorOwnedProcessPurpose.SERVICE:
                    raise SystevisorProcessOwnershipError('only service processes may cross a handoff')
                if state.status is not SystevisorOwnedProcessStatus.RUNNING:
                    raise SystevisorProcessOwnershipError(
                        f'run {state.run_id} is not stable: {state.status.value}',
                    )
                if state.signal_lease_count or state.exec_error_fd is not None:
                    raise SystevisorProcessOwnershipError(
                        f'run {state.run_id} has non-transferable process state',
                    )
                if state.run_id in self._processes_by_run or state.pid in self._processes_by_pid:
                    raise SystevisorProcessOwnershipError('duplicate process identity in handoff')
                instance = engine_state.instances.get(state.instance_id)
                if instance is None or instance.run_id != state.run_id:
                    raise SystevisorProcessOwnershipError(
                        f'engine does not claim handed-off run {state.run_id}',
                    )

                try:
                    wait_result = os.waitid(
                        os.P_PID,
                        state.pid,
                        os.WEXITED | os.WNOHANG | os.WNOWAIT,
                    )
                except ChildProcessError as exc:
                    raise SystevisorProcessOwnershipError(
                        f'wait ownership was lost for run {state.run_id} pid {state.pid}',
                    ) from exc
                birth_identity = _systevisor_processes_read_birth_identity(state.pid)
                if (
                        (wait_result is None or wait_result.si_pid == 0) and
                        state.birth_identity is not None and
                        birth_identity != state.birth_identity
                ):
                    raise SystevisorProcessOwnershipError(
                        f'birth identity changed for run {state.run_id} pid {state.pid}',
                    )
                if state.pidfd is not None:
                    try:
                        os.fstat(state.pidfd)
                    except OSError as exc:
                        raise SystevisorProcessOwnershipError(
                            f'pidfd is not open for run {state.run_id}',
                        ) from exc
                    pidfd_pid = _systevisor_processes_read_pidfd_pid(state.pidfd)
                    if pidfd_pid is not None and pidfd_pid != state.pid:
                        raise SystevisorProcessOwnershipError(
                            f'pidfd identity changed for run {state.run_id}',
                        )

                status: SystevisorOwnedProcessStatus = state.status
                return_code = state.return_code
                if wait_result is not None and wait_result.si_pid != 0:
                    status = SystevisorOwnedProcessStatus.EXIT_OBSERVED
                    return_code = _systevisor_processes_wait_result_return_code(wait_result)
                process = SystevisorOwnedProcess(
                    run_id=state.run_id,
                    instance_id=state.instance_id,
                    pid=state.pid,
                    pidfd=state.pidfd,
                    session_requested=state.session_requested,
                    session_id=state.session_id,
                    birth_identity=state.birth_identity,
                    status=status,
                    stdout_fd=state.stdout_fd,
                    stderr_fd=state.stderr_fd,
                    exec_error_fd=None,
                    return_code=return_code,
                    purpose=state.purpose,
                    child_context=SystevisorChildContext(
                        run_id=state.run_id,
                        instance_id=state.instance_id,
                        spec=instance.desired_spec,
                        identity=SystevisorResolvedIdentity(None, None, None, None, None),
                        environment={},
                    ),
                    observe_resources=state.observe_resources,
                )
                self._processes_by_run[state.run_id] = process
                self._processes_by_pid[state.pid] = process
                processes.append(process)
        except BaseException:
            for process in processes:
                self._processes_by_run.pop(process.run_id, None)
                self._processes_by_pid.pop(process.pid, None)
            raise

    def _spawn(
            self,
            effect: SystevisorSpawnProcessEffect,
            purpose: SystevisorOwnedProcessPurpose,
            health_check_id: ta.Optional[SystevisorHealthCheckId],
    ) -> SystevisorProcessSpawned:
        if effect.run_id in self._processes_by_run:
            raise SystevisorProcessOwnershipError(f'run is already owned: {effect.run_id}')
        prepared = _systevisor_processes_prepare(effect)
        context = _systevisor_processes_child_context(prepared)
        prepared_modifiers: ta.List[SystevisorChildModifier] = []
        try:
            for modifier in self._child_modifiers:
                prepared_modifiers.append(modifier)
                modifier.parent_prepare(context)
            _systevisor_processes_relocate_reserved_fds(prepared, self._child_modifiers, context)
            pid = os.fork()
        except BaseException:
            for modifier in reversed(prepared_modifiers):
                modifier.parent_spawn_failed(context)
            for fd in prepared.fds.all_fds():
                _systevisor_processes_close_quietly(fd)
            raise
        if pid == 0:
            _systevisor_processes_child_main(prepared, self._child_modifiers)

        _systevisor_processes_close_child_fds(prepared)
        try:
            pidfd = _systevisor_processes_pidfd_open(pid)
            birth_identity = _systevisor_processes_read_birth_identity(pid)
            process = SystevisorOwnedProcess(
                run_id=effect.run_id,
                instance_id=effect.instance_id,
                pid=pid,
                pidfd=pidfd,
                session_requested=prepared.isolate_session,
                session_id=None,
                birth_identity=birth_identity,
                status=SystevisorOwnedProcessStatus.SPAWNING,
                stdout_fd=prepared.fds.stdout_parent_fd,
                stderr_fd=prepared.fds.stderr_parent_fd,
                exec_error_fd=prepared.fds.exec_error_parent_fd,
                purpose=purpose,
                health_check_id=health_check_id,
                child_context=context,
                observe_resources=effect.spec.unit.resources.observe,
            )
            if pid in self._processes_by_pid:
                raise SystevisorProcessOwnershipError(f'pid is already owned: {pid}')
            self._processes_by_run[effect.run_id] = process
            self._processes_by_pid[pid] = process
            for modifier in prepared_modifiers:
                modifier.parent_spawned(context, pid)
            return SystevisorProcessSpawned(state=process.snapshot())
        except BaseException:
            _systevisor_processes_close_parent_fds(prepared)
            raise

    def poll_exec_result(self, run_id: SystevisorRunId) -> ta.Optional[SystevisorProcessExecResult]:
        process = self._processes_by_run.get(run_id)
        if process is None:
            raise SystevisorProcessOwnershipError(f'run is not owned: {run_id}')
        if process.exec_error_fd is None:
            return None

        reached_eof = False
        while len(process.exec_error_buffer) <= _SYSTEVISOR_PROCESSES_EXEC_ERROR_LIMIT:
            try:
                chunk = os.read(process.exec_error_fd, 4096)
            except BlockingIOError:
                break
            if not chunk:
                reached_eof = True
                break
            process.exec_error_buffer.extend(chunk)
        if not reached_eof:
            return None

        _systevisor_processes_close_quietly(process.exec_error_fd)
        process.exec_error_fd = None
        if process.exec_error_buffer:
            return SystevisorProcessExecResult(
                run_id=run_id,
                succeeded=False,
                message=process.exec_error_buffer.decode('utf-8', 'replace'),
            )
        process.status = SystevisorOwnedProcessStatus.RUNNING
        if process.session_requested:
            process.session_id = process.pid
        return SystevisorProcessExecResult(run_id=run_id, succeeded=True)

    def acquire_signal_lease(
            self,
            run_id: SystevisorRunId,
            *,
            allow_observed_exit: bool = False,
    ) -> SystevisorSignalLease:
        process = self._processes_by_run.get(run_id)
        if process is None:
            raise SystevisorProcessOwnershipError(f'run is not owned: {run_id}')
        allowed_statuses = {SystevisorOwnedProcessStatus.SPAWNING, SystevisorOwnedProcessStatus.RUNNING}
        if allow_observed_exit:
            allowed_statuses.add(SystevisorOwnedProcessStatus.EXIT_OBSERVED)
        if process.status not in allowed_statuses:
            raise SystevisorProcessOwnershipError(f'run cannot be signal-locked in state {process.status.value}')
        process.signal_lease_count += 1
        return SystevisorSignalLease(self, process, allow_observed_exit=allow_observed_exit)

    def _release_signal_lease(self, lease: SystevisorSignalLease) -> None:
        process = lease._process
        if lease._manager is not self or self._processes_by_run.get(process.run_id) is not process:
            raise SystevisorProcessOwnershipError('signal lease does not belong to this manager')
        if process.signal_lease_count < 1:
            raise SystevisorProcessOwnershipError('signal lease count underflow')
        process.signal_lease_count -= 1

    def _validate_signal_lease(self, lease: SystevisorSignalLease) -> SystevisorOwnedProcess:
        process = lease._process
        if not lease.active or lease._manager is not self:
            raise SystevisorProcessOwnershipError('signal lease is not active for this manager')
        if self._processes_by_run.get(process.run_id) is not process:
            raise SystevisorProcessOwnershipError('signal lease no longer owns its run')
        if process.signal_lease_count < 1 or process.status is SystevisorOwnedProcessStatus.REAPED:
            raise SystevisorProcessOwnershipError('signal lease does not pin a live wait right')
        if process.status is SystevisorOwnedProcessStatus.EXIT_OBSERVED and not lease._allow_observed_exit:
            raise SystevisorProcessOwnershipError('ordinary signal lease cannot target an observed exit')
        return process

    def signal(
            self,
            run_id: SystevisorRunId,
            signal_value: str,
            scope: SystevisorSignalScope,
    ) -> SystevisorSignalDelivery:
        signal_number = systevisor_parse_signal_name(signal_value)
        with self.acquire_signal_lease(run_id) as lease:
            return self.signal_with_lease(lease, signal_number, scope)

    def signal_effect(self, effect: SystevisorSignalProcessEffect) -> SystevisorSignalDelivery:
        return self.signal(effect.run_id, effect.signal, effect.scope)

    def signal_with_lease(
            self,
            lease: SystevisorSignalLease,
            signal_number: int,
            scope: SystevisorSignalScope,
    ) -> SystevisorSignalDelivery:
        process = self._validate_signal_lease(lease)
        if scope is SystevisorSignalScope.PROCESS:
            delivered = self._signal_backend.send_process(lease, signal_number)
        elif scope is SystevisorSignalScope.SESSION:
            delivered = self._signal_backend.send_session(lease, signal_number)
        else:
            raise TypeError(scope)
        return SystevisorSignalDelivery(
            run_id=process.run_id,
            signal=signal_number,
            scope=scope,
            delivered=delivered,
        )

    def poll_exits(self) -> ta.Sequence[SystevisorObservedProcessExit]:
        observed: ta.List[SystevisorObservedProcessExit] = []
        options = os.WEXITED | os.WNOHANG | os.WNOWAIT
        for process in tuple(self._processes_by_run.values()):
            if process.status is SystevisorOwnedProcessStatus.EXIT_OBSERVED:
                if not process.exit_reported and process.return_code is not None:
                    process.exit_reported = True
                    observed.append(SystevisorObservedProcessExit(
                        run_id=process.run_id,
                        instance_id=process.instance_id,
                        return_code=process.return_code,
                    ))
                continue
            if process.status is SystevisorOwnedProcessStatus.REAPED or process.signal_lease_count:
                continue
            try:
                result = os.waitid(os.P_PID, process.pid, options)
            except ChildProcessError as exc:
                raise SystevisorProcessOwnershipError(
                    f'wait ownership was lost for run {process.run_id} pid {process.pid}',
                ) from exc
            if result is None or result.si_pid == 0:
                continue
            process.return_code = _systevisor_processes_wait_result_return_code(result)
            process.status = SystevisorOwnedProcessStatus.EXIT_OBSERVED
            process.exit_reported = True
            observed.append(SystevisorObservedProcessExit(
                run_id=process.run_id,
                instance_id=process.instance_id,
                return_code=process.return_code,
            ))
        return tuple(observed)

    def poll_unknown_exits(self) -> ta.Sequence[SystevisorUnknownProcessExit]:
        if not self._reap_unknown_children:
            return ()
        reaped: ta.List[SystevisorUnknownProcessExit] = []
        options = os.WEXITED | os.WNOHANG | os.WNOWAIT
        for pid in tuple(dict.fromkeys(self._child_pid_provider.child_pids())):
            if pid in self._processes_by_pid:
                continue
            try:
                result = os.waitid(os.P_PID, pid, options)
            except ChildProcessError:
                continue
            if result is None or result.si_pid == 0:
                continue
            return_code = _systevisor_processes_wait_result_return_code(result)
            try:
                reaped_pid, wait_status = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                continue
            if reaped_pid == 0:
                continue
            if reaped_pid != pid:
                raise SystevisorProcessOwnershipError(f'unknown-child wait returned unexpected pid: {reaped_pid}')
            wait_return_code = _systevisor_processes_wait_status_return_code(wait_status)
            if wait_return_code != return_code:
                raise SystevisorProcessOwnershipError(
                    f'unknown-child wait status changed for pid {pid}: {return_code} != {wait_return_code}',
                )
            reaped.append(SystevisorUnknownProcessExit(pid=pid, return_code=return_code))
        return tuple(reaped)

    def acknowledge_exit(self, run_id: SystevisorRunId) -> SystevisorProcessRetirement:
        process = self._processes_by_run.get(run_id)
        if process is None:
            raise SystevisorProcessOwnershipError(f'run is not owned: {run_id}')
        if process.status is not SystevisorOwnedProcessStatus.EXIT_OBSERVED or process.return_code is None:
            raise SystevisorProcessOwnershipError('exit has not been observed')
        if process.signal_lease_count:
            raise SystevisorProcessOwnershipError('cannot reap a signal-locked process')

        if process.session_id is not None:
            with self.acquire_signal_lease(run_id, allow_observed_exit=True) as lease:
                self.signal_with_lease(lease, signal.SIGKILL, SystevisorSignalScope.SESSION)

        try:
            reaped_pid, wait_status = os.waitpid(process.pid, 0)
        except ChildProcessError as exc:
            raise SystevisorProcessOwnershipError(
                f'wait ownership was lost for run {run_id} pid {process.pid}',
            ) from exc
        if reaped_pid != process.pid:
            raise SystevisorProcessOwnershipError(f'wait returned unexpected pid: {reaped_pid}')
        wait_return_code = _systevisor_processes_wait_status_return_code(wait_status)
        if wait_return_code != process.return_code:
            raise SystevisorProcessOwnershipError(
                f'wait status changed for run {run_id}: {process.return_code} != {wait_return_code}',
            )

        _systevisor_processes_close_quietly(process.pidfd)
        process.pidfd = None
        _systevisor_processes_close_quietly(process.exec_error_fd)
        process.exec_error_fd = None
        process.status = SystevisorOwnedProcessStatus.REAPED
        del self._processes_by_run[run_id]
        del self._processes_by_pid[process.pid]
        if process.child_context is not None:
            for modifier in reversed(self._child_modifiers):
                modifier.parent_retired(process.child_context)
        state = process.snapshot()
        return SystevisorProcessRetirement(
            state=state,
            stdout_fd=process.stdout_fd,
            stderr_fd=process.stderr_fd,
        )


def systevisor_close_process_retirement(retirement: SystevisorProcessRetirement) -> None:
    _systevisor_processes_close_quietly(retirement.stdout_fd)
    if retirement.stderr_fd != retirement.stdout_fd:
        _systevisor_processes_close_quietly(retirement.stderr_fd)
