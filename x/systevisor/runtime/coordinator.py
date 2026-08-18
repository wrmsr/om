# ruff: noqa: UP006 UP007 UP045
import collections
import signal
import typing as ta

from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.logs.modules import get_module_logger

from ..core.effects import SystevisorApplyLiveConfigEffect
from ..core.effects import SystevisorEngineEffect
from ..core.effects import SystevisorRunHealthProbeEffect
from ..core.effects import SystevisorScheduleDeadlineEffect
from ..core.effects import SystevisorSignalProcessEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.engine import SystevisorEngine
from ..core.events import SystevisorEngineOutput
from ..core.identities import SystevisorRunId
from ..core.inputs import SystevisorApplySnapshotCommand
from ..core.inputs import SystevisorEngineInput
from ..core.inputs import SystevisorHealthProbeResultFact
from ..core.inputs import SystevisorProcessExitedFact
from ..core.inputs import SystevisorShutdownCommand
from ..core.inputs import SystevisorSpawnFailedFact
from ..core.inputs import SystevisorSpawnSucceededFact
from .clocks import SystevisorClock
from .events import SystevisorEventBus
from .fdio import SystevisorDeadlineFdioHandler
from .fdio import SystevisorProcessExecFdioHandler
from .fdio import SystevisorProcessPidfdFdioHandler
from .fdio import SystevisorProcessWaitFdioHandler
from .health import SystevisorHealthProbeRunner
from .logs import SystevisorLogManager
from .processes import SystevisorObservedProcessExit
from .processes import SystevisorProcessExecResult
from .processes import SystevisorProcessManager
from .processes import SystevisorProcessOutputChannel
from .processes import SystevisorProcessSpawnError
from .signals import SystevisorReceivedSignal
from .signals import SystevisorSignalFdioHandler


_SYSTEVISOR_COORDINATOR_LOG = get_module_logger(globals())


