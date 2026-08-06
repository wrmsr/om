import abc
import json
import os
import queue
import select
import threading
import traceback
import typing as ta

from .. import dataclasses as dc
from .. import lang


##


@dc.dataclass(frozen=True, kw_only=True)
class LaunchErrorInfo:
    pid: int | None

    exception_type: str
    message: str
    traceback: str | None = None

    @classmethod
    def from_exception(cls, exc: BaseException) -> LaunchErrorInfo:
        exception_cls = type(exc)
        return cls(
            pid=os.getpid(),
            exception_type=f'{exception_cls.__module__}.{exception_cls.__qualname__}',
            message=str(exc)[:1_000],
            traceback=''.join(traceback.format_exception(exc))[-2_000:],
        )

    @classmethod
    def startup_channel_closed(cls) -> LaunchErrorInfo:
        return cls(
            pid=None,
            exception_type='omcore.daemons.startup.StartupChannelClosedError',
            message='Worker exited without reporting startup',
        )

    @classmethod
    def invalid_startup_report(cls, exc: BaseException) -> LaunchErrorInfo:
        return cls(
            pid=None,
            exception_type='omcore.daemons.startup.InvalidStartupReportError',
            message=str(exc)[:1_000],
        )


@dc.dataclass(frozen=True, kw_only=True)
class LaunchReport:
    pid: int | None
    error: LaunchErrorInfo | None = None


class LaunchError(RuntimeError):
    def __init__(self, info: LaunchErrorInfo) -> None:
        pid_part = f' in pid {info.pid}' if info.pid is not None else ''
        super().__init__(
            f'Worker startup failed{pid_part}: '
            f'{info.exception_type}: {info.message}',
        )

        self._info = info

    @property
    def info(self) -> LaunchErrorInfo:
        return self._info


##


class LaunchReporter(lang.Abstract):
    @abc.abstractmethod
    def started(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def failed(self, exc: BaseException) -> bool:
        raise NotImplementedError


class LaunchMonitor(lang.Abstract):
    @property
    @abc.abstractmethod
    def reporter(self) -> LaunchReporter:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def inherit_fds(self) -> ta.AbstractSet[int]:
        raise NotImplementedError

    @abc.abstractmethod
    def after_spawn(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, timeout_s: float) -> LaunchReport:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        raise NotImplementedError


##


class _ThreadLaunchReporter(LaunchReporter):
    def __init__(self, reports: queue.Queue[LaunchReport]) -> None:
        super().__init__()

        self._reports = reports
        self._lock = threading.Lock()
        self._reported = False

    def _report(self, report: LaunchReport) -> bool:
        with self._lock:
            if self._reported:
                return False
            self._reported = True

        self._reports.put(report)
        return True

    def started(self) -> None:
        self._report(LaunchReport(pid=os.getpid()))

    def failed(self, exc: BaseException) -> bool:
        return self._report(LaunchReport(
            pid=os.getpid(),
            error=LaunchErrorInfo.from_exception(exc),
        ))


class _ThreadLaunchMonitor(LaunchMonitor):
    def __init__(self) -> None:
        super().__init__()

        self._reports: queue.Queue[LaunchReport] = queue.Queue()
        self._reporter = _ThreadLaunchReporter(self._reports)

    @property
    def reporter(self) -> LaunchReporter:
        return self._reporter

    @property
    def inherit_fds(self) -> ta.AbstractSet[int]:
        return frozenset()

    def after_spawn(self) -> None:
        pass

    def wait(self, timeout_s: float) -> LaunchReport:
        try:
            return self._reports.get(timeout=timeout_s)
        except queue.Empty:
            raise TimeoutError('Timed out waiting for worker startup') from None

    def close(self) -> None:
        pass


##


def _report_to_json(report: LaunchReport) -> bytes:
    error: ta.Mapping[str, ta.Any] | None
    if report.error is not None:
        error = {
            'pid': report.error.pid,
            'exception_type': report.error.exception_type,
            'message': report.error.message,
            'traceback': report.error.traceback,
        }
    else:
        error = None

    return json.dumps({
        'pid': report.pid,
        'error': error,
    }, separators=(',', ':')).encode('utf-8') + b'\n'


def _report_from_json(data: bytes) -> LaunchReport:
    obj = json.loads(data.decode('utf-8'))

    error_obj = obj['error']
    error = LaunchErrorInfo(**error_obj) if error_obj is not None else None

    return LaunchReport(
        pid=obj['pid'],
        error=error,
    )


class _PipeLaunchReporter(LaunchReporter):
    def __init__(self, fd: int) -> None:
        super().__init__()

        self._fd: int | None = fd
        self._reported = False

    @property
    def pass_fd(self) -> int | None:
        return self._fd

    def close(self) -> None:
        if (fd := self._fd) is None:
            return
        self._fd = None
        os.close(fd)

    def _report(self, report: LaunchReport) -> bool:
        if self._reported:
            return False
        self._reported = True

        fd = self._fd
        self._fd = None
        if fd is None:
            return True

        try:
            data = _report_to_json(report)
            while data:
                data = data[os.write(fd, data):]
        except OSError:
            pass
        finally:
            os.close(fd)

        return True

    def started(self) -> None:
        self._report(LaunchReport(pid=os.getpid()))

    def failed(self, exc: BaseException) -> bool:
        return self._report(LaunchReport(
            pid=os.getpid(),
            error=LaunchErrorInfo.from_exception(exc),
        ))


class _PipeLaunchMonitor(LaunchMonitor):
    def __init__(self) -> None:
        super().__init__()

        self._read_fd, write_fd = os.pipe()
        self._reporter = _PipeLaunchReporter(write_fd)

    @property
    def reporter(self) -> LaunchReporter:
        return self._reporter

    @property
    def inherit_fds(self) -> ta.AbstractSet[int]:
        return frozenset([fd]) if (fd := self._reporter.pass_fd) is not None else frozenset()

    def after_spawn(self) -> None:
        self._reporter.close()

    def wait(self, timeout_s: float) -> LaunchReport:
        readable, _, _ = select.select([self._read_fd], [], [], timeout_s)
        if not readable:
            raise TimeoutError('Timed out waiting for worker startup')

        buf = bytearray()
        while not buf.endswith(b'\n'):
            chunk = os.read(self._read_fd, 4096)
            if not chunk:
                if not buf:
                    return LaunchReport(
                        pid=None,
                        error=LaunchErrorInfo.startup_channel_closed(),
                    )
                break
            buf.extend(chunk)
            if len(buf) > 64 * 1024:
                return LaunchReport(
                    pid=None,
                    error=LaunchErrorInfo.invalid_startup_report(RuntimeError('Startup report too large')),
                )

        try:
            return _report_from_json(bytes(buf))
        except Exception as exc:  # noqa
            return LaunchReport(
                pid=None,
                error=LaunchErrorInfo.invalid_startup_report(exc),
            )

    def close(self) -> None:
        self._reporter.close()

        if hasattr(self, '_read_fd'):
            os.close(self._read_fd)
            del self._read_fd


##


def launch_monitor(*, in_process: bool) -> LaunchMonitor:
    if in_process:
        return _ThreadLaunchMonitor()
    return _PipeLaunchMonitor()
