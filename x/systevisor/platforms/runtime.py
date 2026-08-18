# ruff: noqa: UP006 UP007 UP037 UP045
import abc
import ctypes
import dataclasses as dc
import fcntl
import grp
import logging
import logging.handlers
import os
import os.path
import pwd
import resource
import socket
import sys
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.logs.std.filters import TidLoggingFilter
from omcore.logs.std.standard import STANDARD_LOG_FORMAT_PARTS
from omcore.logs.std.standard import StandardLoggingFormatter
from omcore.os.journald import JournaldLoggingHandler
from omcore.os.setproctitle import setproctitle

from ..configs.models import SystevisorManagerConfig
from ..configs.models import SystevisorManagerLogConfig
from ..configs.models import SystevisorObservationConfig
from ..configs.models import SystevisorSelfUpdateConfig


_SYSTEVISOR_PLATFORM_PR_SET_CHILD_SUBREAPER = 36


class SystevisorPlatformError(Exception):
    pass


@dc.dataclass(frozen=True)
class SystevisorProcessBootstrapState:
    pid: int
    is_pid_one: bool
    subreaper_enabled: bool
    systemd_notify: bool
    launchd_job: bool


@dc.dataclass(frozen=True)
class SystevisorPidFileState:
    path: str
    pid: int
    device: int
    inode: int


class SystevisorProcessBootstrap(Abstract):
    @abc.abstractmethod
    def bootstrap(self, config: SystevisorManagerConfig) -> SystevisorProcessBootstrapState:
        raise NotImplementedError


def _systevisor_platform_raise_resource_limit(resource_id: int, minimum: int, name: str) -> None:
    if minimum <= 0:
        return
    soft, hard = resource.getrlimit(resource_id)
    if soft == resource.RLIM_INFINITY or soft >= minimum:
        return
    if hard != resource.RLIM_INFINITY and hard < minimum:
        raise SystevisorPlatformError(
            f'{name} hard limit {hard} is below configured minimum {minimum}',
        )
    try:
        resource.setrlimit(resource_id, (minimum, hard))
    except (OSError, ValueError) as exc:
        raise SystevisorPlatformError(f'could not raise {name} soft limit to {minimum}: {exc}') from exc


def _systevisor_platform_enable_subreaper() -> bool:
    if not sys.platform.startswith('linux'):
        return False
    if os.getpid() == 1:
        return True
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = getattr(libc, 'prctl', None)
    if prctl is None:
        raise SystevisorPlatformError('libc does not expose prctl for child-subreaper setup')
    prctl.argtypes = [
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    ]
    prctl.restype = ctypes.c_int
    if prctl(_SYSTEVISOR_PLATFORM_PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        error_number = ctypes.get_errno()
        raise SystevisorPlatformError(
            f'could not enable child subreaper: {os.strerror(error_number)}',
        )
    return True


def _systevisor_platform_daemonize() -> None:
    first_pid = os.fork()
    if first_pid != 0:
        os._exit(0)
    os.setsid()
    second_pid = os.fork()
    if second_pid != 0:
        os._exit(0)

    null_read_fd = os.open(os.devnull, os.O_RDONLY)
    null_write_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null_read_fd, 0)
        os.dup2(null_write_fd, 1)
        os.dup2(null_write_fd, 2)
    finally:
        if null_read_fd > 2:
            os.close(null_read_fd)
        if null_write_fd > 2:
            os.close(null_write_fd)


def _systevisor_platform_drop_manager_identity(config: SystevisorManagerConfig) -> None:
    passwd_entry: ta.Any = None
    if config.user is not None:
        try:
            passwd_entry = pwd.getpwnam(config.user)
        except KeyError as exc:
            raise SystevisorPlatformError(f'unknown manager user: {config.user!r}') from exc

    if config.group is not None:
        try:
            gid: ta.Optional[int] = grp.getgrnam(config.group).gr_gid
        except KeyError as exc:
            raise SystevisorPlatformError(f'unknown manager group: {config.group!r}') from exc
    else:
        gid = passwd_entry.pw_gid if passwd_entry is not None else None
    uid = passwd_entry.pw_uid if passwd_entry is not None else None

    effective_uid = os.geteuid()
    if effective_uid != 0:
        if uid is not None and uid != effective_uid:
            raise SystevisorPlatformError(f'cannot switch manager uid from {effective_uid} to {uid}')
        if gid is not None and gid != os.getegid():
            raise SystevisorPlatformError(f'cannot switch manager gid from {os.getegid()} to {gid}')
        return

    if passwd_entry is not None:
        os.initgroups(passwd_entry.pw_name, ta.cast(int, gid))
    if gid is not None:
        os.setgid(gid)
    if uid is not None:
        os.setuid(uid)


