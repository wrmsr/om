# ruff: noqa: PT009 UP006 UP007 UP045
import os
import select
import signal
import time
import typing as ta
import unittest

from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorIdentityConfig
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorSignalScope
from x.systevisor.configs.models import SystevisorStopConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorSignalProcessEffect
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.states import SystevisorSignalReason
from x.systevisor.runtime.processes import SystevisorChildContext
from x.systevisor.runtime.processes import SystevisorChildModifier
from x.systevisor.runtime.processes import SystevisorChildPidProvider
from x.systevisor.runtime.processes import SystevisorObservedProcessExit
from x.systevisor.runtime.processes import SystevisorOwnedProcessStatus
from x.systevisor.runtime.processes import SystevisorProcessExecResult
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.runtime.processes import SystevisorProcessOwnershipError
from x.systevisor.runtime.processes import SystevisorProcessSpawnError
from x.systevisor.runtime.processes import systevisor_close_process_retirement


_SYSTEVISOR_TEST_PROCESS_TIMEOUT_SECS = 10.


def _systevisor_test_process_effect(
        argv: tuple,
        *,
        run_id: int = 1,
        scope: SystevisorSignalScope = SystevisorSignalScope.PROCESS,
        identity: SystevisorIdentityConfig = SystevisorIdentityConfig(),
) -> SystevisorSpawnProcessEffect:
    config = SystevisorConfig(units={
        'test': SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=argv),
            restart=SystevisorRestartConfig(start_secs=0.),
            stop=SystevisorStopConfig(scope=scope),
            identity=identity,
        ),
    })
    snapshot = systevisor_build_config_snapshot(config, (), ())
    spec = snapshot.instances[SystevisorInstanceId('test:0')]
    return SystevisorSpawnProcessEffect(
        run_id=SystevisorRunId(run_id),
        instance_id=spec.instance_id,
        spec=spec,
    )


def _systevisor_test_wait_exec_result(
        manager: SystevisorProcessManager,
        run_id: SystevisorRunId,
) -> SystevisorProcessExecResult:
    deadline = time.monotonic() + _SYSTEVISOR_TEST_PROCESS_TIMEOUT_SECS
    while time.monotonic() < deadline:
        state = manager.get_state(run_id)
        assert state is not None
        assert state.exec_error_fd is not None
        readable, _, _ = select.select([state.exec_error_fd], [], [], max(0., deadline - time.monotonic()))
        if not readable:
            break
        result = manager.poll_exec_result(run_id)
        if result is not None:
            return result
    raise AssertionError('timed out waiting for exec handshake')


def _systevisor_test_wait_exec(manager: SystevisorProcessManager, run_id: SystevisorRunId) -> None:
    result = _systevisor_test_wait_exec_result(manager, run_id)
    if not result.succeeded:
        raise AssertionError(result.message)


def _systevisor_test_wait_exit(
        manager: SystevisorProcessManager,
        run_id: SystevisorRunId,
) -> SystevisorObservedProcessExit:
    deadline = time.monotonic() + _SYSTEVISOR_TEST_PROCESS_TIMEOUT_SECS
    while time.monotonic() < deadline:
        exits = manager.poll_exits()
        if exits:
            if len(exits) != 1 or exits[0].run_id != run_id:
                raise AssertionError(exits)
            return exits[0]
    raise AssertionError('timed out waiting for child exit')


def _systevisor_test_cleanup_process(manager: SystevisorProcessManager, run_id: SystevisorRunId) -> None:
    state = manager.get_state(run_id)
    if state is None:
        return
    if state.status in {SystevisorOwnedProcessStatus.SPAWNING, SystevisorOwnedProcessStatus.RUNNING}:
        try:
            manager.signal(run_id, 'KILL', SystevisorSignalScope.PROCESS)
        except (ProcessLookupError, SystevisorProcessOwnershipError):
            pass
        _systevisor_test_wait_exit(manager, run_id)
    retirement = manager.acknowledge_exit(run_id)
    systevisor_close_process_retirement(retirement)


