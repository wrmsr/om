# ruff: noqa: UP006 UP007 UP045
import time
import typing as ta

from omcore.logs.modules import get_module_logger

from ..configs.models import SystevisorSignalScope
from ..configs.models import SystevisorStopConfig
from ..core.identities import SystevisorRunId
from .clocks import SystevisorClock
from .processes import SystevisorOwnedProcessState
from .processes import SystevisorOwnedProcessStatus
from .processes import SystevisorProcessManager
from .processes import SystevisorProcessOwnershipError


##


_SYSTEVISOR_EMERGENCIES_LOG = get_module_logger(globals())


class SystevisorEmergencyStop:
    """
    Stops every process the manager still owns using nothing but the process manager, for the exits where the engine or
    the reactor is the thing that failed. Each run gets its unit's own stop signal and timeout before being killed, but
    there is no ordering, no output draining, and no event: this is what stands between an internal error and children
    left running with nothing supervising them.
    """

    def __init__(
            self,
            process_manager: SystevisorProcessManager,
            clock: SystevisorClock,
            *,
            sleep: ta.Callable[[float], None] = time.sleep,
            poll_interval_secs: float = .05,
            kill_wait_secs: float = 5.,
    ) -> None:
        super().__init__()

        self._process_manager = process_manager
        self._clock = clock
        self._sleep = sleep
        self._poll_interval_secs = poll_interval_secs
        self._kill_wait_secs = kill_wait_secs

    def _signal(self, run_id: SystevisorRunId, signal_name: str, scope: SystevisorSignalScope) -> None:
        # A session can only be signalled once its leader has confirmed exec, so fall back to the direct child.
        failure: ta.Optional[BaseException] = None
        for attempt_scope in dict.fromkeys((scope, SystevisorSignalScope.PROCESS)):
            try:
                self._process_manager.signal(run_id, signal_name, attempt_scope)
            except (SystevisorProcessOwnershipError, OSError) as exc:
                failure = exc
            else:
                return
        _SYSTEVISOR_EMERGENCIES_LOG.warning('Systevisor could not signal run %s: %s', int(run_id), failure)

    def _reap(self) -> None:
        try:
            self._process_manager.poll_exits()
        except SystevisorProcessOwnershipError as exc:
            _SYSTEVISOR_EMERGENCIES_LOG.warning('Systevisor could not observe exits: %s', exc)
        for state in self._process_manager.snapshot_states():
            if state.status is not SystevisorOwnedProcessStatus.EXIT_OBSERVED:
                continue
            try:
                self._process_manager.acknowledge_exit(state.run_id)
            except SystevisorProcessOwnershipError as exc:
                _SYSTEVISOR_EMERGENCIES_LOG.warning('Systevisor could not reap run %s: %s', int(state.run_id), exc)

    def run(self) -> ta.Sequence[SystevisorOwnedProcessState]:
        """Returns whatever could not be stopped."""

        self._reap()
        stop_configs: ta.Dict[SystevisorRunId, SystevisorStopConfig] = {
            run_id: context.spec.unit.stop
            for run_id, context in self._process_manager.child_contexts().items()
        }
        if not stop_configs:
            return self._process_manager.snapshot_states()

        _SYSTEVISOR_EMERGENCIES_LOG.warning('Systevisor is stopping %d owned process(es) directly', len(stop_configs))
        now = self._clock.monotonic()
        kill_at: ta.Dict[SystevisorRunId, float] = {}
        for run_id, stop in stop_configs.items():
            kill_at[run_id] = now + stop.timeout_secs
            self._signal(run_id, stop.signal, stop.scope)

        give_up_at: ta.Optional[float] = None
        while True:
            self._reap()
            remaining = {state.run_id for state in self._process_manager.snapshot_states()}
            if not remaining:
                break

            now = self._clock.monotonic()
            for run_id in sorted(remaining & set(kill_at)):
                if kill_at[run_id] <= now:
                    del kill_at[run_id]
                    stop = stop_configs[run_id]
                    self._signal(run_id, stop.kill_signal, stop.kill_scope or stop.scope)

            if not (remaining & set(kill_at)):
                if give_up_at is None:
                    give_up_at = now + self._kill_wait_secs
                elif give_up_at <= now:
                    break
            self._sleep(self._poll_interval_secs)

        left = self._process_manager.snapshot_states()
        for state in left:
            _SYSTEVISOR_EMERGENCIES_LOG.error(
                'Systevisor is leaving run %s (pid %d) behind',
                int(state.run_id),
                state.pid,
            )
        return left