class SystevisorPosixProcessBootstrap(SystevisorProcessBootstrap):
    def bootstrap(self, config: SystevisorManagerConfig) -> SystevisorProcessBootstrapState:
        if not config.foreground:
            _systevisor_platform_daemonize()

        if config.working_directory is not None:
            try:
                os.chdir(config.working_directory)
            except OSError as exc:
                raise SystevisorPlatformError(
                    f'could not change manager working directory to {config.working_directory!r}: {exc}',
                ) from exc
        os.umask(config.umask)

        if hasattr(resource, 'RLIMIT_NOFILE'):
            _systevisor_platform_raise_resource_limit(resource.RLIMIT_NOFILE, config.min_fds, 'RLIMIT_NOFILE')
        if hasattr(resource, 'RLIMIT_NPROC'):
            _systevisor_platform_raise_resource_limit(resource.RLIMIT_NPROC, config.min_procs, 'RLIMIT_NPROC')

        subreaper_enabled = config.subreaper and _systevisor_platform_enable_subreaper()
        _systevisor_platform_drop_manager_identity(config)
        if config.process_title is not None:
            setproctitle(config.process_title)

        return SystevisorProcessBootstrapState(
            pid=os.getpid(),
            is_pid_one=os.getpid() == 1,
            subreaper_enabled=subreaper_enabled,
            systemd_notify=bool(os.environ.get('NOTIFY_SOCKET')),
            launchd_job=bool(os.environ.get('LAUNCH_JOBKEY_LABEL')),
        )


class SystevisorPidFileManager:
    def __init__(self) -> None:
        self._fd: ta.Optional[int] = None
        self._state: ta.Optional[SystevisorPidFileState] = None

    @property
    def state(self) -> ta.Optional[SystevisorPidFileState]:
        return self._state

    @property
    def fd(self) -> ta.Optional[int]:
        return self._fd

    def acquire(self, path: str) -> SystevisorPidFileState:
        if self._fd is not None:
            raise SystevisorPlatformError('pidfile is already acquired')
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SystevisorPlatformError(f'pidfile is locked by another process: {path!r}') from exc
            stat_result = os.fstat(fd)
            os.ftruncate(fd, 0)
            data = f'{os.getpid()}\n'.encode('ascii')
            offset = 0
            while offset < len(data):
                offset += os.write(fd, data[offset:])
            os.fsync(fd)
            state = SystevisorPidFileState(
                path=os.path.abspath(path),
                pid=os.getpid(),
                device=stat_result.st_dev,
                inode=stat_result.st_ino,
            )
        except BaseException:
            os.close(fd)
            raise
        self._fd = fd
        self._state = state
        return state

    def rehydrate(self, state: SystevisorPidFileState, fd: int) -> None:
        if self._fd is not None or self._state is not None:
            raise SystevisorPlatformError('pidfile manager can only be rehydrated before use')
        if state.pid != os.getpid():
            raise SystevisorPlatformError(
                f'pidfile handoff belongs to pid {state.pid}, not current pid {os.getpid()}',
            )
        try:
            fd_stat = os.fstat(fd)
            path_stat = os.stat(state.path)
        except OSError as exc:
            raise SystevisorPlatformError(f'could not validate inherited pidfile: {exc}') from exc
        expected_identity = (state.device, state.inode)
        if (
                (fd_stat.st_dev, fd_stat.st_ino) != expected_identity or
                (path_stat.st_dev, path_stat.st_ino) != expected_identity
        ):
            raise SystevisorPlatformError('inherited pidfile identity changed')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SystevisorPlatformError('inherited pidfile lock was lost') from exc
        flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
        self._fd = fd
        self._state = state

    def close(self) -> None:
        fd = self._fd
        state = self._state
        if fd is None or state is None:
            return
        try:
            try:
                current = os.stat(state.path)
            except FileNotFoundError:
                current = None
            if current is not None and (current.st_dev, current.st_ino) == (state.device, state.inode):
                os.unlink(state.path)
        finally:
            os.close(fd)
            self._fd = None
            self._state = None