class SystevisorRuntimeCoordinator:
    def __init__(
            self,
            engine: SystevisorEngine,
            process_manager: SystevisorProcessManager,
            fdio_manager: FdioManager,
            clock: SystevisorClock,
            event_bus: SystevisorEventBus,
            log_manager: SystevisorLogManager,
            health_probe_runner: SystevisorHealthProbeRunner,
    ) -> None:
        self._engine = engine
        self._process_manager = process_manager
        self._fdio_manager = fdio_manager
        self._clock = clock
        self._event_bus = event_bus
        self._log_manager = log_manager
        self._health_probe_runner = health_probe_runner

        self._input_queue: ta.Deque[SystevisorEngineInput] = collections.deque()
        self._processing = False
        self._closed = False
        self._exec_handlers: ta.Dict[SystevisorRunId, SystevisorProcessExecFdioHandler] = {}
        self._pidfd_handlers: ta.Dict[SystevisorRunId, SystevisorProcessPidfdFdioHandler] = {}
        self._output_handlers: ta.Dict[SystevisorRunId, ta.List[FdioHandler]] = {}
        self._delivered_exec_results: ta.Set[SystevisorRunId] = set()
        self._failed_exec_runs: ta.Set[SystevisorRunId] = set()
        self._pending_exits: ta.Dict[SystevisorRunId, SystevisorObservedProcessExit] = {}
        self._signal_handler: ta.Optional[SystevisorSignalFdioHandler] = None

        self._deadline_handler = SystevisorDeadlineFdioHandler(clock, self._on_deadline)
        self._wait_handler = SystevisorProcessWaitFdioHandler(
            clock,
            self._observe_process_exits,
            process_manager.has_processes,
        )
        self._fdio_manager.register(self._deadline_handler)
        self._fdio_manager.register(self._wait_handler)

    @property
    def engine(self) -> SystevisorEngine:
        return self._engine

    @property
    def event_bus(self) -> SystevisorEventBus:
        return self._event_bus

    @property
    def log_manager(self) -> SystevisorLogManager:
        return self._log_manager

    def install_signal_handler(self, signal_numbers: ta.Iterable[int] = ()) -> None:
        if self._signal_handler is not None:
            raise RuntimeError('signal handler is already installed')
        handler = (
            SystevisorSignalFdioHandler(self._on_signal, signal_numbers)
            if signal_numbers else
            SystevisorSignalFdioHandler(self._on_signal)
        )
        handler.install()
        self._signal_handler = handler
        self._fdio_manager.register(handler)

    def submit(self, engine_input: SystevisorEngineInput) -> ta.Sequence[SystevisorEngineOutput]:
        if self._closed:
            raise RuntimeError('runtime coordinator is closed')
        self._input_queue.append(engine_input)
        if self._processing:
            return ()

        outputs: ta.List[SystevisorEngineOutput] = []
        self._processing = True
        try:
            while self._input_queue:
                current_input = self._input_queue.popleft()
                output = self._engine.step(current_input, self._clock.monotonic())
                if isinstance(current_input, SystevisorApplySnapshotCommand):
                    self._log_manager.set_default_strip_ansi(current_input.snapshot.config.manager.strip_ansi)
                    self._event_bus.set_journal_capacity(current_input.snapshot.config.api.event_backlog)
                outputs.append(output)
                for event in output.events:
                    _, failures = self._event_bus.publish('engine', event, self._clock.monotonic())
                    for failure in failures:
                        _SYSTEVISOR_COORDINATOR_LOG.error(
                            'Systevisor event subscriber %s failed',
                            failure.subscription_id,
                            exc_info=(
                                type(failure.exception),
                                failure.exception,
                                failure.exception.__traceback__,
                            ),
                        )
                for effect in output.effects:
                    self._execute_effect(effect)
        finally:
            self._processing = False
        return tuple(outputs)

    def _execute_effect(self, effect: SystevisorEngineEffect) -> None:
        if isinstance(effect, SystevisorSpawnProcessEffect):
            self._spawn(effect)
        elif isinstance(effect, SystevisorSignalProcessEffect):
            self._process_manager.signal_effect(effect)
        elif isinstance(effect, SystevisorScheduleDeadlineEffect):
            self._deadline_handler.schedule(effect)
        elif isinstance(effect, SystevisorApplyLiveConfigEffect):
            self._log_manager.update_process(effect)
        elif isinstance(effect, SystevisorRunHealthProbeEffect):
            self._run_health_probe(effect)
        else:
            raise TypeError(effect)

    def _on_deadline(self, fact: SystevisorEngineInput) -> None:
        self.submit(fact)

    def _spawn(self, effect: SystevisorSpawnProcessEffect) -> None:
        try:
            spawned = self._process_manager.spawn(effect)
        except (SystevisorProcessSpawnError, OSError) as exc:
            self._input_queue.append(SystevisorSpawnFailedFact(effect.run_id, str(exc)))
            return

        stdout_fd = self._process_manager.take_output_fd(
            effect.run_id,
            SystevisorProcessOutputChannel.STDOUT,
        )
        stderr_fd = self._process_manager.take_output_fd(
            effect.run_id,
            SystevisorProcessOutputChannel.STDERR,
        )
        output_handlers: ta.List[FdioHandler] = list(
            self._log_manager.register_process(effect, stdout_fd, stderr_fd),
        )
        self._output_handlers[effect.run_id] = output_handlers
        for handler in output_handlers:
            self._fdio_manager.register(handler)

        exec_error_fd = spawned.state.exec_error_fd
        if exec_error_fd is None:
            raise RuntimeError('spawned process has no exec handshake fd')
        def exec_ready(run_id: SystevisorRunId = effect.run_id) -> bool:
            return self._on_exec_ready(run_id)

        exec_handler = SystevisorProcessExecFdioHandler(exec_error_fd, exec_ready)
        self._exec_handlers[effect.run_id] = exec_handler
        self._fdio_manager.register(exec_handler)

        if spawned.state.pidfd is not None:
            pidfd_handler = SystevisorProcessPidfdFdioHandler(
                spawned.state.pidfd,
                self._observe_process_exits,
            )
            self._pidfd_handlers[effect.run_id] = pidfd_handler
            self._fdio_manager.register(pidfd_handler)
        self._wait_handler.poke()

    def _run_health_probe(self, effect: SystevisorRunHealthProbeEffect) -> None:
        started = self._health_probe_runner.start(effect, self._on_health_probe_result)
        run_id = started.command_run_id
        if run_id is None:
            return
        state = self._process_manager.get_state(run_id)
        if state is None or state.exec_error_fd is None:
            raise RuntimeError('spawned health command has no exec handshake fd')

        def exec_ready(command_run_id: SystevisorRunId = run_id) -> bool:
            return self._on_exec_ready(command_run_id)

        exec_handler = SystevisorProcessExecFdioHandler(state.exec_error_fd, exec_ready)
        self._exec_handlers[run_id] = exec_handler
        self._fdio_manager.register(exec_handler)
        if state.pidfd is not None:
            pidfd_handler = SystevisorProcessPidfdFdioHandler(
                state.pidfd,
                self._observe_process_exits,
            )
            self._pidfd_handlers[run_id] = pidfd_handler
            self._fdio_manager.register(pidfd_handler)
        self._wait_handler.poke()

    def _on_health_probe_result(self, fact: SystevisorHealthProbeResultFact) -> None:
        self.submit(fact)

    def _on_exec_ready(self, run_id: SystevisorRunId) -> bool:
        result = self._process_manager.poll_exec_result(run_id)
        if result is None:
            return False
        self._handle_exec_result(result)
        pending_exit = self._pending_exits.pop(run_id, None)
        if pending_exit is not None:
            self._complete_process_exit(pending_exit)
        return True

    def _handle_exec_result(self, result: SystevisorProcessExecResult) -> None:
        if result.run_id in self._delivered_exec_results:
            return
        self._delivered_exec_results.add(result.run_id)
        exec_handler = self._exec_handlers.pop(result.run_id, None)
        if exec_handler is not None:
            exec_handler.close()
        if self._health_probe_runner.owns_command_run(result.run_id):
            self._health_probe_runner.command_exec_result(result)
            return
        if result.succeeded:
            self.submit(SystevisorSpawnSucceededFact(result.run_id))
        else:
            self._failed_exec_runs.add(result.run_id)
            self.submit(SystevisorSpawnFailedFact(result.run_id, result.message or 'child setup failed'))

    def _observe_process_exits(self) -> None:
        for observed in self._process_manager.poll_exits():
            if observed.run_id not in self._delivered_exec_results:
                result = self._process_manager.poll_exec_result(observed.run_id)
                if result is None:
                    self._pending_exits[observed.run_id] = observed
                    continue
                self._handle_exec_result(result)
            self._complete_process_exit(observed)

    def _complete_process_exit(self, observed: SystevisorObservedProcessExit) -> None:
        pidfd_handler = self._pidfd_handlers.pop(observed.run_id, None)
        if pidfd_handler is not None:
            pidfd_handler.close()
        self._process_manager.acknowledge_exit(observed.run_id)
        if self._health_probe_runner.owns_command_run(observed.run_id):
            self._health_probe_runner.command_exit(observed)
            self._delivered_exec_results.discard(observed.run_id)
            self._pending_exits.pop(observed.run_id, None)
            return
        self._log_manager.retire_process(observed.run_id)
        if observed.run_id in self._failed_exec_runs:
            self._failed_exec_runs.remove(observed.run_id)
        else:
            self.submit(SystevisorProcessExitedFact(observed.run_id, observed.return_code))
        self._delivered_exec_results.discard(observed.run_id)
        self._pending_exits.pop(observed.run_id, None)

    def _on_signal(self, received: SystevisorReceivedSignal) -> None:
        if received.signal_number == signal.SIGCHLD:
            self._observe_process_exits()
        elif received.signal_number in {signal.SIGTERM, signal.SIGINT, signal.SIGQUIT}:
            self.submit(SystevisorShutdownCommand())
        elif received.signal_number == signal.SIGHUP:
            self._event_bus.publish('runtime.reload_requested', received, self._clock.monotonic())
        else:
            self._event_bus.publish('runtime.signal', received, self._clock.monotonic())

    def poll(self, timeout: ta.Optional[float] = None) -> None:
        self._fdio_manager.poll(timeout=timeout)
        for run_id in tuple(self._output_handlers):
            if all(handler.closed for handler in self._output_handlers[run_id]):
                del self._output_handlers[run_id]

    def close(self) -> None:
        if self._closed:
            return
        if self._signal_handler is not None:
            self._signal_handler.close()
            self._signal_handler = None
        for exec_handler in self._exec_handlers.values():
            exec_handler.close()
        for pidfd_handler in self._pidfd_handlers.values():
            pidfd_handler.close()
        for handlers in self._output_handlers.values():
            for output_handler in handlers:
                output_handler.close()
        self._deadline_handler.close()
        self._wait_handler.close()
        self._health_probe_runner.close()
        self._log_manager.close()
        self._closed = True
