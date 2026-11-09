# ruff: noqa: PT009 UP006 UP007 UP045
import os
import select
import signal
import typing as ta
import unittest

from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorExecConfig
from ..configs.models import SystevisorRestartConfig
from ..configs.models import SystevisorSignalScope
from ..configs.models import SystevisorStopConfig
from ..configs.models import SystevisorUnitConfig
from ..configs.snapshots import systevisor_build_config_snapshot
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..runtime.clocks import SystevisorSystemClock
from ..runtime.emergencies import SystevisorEmergencyStop
from ..runtime.processes import SystevisorPosixProcessSignalBackend
from ..runtime.processes import SystevisorProcessManager
from ..runtime.processes import SystevisorSignalLease


_SYSTEVISOR_TEST_EMERGENCY_TIMEOUT_SECS = 10.


class SystevisorTestEmergencySignalBackend(SystevisorPosixProcessSignalBackend):
    def __init__(self) -> None:
        self.sent: ta.List[ta.Tuple[int, str, int]] = []

    def send_process(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        self.sent.append((int(lease.run_id), 'process', signal_number))
        return super().send_process(lease, signal_number)

    def send_session(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
        self.sent.append((int(lease.run_id), 'session', signal_number))
        return super().send_session(lease, signal_number)


def _systevisor_test_emergency_effect(
        run_id: int,
        argv: ta.Sequence[str],
        stop: SystevisorStopConfig,
) -> SystevisorSpawnProcessEffect:
    snapshot = systevisor_build_config_snapshot(SystevisorConfig(units={
        f'unit{run_id}': SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=tuple(argv)),
            restart=SystevisorRestartConfig(start_secs=0.),
            stop=stop,
        ),
    }), (), ())
    spec = snapshot.instances[SystevisorInstanceId(f'unit{run_id}:0')]
    return SystevisorSpawnProcessEffect(SystevisorRunId(run_id), spec.instance_id, spec)


class TestSystevisorEmergencyStop(unittest.TestCase):
    def _spawn_ready(
            self,
            manager: SystevisorProcessManager,
            effect: SystevisorSpawnProcessEffect,
    ) -> int:
        # Each program announces itself once it is past exec and has its signal handling in place.
        state = manager.spawn(effect).state
        assert state.stdout_fd is not None
        self.addCleanup(os.close, state.stdout_fd)
        readable, _, _ = select.select([state.stdout_fd], [], [], _SYSTEVISOR_TEST_EMERGENCY_TIMEOUT_SECS)
        self.assertTrue(readable)
        self.assertEqual(os.read(state.stdout_fd, 4096), b'ready\n')
        self.assertIsNotNone(manager.poll_exec_result(effect.run_id))
        return state.pid

    def test_stops_every_owned_process_and_escalates_past_its_own_timeout(self) -> None:
        backend = SystevisorTestEmergencySignalBackend()
        manager = SystevisorProcessManager(signal_backend=backend)
        obedient_pid = self._spawn_ready(manager, _systevisor_test_emergency_effect(
            1,
            ('/bin/sh', '-c', 'echo ready; exec sleep 60'),
            SystevisorStopConfig(signal='INT', timeout_secs=60.),
        ))
        stubborn_pid = self._spawn_ready(manager, _systevisor_test_emergency_effect(
            2,
            ('/bin/sh', '-c', 'trap "" TERM; echo ready; while :; do sleep 60; done'),
            SystevisorStopConfig(timeout_secs=.05, scope=SystevisorSignalScope.SESSION),
        ))

        left = SystevisorEmergencyStop(manager, SystevisorSystemClock(), poll_interval_secs=.01).run()

        self.assertEqual(left, ())
        self.assertFalse(manager.has_processes())
        self.assertEqual(backend.sent, [
            (1, 'process', signal.SIGINT),
            (2, 'session', signal.SIGTERM),
            (2, 'session', signal.SIGKILL),
            # Reaping a session leader sweeps whatever is left of its session.
            (2, 'session', signal.SIGKILL),
        ])
        for pid in (obedient_pid, stubborn_pid):
            with self.assertRaises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)

    def test_nothing_owned_is_a_noop(self) -> None:
        backend = SystevisorTestEmergencySignalBackend()
        manager = SystevisorProcessManager(signal_backend=backend)

        self.assertEqual(SystevisorEmergencyStop(manager, SystevisorSystemClock()).run(), ())
        self.assertEqual(backend.sent, [])