class SystevisorPreparedManagerLogging:
    def __init__(
            self,
            owner: 'SystevisorManagerLogging',
            config: SystevisorManagerLogConfig,
            handlers: ta.Sequence[logging.Handler],
    ) -> None:
        self._owner = owner
        self._config = config
        self._handlers = tuple(handlers)
        self._finished = False

    def commit(self) -> None:
        if self._finished:
            raise SystevisorPlatformError('manager logging change is already finished')
        self._owner._commit(self._config, self._handlers)  # noqa: SLF001
        self._finished = True

    def rollback(self) -> None:
        if self._finished:
            return
        for handler in self._handlers:
            handler.close()
        self._finished = True


class SystevisorManagerLogging:
    def __init__(self, target: ta.Optional[logging.Logger] = None) -> None:
        self._target = target if target is not None else logging.getLogger()
        self._handlers: ta.Sequence[logging.Handler] = ()
        self._config: ta.Optional[SystevisorManagerLogConfig] = None
        self._previous_level: ta.Optional[int] = None

    @property
    def config(self) -> ta.Optional[SystevisorManagerLogConfig]:
        return self._config

    def prepare(self, config: SystevisorManagerLogConfig) -> SystevisorPreparedManagerLogging:
        formatter = StandardLoggingFormatter(StandardLoggingFormatter.build_log_format(STANDARD_LOG_FORMAT_PARTS))
        handlers: ta.List[logging.Handler] = []
        try:
            if config.stderr:
                handlers.append(logging.StreamHandler())
            if config.file is not None:
                handlers.append(logging.handlers.RotatingFileHandler(
                    config.file,
                    maxBytes=config.max_bytes,
                    backupCount=config.backups,
                ))
            if config.journald:
                handlers.append(JournaldLoggingHandler())
            for handler in handlers:
                handler.setFormatter(formatter)
                handler.addFilter(TidLoggingFilter())
        except BaseException:
            for handler in handlers:
                handler.close()
            raise
        return SystevisorPreparedManagerLogging(self, config, handlers)

    def configure(self, config: SystevisorManagerLogConfig) -> None:
        self.prepare(config).commit()

    def _commit(
            self,
            config: SystevisorManagerLogConfig,
            handlers: ta.Sequence[logging.Handler],
    ) -> None:
        old_handlers = self._handlers
        if self._previous_level is None:
            self._previous_level = self._target.level
        for handler in handlers:
            self._target.addHandler(handler)
        self._target.setLevel(config.level.upper())
        self._handlers = tuple(handlers)
        self._config = config
        for handler in old_handlers:
            self._target.removeHandler(handler)
            handler.close()

    def close(self) -> None:
        for handler in self._handlers:
            self._target.removeHandler(handler)
            handler.close()
        self._handlers = ()
        self._config = None
        if self._previous_level is not None:
            self._target.setLevel(self._previous_level)
            self._previous_level = None


class SystevisorServiceNotifier(Abstract):
    @abc.abstractmethod
    def notify(self, message: str) -> bool:
        raise NotImplementedError


class SystevisorSystemdServiceNotifier(SystevisorServiceNotifier):
    def __init__(self, notify_socket: ta.Optional[str] = None) -> None:
        self._notify_socket = notify_socket if notify_socket is not None else os.environ.get('NOTIFY_SOCKET')

    def notify(self, message: str) -> bool:
        if self._notify_socket is None:
            return False
        address = self._notify_socket
        if address.startswith('@'):
            address = '\x00' + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notifier_socket:
            notifier_socket.connect(address)
            notifier_socket.sendall(message.encode('utf-8'))
        return True


@dc.dataclass(frozen=True)
class SystevisorManagerRuntimeState:
    bootstrap: SystevisorProcessBootstrapState
    config: SystevisorManagerConfig
    pid_file: ta.Optional[SystevisorPidFileState]
    ready: bool = False
    stopping: bool = False


class SystevisorPreparedManagerRuntimeChange:
    def __init__(
            self,
            owner: 'SystevisorManagerRuntime',
            config: SystevisorManagerConfig,
            logging_change: ta.Optional[SystevisorPreparedManagerLogging],
    ) -> None:
        self._owner = owner
        self._config = config
        self._logging_change = logging_change
        self._finished = False

    def commit(self) -> None:
        if self._finished:
            raise SystevisorPlatformError('manager runtime change is already finished')
        if self._logging_change is not None:
            self._logging_change.commit()
        self._owner._commit_config(self._config)  # noqa: SLF001
        self._finished = True

    def rollback(self) -> None:
        if self._finished:
            return
        if self._logging_change is not None:
            self._logging_change.rollback()
        self._finished = True


