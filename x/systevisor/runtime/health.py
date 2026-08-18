# ruff: noqa: UP006 UP007 UP037 UP045
import abc
import dataclasses as dc
import errno
import socket
import typing as ta
import urllib.parse

from omcore.http.pipelines.clients.requests import IoPipelineHttpRequestEncoder
from omcore.http.pipelines.clients.responses import IoPipelineHttpClientResponseDecoder
from omcore.http.pipelines.requests import FullIoPipelineHttpRequest
from omcore.http.pipelines.responses import IoPipelineHttpResponseAborted
from omcore.http.pipelines.responses import IoPipelineHttpResponseEnd
from omcore.http.pipelines.responses import IoPipelineHttpResponseHead
from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorHealthProbeKind
from ..configs.models import SystevisorSignalScope
from ..core.effects import SystevisorRunHealthProbeEffect
from ..core.identities import SystevisorHealthCheckId
from ..core.identities import SystevisorRunId
from ..core.inputs import SystevisorHealthProbeResultFact
from .clocks import SystevisorClock
from .logs import SystevisorLogManager
from .logs import SystevisorLogStream
from .processes import SystevisorObservedProcessExit
from .processes import SystevisorOwnedProcessStatus
from .processes import SystevisorProcessExecResult
from .processes import SystevisorProcessManager
from .processes import SystevisorProcessOwnershipError
from .processes import SystevisorProcessSpawnError


@dc.dataclass(frozen=True)
class SystevisorHealthProbeRuntimeStart:
    command_run_id: ta.Optional[SystevisorRunId] = None


class SystevisorHealthProbeRunner(Abstract):
    @abc.abstractmethod
    def start(
            self,
            effect: SystevisorRunHealthProbeEffect,
            callback: ta.Callable[[SystevisorHealthProbeResultFact], None],
    ) -> SystevisorHealthProbeRuntimeStart:
        raise NotImplementedError

    @abc.abstractmethod
    def owns_command_run(self, run_id: SystevisorRunId) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def command_exec_result(self, result: SystevisorProcessExecResult) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def command_exit(self, observed: SystevisorObservedProcessExit) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        raise NotImplementedError


@dc.dataclass
class SystevisorHealthRuntimeCheck:
    effect: SystevisorRunHealthProbeEffect
    callback: ta.Callable[[SystevisorHealthProbeResultFact], None]
    deadline_at: float
    handler: ta.Optional[FdioHandler] = None
    command_run_id: ta.Optional[SystevisorRunId] = None
    finished: bool = False


class SystevisorHealthConnectFdioHandler(FdioHandler):
    def __init__(
            self,
            sock: socket.socket,
            callback: ta.Callable[[ta.Optional[socket.socket], ta.Optional[str]], None],
    ) -> None:
        self._sock: ta.Optional[socket.socket] = sock
        self._callback = callback

    def fd(self) -> int:
        if self._sock is None:
            return -1
        return self._sock.fileno()

    @property
    def closed(self) -> bool:
        return self._sock is None

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def writable(self) -> bool:
        return self._sock is not None

    def on_writable(self) -> None:
        sock = self._sock
        if sock is None:
            return
        error_number = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if error_number:
            self.close()
            self._callback(None, _systevisor_health_os_error_message(error_number))
            return
        self._sock = None
        self._callback(sock, None)

    def on_error(self, exc: ta.Optional[BaseException] = None) -> None:
        self.close()
        self._callback(None, str(exc) if exc is not None else 'socket connection failed')


def _systevisor_health_os_error_message(error_number: int) -> str:
    return f'[Errno {error_number}] {errno.errorcode.get(error_number, "socket error")}'


@dc.dataclass(frozen=True)
class SystevisorHttpHealthResult:
    success: bool
    message: str
    status: ta.Optional[int] = None


class SystevisorHttpHealthIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            request: FullIoPipelineHttpRequest,
            expected_statuses: ta.Container[int],
    ) -> None:
        super().__init__()
        self._request = request
        self._expected_statuses = expected_statuses
        self._status: ta.Optional[int] = None
        self.result: ta.Optional[SystevisorHttpHealthResult] = None

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._request)
            return
        if isinstance(msg, IoPipelineHttpResponseHead):
            self._status = msg.status
            return
        if isinstance(msg, IoPipelineHttpResponseEnd):
            if self._status is None:
                self.result = SystevisorHttpHealthResult(False, 'response ended without a status')
            else:
                self.result = SystevisorHttpHealthResult(
                    self._status in self._expected_statuses,
                    f'HTTP status {self._status}',
                    self._status,
                )
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineHttpResponseAborted):
            self.result = SystevisorHttpHealthResult(False, 'HTTP response aborted')
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.result = SystevisorHttpHealthResult(False, 'connection closed before HTTP response completed')
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.Error):
            self.result = SystevisorHttpHealthResult(False, str(msg.exc))
            ctx.feed_final_output()
            return
        ctx.feed_in(msg)