class SystevisorTestChildModifier(SystevisorChildModifier):
    def __init__(self, checkpoint_fd: int) -> None:
        self._checkpoint_fd = checkpoint_fd

    def preserved_fds(self, context: SystevisorChildContext) -> tuple:
        return (self._checkpoint_fd,)

    def after_identity(self, context: SystevisorChildContext) -> None:
        os.write(self._checkpoint_fd, b'modified')


class SystevisorTestChildPidProvider(SystevisorChildPidProvider):
    def __init__(self, pids: ta.Iterable[int] = ()) -> None:
        self.pids = tuple(pids)

    def child_pids(self) -> ta.Sequence[int]:
        return self.pids


class TestSystevisorProcesses(unittest.TestCase):
    def test_exec_and_wait_are_observed_before_explicit_reap(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(('/bin/sh', '-c', 'exit 7'))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)

        _systevisor_test_wait_exec(manager, effect.run_id)
        observed = _systevisor_test_wait_exit(manager, effect.run_id)

        self.assertEqual(observed.return_code, 7)
        state = manager.get_state(effect.run_id)
        assert state is not None
        self.assertEqual(state.status, SystevisorOwnedProcessStatus.EXIT_OBSERVED)
        wait_result = os.waitid(os.P_PID, state.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        assert wait_result is not None
        self.assertEqual(state.pid, wait_result.si_pid)

        retirement = manager.acknowledge_exit(effect.run_id)
        systevisor_close_process_retirement(retirement)
        self.assertIsNone(manager.get_state(effect.run_id))

    def test_signal_lease_prevents_wait_observation(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(('/bin/sh', '-c', 'exit 0'))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        _systevisor_test_wait_exec(manager, effect.run_id)

        with manager.acquire_signal_lease(effect.run_id):
            deadline = time.monotonic() + _SYSTEVISOR_TEST_PROCESS_TIMEOUT_SECS
            state = manager.get_state(effect.run_id)
            assert state is not None
            while time.monotonic() < deadline:
                result = os.waitid(os.P_PID, state.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                if result is not None and result.si_pid:
                    break
            else:
                raise AssertionError('timed out waiting for locked child to exit')
            self.assertEqual(manager.poll_exits(), ())
            locked_state = manager.get_state(effect.run_id)
            assert locked_state is not None
            self.assertEqual(locked_state.signal_lease_count, 1)

        observed = _systevisor_test_wait_exit(manager, effect.run_id)
        self.assertEqual(observed.return_code, 0)

    def test_run_scoped_signal_terminates_owned_child(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(('/bin/sleep', '60'))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        _systevisor_test_wait_exec(manager, effect.run_id)

        delivery = manager.signal_effect(SystevisorSignalProcessEffect(
            run_id=effect.run_id,
            signal='TERM',
            scope=SystevisorSignalScope.PROCESS,
            reason=SystevisorSignalReason.STOP,
        ))
        observed = _systevisor_test_wait_exit(manager, effect.run_id)

        self.assertTrue(delivery.delivered)
        self.assertEqual(delivery.signal, signal.SIGTERM)
        self.assertEqual(observed.return_code, -signal.SIGTERM)

    def test_unknown_run_can_never_reach_signal_backend(self) -> None:
        manager = SystevisorProcessManager()
        with self.assertRaises(SystevisorProcessOwnershipError):
            manager.signal(SystevisorRunId(999), 'KILL', SystevisorSignalScope.PROCESS)

    def test_session_signal_requires_an_owned_isolated_session(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(('/bin/sleep', '60'))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        _systevisor_test_wait_exec(manager, effect.run_id)

        with self.assertRaises(SystevisorProcessOwnershipError):
            manager.signal(effect.run_id, 'TERM', SystevisorSignalScope.SESSION)

    def test_owned_isolated_session_can_be_signaled(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(
            ('/bin/sleep', '60'),
            scope=SystevisorSignalScope.SESSION,
        )
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        _systevisor_test_wait_exec(manager, effect.run_id)

        delivery = manager.signal(effect.run_id, 'TERM', SystevisorSignalScope.SESSION)
        observed = _systevisor_test_wait_exit(manager, effect.run_id)

        self.assertTrue(delivery.delivered)
        self.assertEqual(observed.return_code, -signal.SIGTERM)

    def test_exec_failure_is_reported_without_losing_wait_ownership(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(('/definitely/not/a/systevisor/executable',))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)

        result = _systevisor_test_wait_exec_result(manager, effect.run_id)

        self.assertFalse(result.succeeded)
        self.assertIn('No such file', result.message or '')
        observed = _systevisor_test_wait_exit(manager, effect.run_id)
        self.assertEqual(observed.return_code, 127)

    def test_captured_stdout_and_stderr_remain_owned_through_exit(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect((
            '/bin/sh',
            '-c',
            'printf stdout-value; printf stderr-value >&2',
        ))
        spawned = manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        _systevisor_test_wait_exec(manager, effect.run_id)
        _systevisor_test_wait_exit(manager, effect.run_id)

        assert spawned.state.stdout_fd is not None
        assert spawned.state.stderr_fd is not None
        self.assertEqual(os.read(spawned.state.stdout_fd, 4096), b'stdout-value')
        self.assertEqual(os.read(spawned.state.stderr_fd, 4096), b'stderr-value')

        retirement = manager.acknowledge_exit(effect.run_id)
        self.assertEqual(retirement.stdout_fd, spawned.state.stdout_fd)
        self.assertEqual(retirement.stderr_fd, spawned.state.stderr_fd)
        systevisor_close_process_retirement(retirement)

    def test_child_modifier_receives_only_explicitly_preserved_fd(self) -> None:
        checkpoint_read_fd, checkpoint_write_fd = os.pipe()
        self.addCleanup(os.close, checkpoint_read_fd)
        self.addCleanup(os.close, checkpoint_write_fd)
        manager = SystevisorProcessManager(
            child_modifiers=(SystevisorTestChildModifier(checkpoint_write_fd),),
        )
        effect = _systevisor_test_process_effect(('/bin/true',))
        manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)

        readable, _, _ = select.select(
            [checkpoint_read_fd],
            [],
            [],
            _SYSTEVISOR_TEST_PROCESS_TIMEOUT_SECS,
        )
        self.assertTrue(readable)
        self.assertEqual(os.read(checkpoint_read_fd, 4096), b'modified')
        _systevisor_test_wait_exec(manager, effect.run_id)
        _systevisor_test_wait_exit(manager, effect.run_id)

    def test_unknown_identity_is_rejected_before_fork(self) -> None:
        manager = SystevisorProcessManager()
        effect = _systevisor_test_process_effect(
            ('/bin/true',),
            identity=SystevisorIdentityConfig(user='systevisor-user-that-does-not-exist-0123456789'),
        )

        with self.assertRaises(SystevisorProcessSpawnError):
            manager.spawn(effect)

        self.assertEqual(manager.snapshot_states(), ())

    def test_unknown_child_is_reaped_without_receiving_a_signal_capability(self) -> None:
        provider = SystevisorTestChildPidProvider()
        manager = SystevisorProcessManager(child_pid_provider=provider)
        manager.set_reap_unknown_children(True)
        pid = os.fork()
        if pid == 0:
            os._exit(23)
        provider.pids = (pid,)
        try:
            os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT)
            reaped = manager.poll_unknown_exits()

            self.assertEqual(len(reaped), 1)
            self.assertEqual(reaped[0].pid, pid)
            self.assertEqual(reaped[0].return_code, 23)
            with self.assertRaises(ChildProcessError):
                os.waitpid(pid, os.WNOHANG)
        finally:
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass

    def test_unknown_reaper_never_consumes_an_owned_child(self) -> None:
        provider = SystevisorTestChildPidProvider()
        manager = SystevisorProcessManager(child_pid_provider=provider)
        manager.set_reap_unknown_children(True)
        effect = _systevisor_test_process_effect(('/bin/true',))
        spawned = manager.spawn(effect)
        self.addCleanup(_systevisor_test_cleanup_process, manager, effect.run_id)
        provider.pids = (spawned.state.pid,)
        _systevisor_test_wait_exec(manager, effect.run_id)
        os.waitid(os.P_PID, spawned.state.pid, os.WEXITED | os.WNOWAIT)

        self.assertEqual(manager.poll_unknown_exits(), ())
        self.assertEqual(_systevisor_test_wait_exit(manager, effect.run_id).run_id, effect.run_id)