class SystevisorManagerRuntime:
    def __init__(
            self,
            bootstrap: SystevisorProcessBootstrap,
            logging_manager: SystevisorManagerLogging,
            pid_file_manager: SystevisorPidFileManager,
            notifier: SystevisorServiceNotifier,
    ) -> None:
        self._bootstrap = bootstrap
        self._logging_manager = logging_manager
        self._pid_file_manager = pid_file_manager
        self._notifier = notifier
        self._state: ta.Optional[SystevisorManagerRuntimeState] = None

    @property
    def state(self) -> ta.Optional[SystevisorManagerRuntimeState]:
        return self._state

    @property
    def pid_file_fd(self) -> ta.Optional[int]:
        return self._pid_file_manager.fd

    def setup(self, config: SystevisorManagerConfig) -> SystevisorManagerRuntimeState:
        if self._state is not None:
            raise SystevisorPlatformError('manager runtime is already set up')
        bootstrap_state = self._bootstrap.bootstrap(config)
        self._logging_manager.configure(config.log)
        try:
            pid_file = self._pid_file_manager.acquire(config.pid_file) if config.pid_file is not None else None
        except BaseException:
            self._logging_manager.close()
            raise
        self._state = SystevisorManagerRuntimeState(
            bootstrap=bootstrap_state,
            config=config,
            pid_file=pid_file,
        )
        self._notifier.notify(f'STATUS={config.identifier} is starting')
        return self._state

    def rehydrate(
            self,
            state: SystevisorManagerRuntimeState,
            pid_file_fd: ta.Optional[int],
    ) -> SystevisorManagerRuntimeState:
        if self._state is not None:
            raise SystevisorPlatformError('manager runtime can only be rehydrated before setup')
        if state.bootstrap.pid != os.getpid() or state.bootstrap.is_pid_one != (os.getpid() == 1):
            raise SystevisorPlatformError('manager bootstrap identity changed across exec')
        if (state.pid_file is None) != (pid_file_fd is None):
            raise SystevisorPlatformError('pidfile state and descriptor do not match')
        self._logging_manager.configure(state.config.log)
        try:
            if state.pid_file is not None:
                self._pid_file_manager.rehydrate(state.pid_file, ta.cast(int, pid_file_fd))
        except BaseException:
            self._logging_manager.close()
            raise
        if state.config.process_title is not None:
            setproctitle(state.config.process_title)
        self._state = dc.replace(state, ready=False, stopping=False)
        self._notifier.notify(f'STATUS={state.config.identifier} resumed after self-update')
        return self._state

    @staticmethod
    def _immutable_config(config: SystevisorManagerConfig) -> SystevisorManagerConfig:
        return dc.replace(
            config,
            log=SystevisorManagerLogConfig(),
            observation=SystevisorObservationConfig(),
            self_update=SystevisorSelfUpdateConfig(),
            process_title=None,
            strip_ansi=False,
        )

    def prepare(self, config: SystevisorManagerConfig) -> SystevisorPreparedManagerRuntimeChange:
        state = self._state
        if state is None:
            raise SystevisorPlatformError('manager runtime is not set up')
        if self._immutable_config(config) != self._immutable_config(state.config):
            raise SystevisorPlatformError('manager bootstrap fields cannot change during live reload')
        if config.process_title is not None and '\x00' in config.process_title:
            raise SystevisorPlatformError('manager process title may not contain NUL')
        logging_change = self._logging_manager.prepare(config.log) if config.log != state.config.log else None
        return SystevisorPreparedManagerRuntimeChange(self, config, logging_change)

    def _commit_config(self, config: SystevisorManagerConfig) -> None:
        state = self._state
        if state is None:
            raise SystevisorPlatformError('manager runtime is not set up')
        if config.process_title != state.config.process_title and config.process_title is not None:
            setproctitle(config.process_title)
        self._state = dc.replace(state, config=config)
        self._notifier.notify(f'STATUS={config.identifier} configuration applied')

    def ready(self) -> None:
        state = self._state
        if state is None:
            raise SystevisorPlatformError('manager runtime is not set up')
        if state.ready:
            return
        self._notifier.notify(f'READY=1\nSTATUS={state.config.identifier} is ready\nMAINPID={state.bootstrap.pid}')
        self._state = dc.replace(state, ready=True)

    def stopping(self) -> None:
        state = self._state
        if state is None or state.stopping:
            return
        self._notifier.notify(f'STOPPING=1\nSTATUS={state.config.identifier} is stopping')
        self._state = dc.replace(state, stopping=True)

    def close(self) -> None:
        self.stopping()
        self._pid_file_manager.close()
        self._logging_manager.close()
        self._state = None