class SystevisorHttpHealthFdioHandler(IoPipelineDriverSocketFdioHandler):
    def __init__(
            self,
            sock: socket.socket,
            addr: ta.Any,
            response_handler: SystevisorHttpHealthIoPipelineHandler,
            callback: ta.Callable[[SystevisorHttpHealthResult], None],
    ) -> None:
        self._systevisor_response_handler = response_handler
        self._systevisor_callback = callback
        self._systevisor_reported = False
        super().__init__(sock, addr, IoPipeline.Spec([
            IoPipelineHttpRequestEncoder(),
            IoPipelineHttpClientResponseDecoder(),
            response_handler,
        ]))

    def _systevisor_after_io(self) -> None:
        result = self._systevisor_response_handler.result
        if result is not None and not self._systevisor_reported:
            self._systevisor_reported = True
            self._systevisor_callback(result)

    def _systevisor_io(self, method: ta.Callable[[], None]) -> None:
        try:
            method()
        except BaseException as exc:  # noqa: BLE001
            if not self._systevisor_reported:
                self._systevisor_reported = True
                self._systevisor_callback(SystevisorHttpHealthResult(False, str(exc)))
        finally:
            self._systevisor_after_io()

    def on_readable(self) -> None:
        self._systevisor_io(super().on_readable)

    def on_writable(self) -> None:
        self._systevisor_io(super().on_writable)

    def on_timeout(self) -> None:
        self._systevisor_io(super().on_timeout)


