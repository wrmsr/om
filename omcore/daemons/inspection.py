import enum
import os
import typing as ta

from .. import check
from .. import dataclasses as dc
from .. import lang
from ..os.pidfiles.pidfile import Pidfile
from .pidfiles import DaemonPidfileInfo
from .pidfiles import DaemonPidfileInfoError
from .pidfiles import parse_daemon_pidfile_info
from .waiting import Wait
from .waiting import waiter_for


##


class DaemonLifecycleState(enum.Enum):
    ABSENT = enum.auto()
    STALE = enum.auto()
    RUNNING = enum.auto()
    READY = enum.auto()


class DaemonReadinessState(enum.Enum):
    NOT_CHECKED = enum.auto()
    NOT_READY = enum.auto()
    READY = enum.auto()
    ERROR = enum.auto()


@dc.dataclass(frozen=True, kw_only=True)
class DaemonInspection:
    pid_file: str
    state: DaemonLifecycleState

    pidfile_inode: tuple[int, int] | None = None
    pid: int | None = None
    info: DaemonPidfileInfo | None = None
    pidfile_error: str | None = None

    readiness: DaemonReadinessState = DaemonReadinessState.NOT_CHECKED
    readiness_error: str | None = None

    @property
    def exists(self) -> bool:
        return self.state is not DaemonLifecycleState.ABSENT

    @property
    def running(self) -> bool:
        return self.state in (DaemonLifecycleState.RUNNING, DaemonLifecycleState.READY)

    @property
    def ready(self) -> bool:
        return self.state is DaemonLifecycleState.READY


class DaemonInspectionRaceError(RuntimeError):
    pass


##


@dc.dataclass(frozen=True, kw_only=True)
class _PidfileObservation:
    exists: bool
    locked: bool = False
    inode: tuple[int, int] | None = None
    raw: str | None = None
    read_error: str | None = None


class _PidfileChangedError(Exception):
    pass


def _format_error(exc: BaseException) -> str:
    return f'{type(exc).__name__}: {exc}'


def _read_pidfile_fd(fd: int, max_bytes: int) -> str | None:
    before = os.fstat(fd)
    data = os.pread(fd, max_bytes + 1, 0)
    after = os.fstat(fd)

    if before.st_size != after.st_size:
        raise _PidfileChangedError
    if len(data) > max_bytes or after.st_size > max_bytes:
        raise DaemonPidfileInfoError(f'Daemon pidfile exceeds {max_bytes} bytes')
    if len(data) != after.st_size:
        raise _PidfileChangedError
    if not data:
        return None

    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise DaemonPidfileInfoError(f'Daemon pidfile is not UTF-8: {exc}') from exc


def _parse_pidfile_record(
        raw: str | None,
) -> tuple[int | None, DaemonPidfileInfo | None, str | None]:
    if raw is None:
        return None, None, None

    lines = raw.splitlines()
    if not lines:
        return None, None, None

    try:
        pid = int(lines[0].strip())
        if pid <= 0:
            raise ValueError(pid)
    except ValueError:
        return None, None, _format_error(DaemonPidfileInfoError(
            f'Invalid daemon pid line: {lines[0]!r}',
        ))

    try:
        info = parse_daemon_pidfile_info(raw)
    except DaemonPidfileInfoError as exc:
        return pid, None, _format_error(exc)

    return pid, info, None


##


class DaemonInspector(lang.Final):
    DEFAULT_MAX_PIDFILE_BYTES: ta.ClassVar[int] = 64 * 1024
    DEFAULT_MAX_PATH_RETRIES: ta.ClassVar[int] = 8

    def __init__(
            self,
            pid_file: str,
            *,
            wait: Wait | None = None,
            max_pidfile_bytes: int = DEFAULT_MAX_PIDFILE_BYTES,
            max_path_retries: int = DEFAULT_MAX_PATH_RETRIES,
    ) -> None:
        super().__init__()

        self._pid_file = check.non_empty_str(pid_file)
        self._wait = wait
        check.arg(max_pidfile_bytes > 0)
        self._max_pidfile_bytes = max_pidfile_bytes
        check.arg(max_path_retries > 0)
        self._max_path_retries = max_path_retries

    @property
    def pid_file(self) -> str:
        return self._pid_file

    @property
    def wait(self) -> Wait | None:
        return self._wait

    def _observe_pidfile(self) -> _PidfileObservation:
        for _ in range(self._max_path_retries):
            try:
                pidfile_context = Pidfile(
                    self._pid_file,
                    inheritable=False,
                    no_create=True,
                )
                with pidfile_context as pidfile:
                    fd = check.not_none(pidfile.fileno())
                    fd_stat = os.fstat(fd)
                    inode = (fd_stat.st_dev, fd_stat.st_ino)
                    locked = not pidfile.try_acquire_lock()

                    try:
                        raw = _read_pidfile_fd(fd, self._max_pidfile_bytes)
                        read_error = None
                    except _PidfileChangedError:
                        continue
                    except DaemonPidfileInfoError as exc:
                        raw = None
                        read_error = _format_error(exc)

                    try:
                        path_stat = os.stat(self._pid_file)
                    except FileNotFoundError:
                        continue
                    if inode != (path_stat.st_dev, path_stat.st_ino):
                        continue

                    return _PidfileObservation(
                        exists=True,
                        locked=locked,
                        inode=inode,
                        raw=raw,
                        read_error=read_error,
                    )

            except FileNotFoundError:
                return _PidfileObservation(exists=False)

        raise DaemonInspectionRaceError(
            f'Daemon pidfile path changed repeatedly during inspection: {self._pid_file!r}',
        )

    def inspect(self) -> DaemonInspection:
        observation = self._observe_pidfile()
        if not observation.exists:
            return DaemonInspection(
                pid_file=self._pid_file,
                state=DaemonLifecycleState.ABSENT,
            )

        pid, info, pidfile_error = _parse_pidfile_record(observation.raw)
        if observation.read_error is not None:
            pidfile_error = observation.read_error

        if not observation.locked:
            return DaemonInspection(
                pid_file=self._pid_file,
                state=DaemonLifecycleState.STALE,
                pidfile_inode=observation.inode,
                pid=pid,
                info=info,
                pidfile_error=pidfile_error,
            )

        readiness = DaemonReadinessState.NOT_CHECKED
        readiness_error = None
        state = DaemonLifecycleState.RUNNING
        if self._wait is not None:
            try:
                ready = check.isinstance(waiter_for(self._wait).do_wait(), bool)
            except Exception as exc:  # noqa: BLE001 - waiter implementations define their own failure types.
                readiness = DaemonReadinessState.ERROR
                readiness_error = _format_error(exc)
            else:
                if ready:
                    readiness = DaemonReadinessState.READY
                    state = DaemonLifecycleState.READY
                else:
                    readiness = DaemonReadinessState.NOT_READY

        return DaemonInspection(
            pid_file=self._pid_file,
            state=state,
            pidfile_inode=observation.inode,
            pid=pid,
            info=info,
            pidfile_error=pidfile_error,
            readiness=readiness,
            readiness_error=readiness_error,
        )
