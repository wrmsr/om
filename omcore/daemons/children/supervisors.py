import queue
import threading
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..runtime import ServiceRuntime
from ..runtime import ShutdownReason
from ..runtime import ShutdownRequest
from .configs import ChildProcessConfig
from .configs import ChildTerminationConfig
from .processes import DEFAULT_CHILD_PROCESS_FACTORY
from .processes import ChildProcess
from .processes import ChildProcessFactory


##


@dc.dataclass(frozen=True, kw_only=True)
class ChildProcessResult:
    pid: int
    returncode: int
    shutdown_request: ShutdownRequest | None
    escalated: bool


class ChildSupervisorError(RuntimeError):
    pass


class ChildProcessExitedError(ChildSupervisorError):
    def __init__(self, result: ChildProcessResult) -> None:
        super().__init__(
            f'Child process {result.pid} exited unexpectedly with status {result.returncode}',
        )

        self._result = result

    @property
    def result(self) -> ChildProcessResult:
        return self._result


class ChildProcessStopTimeoutError(ChildSupervisorError, TimeoutError):
    def __init__(self, pid: int, timeout_s: float) -> None:
        super().__init__(f'Child process {pid} remained alive {timeout_s:g}s after being killed')

        self._pid = pid
        self._timeout_s = timeout_s

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def timeout_s(self) -> float:
        return self._timeout_s


##


@dc.dataclass(frozen=True, kw_only=True)
class ChildProcessSupervisorConfig:
    process: ChildProcessConfig
    termination: ChildTerminationConfig = ChildTerminationConfig()

    def __post_init__(self) -> None:
        if self.termination.signal_process_group:
            check.arg(self.process.start_new_session)


class ChildProcessSupervisor(lang.Final):
    def __init__(
            self,
            config: ChildProcessSupervisorConfig,
            *,
            process_factory: ChildProcessFactory = DEFAULT_CHILD_PROCESS_FACTORY,
    ) -> None:
        super().__init__()

        self._config = config
        self._process_factory = process_factory

    @property
    def config(self) -> ChildProcessSupervisorConfig:
        return self._config

    def _shutdown_signal(self, request: ShutdownRequest) -> int | None:
        termination = self._config.termination
        if (
                termination.forward_runtime_signal and
                request.reason is ShutdownReason.SIGNAL and
                request.signal is not None
        ):
            return request.signal
        return termination.signal

    def _terminate_on_shutdown(
            self,
            runtime: ServiceRuntime,
            process: ChildProcess,
            child_exited: threading.Event,
            escalated: threading.Event,
            outcomes: queue.Queue[tuple[str, ta.Any]],
    ) -> None:
        request = check.not_none(runtime.shutdown.wait())
        if child_exited.is_set():
            return

        termination = self._config.termination
        if (signum := self._shutdown_signal(request)) is not None:
            try:
                process.send_signal(
                    signum,
                    process_group=termination.signal_process_group,
                )
            except ProcessLookupError:
                return
            except Exception:  # noqa: BLE001, S110 - a failed graceful signal proceeds to the kill policy.
                pass

        if child_exited.wait(termination.grace_timeout_s):
            return

        escalated.set()
        try:
            process.kill(process_group=termination.signal_process_group)
        except ProcessLookupError:
            return
        except Exception as exc:  # noqa: BLE001 - factory implementations may expose arbitrary control failures.
            outcomes.put(('error', exc))
            return

        if child_exited.wait(termination.kill_timeout_s):
            return

        outcomes.put(('error', ChildProcessStopTimeoutError(
            process.pid,
            check.not_none(termination.kill_timeout_s),
        )))

    @staticmethod
    def _reap(
            runtime: ServiceRuntime,
            process: ChildProcess,
            child_exited: threading.Event,
            outcomes: queue.Queue[tuple[str, ta.Any]],
    ) -> None:
        try:
            returncode = process.wait()
            shutdown_request = runtime.shutdown.request_
        except Exception as exc:  # noqa: BLE001 - factory implementations may expose arbitrary wait failures.
            outcomes.put(('error', exc))
        else:
            child_exited.set()
            outcomes.put(('exit', (returncode, shutdown_request)))

    def run(self, runtime: ServiceRuntime) -> ChildProcessResult:
        try:
            process = self._process_factory.spawn(self._config.process)
        except Exception:  # noqa: BLE001 - factory implementations may expose arbitrary startup failures.
            runtime.shutdown.request(message='child-process-start-error')
            raise

        child_exited = threading.Event()
        escalated = threading.Event()
        outcomes: queue.Queue[tuple[str, ta.Any]] = queue.Queue()

        shutdown_thread = threading.Thread(
            target=self._terminate_on_shutdown,
            args=(runtime, process, child_exited, escalated, outcomes),
            name=f'ChildProcessShutdown-{process.pid}',
            daemon=True,
        )
        reap_thread = threading.Thread(
            target=self._reap,
            args=(runtime, process, child_exited, outcomes),
            name=f'ChildProcessReaper-{process.pid}',
            daemon=True,
        )
        shutdown_thread.start()
        reap_thread.start()

        outcome, value = outcomes.get()
        if outcome == 'error':
            runtime.shutdown.request(message=f'child-process-error:{process.pid}')
            shutdown_thread.join()
            if child_exited.is_set():
                reap_thread.join()
            raise check.isinstance(value, BaseException)

        check.equal(outcome, 'exit')
        returncode, shutdown_request = ta.cast(tuple[int, ShutdownRequest | None], value)

        if shutdown_request is None:
            runtime.shutdown.request(message=f'child-process-exited:{process.pid}:{returncode}')

        reap_thread.join()
        shutdown_thread.join()

        result = ChildProcessResult(
            pid=process.pid,
            returncode=returncode,
            shutdown_request=shutdown_request,
            escalated=escalated.is_set(),
        )
        if shutdown_request is None:
            raise ChildProcessExitedError(result)
        return result