class SystevisorFdioHealthProbeRunner(SystevisorHealthProbeRunner, FdioHandler):
    def __init__(
            self,
            process_manager: SystevisorProcessManager,
            fdio_manager: FdioManager,
            clock: SystevisorClock,
            log_manager: SystevisorLogManager,
    ) -> None:
        self._process_manager = process_manager
        self._fdio_manager = fdio_manager
        self._clock = clock
        self._log_manager = log_manager
        self._checks: ta.Dict[SystevisorHealthCheckId, SystevisorHealthRuntimeCheck] = {}
        self._command_checks: ta.Dict[SystevisorRunId, SystevisorHealthRuntimeCheck] = {}
        self._closed = False
        fdio_manager.register(self)

    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        for check in tuple(self._checks.values()):
            if check.handler is not None:
                check.handler.close()
            if check.command_run_id is not None:
                try:
                    self._signal_command(check.command_run_id)
                except SystevisorProcessOwnershipError:
                    pass
        self._checks.clear()
        self._closed = True

    def next_deadline(self) -> ta.Optional[float]:
        if not self._checks:
            return None
        return min(check.deadline_at for check in self._checks.values())

    def on_timeout(self) -> None:
        now = self._clock.monotonic()
        for check in tuple(self._checks.values()):
            if check.deadline_at > now:
                continue
            if check.command_run_id is not None:
                try:
                    self._signal_command(check.command_run_id)
                except SystevisorProcessOwnershipError:
                    pass
            self._finish(check, False, f'probe timed out after {check.effect.probe.timeout_secs:g}s')

    def start(
            self,
            effect: SystevisorRunHealthProbeEffect,
            callback: ta.Callable[[SystevisorHealthProbeResultFact], None],
    ) -> SystevisorHealthProbeRuntimeStart:
        if self._closed:
            raise RuntimeError('health probe runner is closed')
        if effect.check_id in self._checks:
            raise RuntimeError(f'health check is already active: {effect.check_id}')
        check = SystevisorHealthRuntimeCheck(
            effect=effect,
            callback=callback,
            deadline_at=self._clock.monotonic() + effect.probe.timeout_secs,
        )
        self._checks[effect.check_id] = check

        kind = effect.probe.kind
        if kind is SystevisorHealthProbeKind.PROCESS:
            state = self._process_manager.get_state(effect.run_id)
            success = state is not None and state.status is SystevisorOwnedProcessStatus.RUNNING
            self._finish(check, success, 'owned process is running' if success else 'owned process is not running')
        elif kind is SystevisorHealthProbeKind.LOG_ACTIVITY:
            self._start_log_activity(check)
        elif kind is SystevisorHealthProbeKind.TCP:
            self._start_connect(check, http=False)
        elif kind is SystevisorHealthProbeKind.HTTP:
            self._start_connect(check, http=True)
        elif kind is SystevisorHealthProbeKind.COMMAND:
            self._start_command(check)
        else:
            raise TypeError(kind)
        return SystevisorHealthProbeRuntimeStart(command_run_id=check.command_run_id)

    def owns_command_run(self, run_id: SystevisorRunId) -> bool:
        return run_id in self._command_checks

    def command_exec_result(self, result: SystevisorProcessExecResult) -> None:
        check = self._command_checks[result.run_id]
        if not result.succeeded:
            self._finish(check, False, result.message or 'health command exec failed')

    def command_exit(self, observed: SystevisorObservedProcessExit) -> None:
        check = self._command_checks.pop(observed.run_id)
        if not check.finished:
            self._finish(
                check,
                observed.return_code == 0,
                f'health command exited with status {observed.return_code}',
                {'return_code': observed.return_code},
            )

    def _start_log_activity(self, check: SystevisorHealthRuntimeCheck) -> None:
        probe = check.effect.probe
        if probe.channel is None or probe.max_quiet_secs is None:
            self._finish(check, False, 'log activity probe is missing its channel policy')
            return
        stream = SystevisorLogStream(probe.channel)
        last_activity_at = self._log_manager.last_activity_at(check.effect.run_id, stream)
        if last_activity_at is None:
            self._finish(check, False, f'{stream.value} is not captured')
            return
        quiet_secs = max(0., self._clock.monotonic() - last_activity_at)
        self._finish(
            check,
            quiet_secs <= probe.max_quiet_secs,
            f'{stream.value} quiet for {quiet_secs:g}s',
            {'quiet_secs': quiet_secs, 'last_activity_at': last_activity_at},
        )

    def _start_connect(self, check: SystevisorHealthRuntimeCheck, *, http: bool) -> None:
        probe = check.effect.probe
        host: ta.Optional[str]
        port: ta.Optional[int]
        if http:
            parsed = urllib.parse.urlsplit(probe.url or '')
            host = parsed.hostname
            port = parsed.port or 80
        else:
            parsed = None
            host = probe.host
            port = probe.port
        if host is None or port is None:
            self._finish(check, False, 'probe address is incomplete')
            return
        try:
            family, socket_type, protocol, _, address = socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
            )[0]
            sock = socket.socket(family, socket_type, protocol)
            sock.setblocking(False)
            result = sock.connect_ex(address)
        except OSError as exc:
            self._finish(check, False, str(exc))
            return

        def connected(
                connected_socket: ta.Optional[socket.socket],
                message: ta.Optional[str],
        ) -> None:
            if connected_socket is None:
                self._finish(check, False, message or 'connection failed')
            elif http:
                self._start_http(check, connected_socket, address, parsed)
            else:
                connected_socket.close()
                self._finish(check, True, f'connected to {host}:{port}')

        if result == 0:
            connected(sock, None)
        elif result in {errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY, errno.EINTR}:
            handler = SystevisorHealthConnectFdioHandler(sock, connected)
            check.handler = handler
            self._fdio_manager.register(handler)
        else:
            sock.close()
            self._finish(check, False, _systevisor_health_os_error_message(result))

    def _start_http(
            self,
            check: SystevisorHealthRuntimeCheck,
            sock: socket.socket,
            address: ta.Any,
            parsed: ta.Any,
    ) -> None:
        probe = check.effect.probe
        target = urllib.parse.urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
        host_header = parsed.hostname or ''
        if parsed.port is not None:
            host_header = f'{host_header}:{parsed.port}'
        request = FullIoPipelineHttpRequest.simple(
            host_header,
            target,
            method=probe.method,
            connection='close',
        )
        response_handler = SystevisorHttpHealthIoPipelineHandler(request, frozenset(probe.expected_statuses))

        def completed(result: SystevisorHttpHealthResult) -> None:
            self._finish(
                check,
                result.success,
                result.message,
                {'status': result.status} if result.status is not None else {},
            )

        handler = SystevisorHttpHealthFdioHandler(sock, address, response_handler, completed)
        check.handler = handler
        try:
            if handler.next(read=False) is not None:
                raise RuntimeError('unexpected HTTP health pipeline output')
        except BaseException as exc:  # noqa: BLE001
            handler.close()
            self._finish(check, False, str(exc))
            return
        if not handler.closed:
            self._fdio_manager.register(handler)

    def _start_command(self, check: SystevisorHealthRuntimeCheck) -> None:
        try:
            run_id, _ = self._process_manager.spawn_health_command(check.effect)
        except (SystevisorProcessSpawnError, OSError) as exc:
            self._finish(check, False, str(exc))
            return
        check.command_run_id = run_id
        self._command_checks[run_id] = check

    def _signal_command(self, run_id: SystevisorRunId) -> None:
        state = self._process_manager.get_state(run_id)
        if state is None:
            raise SystevisorProcessOwnershipError(f'health command is not owned: {run_id}')
        scope = (
            SystevisorSignalScope.SESSION
            if state.session_id == state.pid else
            SystevisorSignalScope.PROCESS
        )
        self._process_manager.signal(run_id, 'KILL', scope)

    def _finish(
            self,
            check: SystevisorHealthRuntimeCheck,
            success: bool,
            message: str,
            data: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        if check.finished:
            return
        check.finished = True
        self._checks.pop(check.effect.check_id, None)
        if check.handler is not None:
            check.handler.close()
            check.handler = None
        check.callback(SystevisorHealthProbeResultFact(
            check_id=check.effect.check_id,
            run_id=check.effect.run_id,
            success=success,
            message=message,
            data=dict(data or {}),
        ))
