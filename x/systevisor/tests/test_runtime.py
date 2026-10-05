# ruff: noqa: PT009 UP006 UP007 UP045
import errno
import os
import pathlib
import select
import signal
import tempfile
import time
import typing as ta
import unittest

from omcore.io.fdio.manager import FdioManager
from omcore.io.fdio.pollers import FdioPoller
from omcore.io.fdio.pollers import SelectFdioPoller
from omcore.lite.inject import inj

from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorExecConfig
from ..configs.models import SystevisorManagerConfig
from ..configs.models import SystevisorOutputConfig
from ..configs.models import SystevisorOutputMode
from ..configs.models import SystevisorRestartConfig
from ..configs.models import SystevisorStdioConfig
from ..configs.models import SystevisorStopConfig
from ..configs.models import SystevisorUnitConfig
from ..configs.snapshots import systevisor_build_config_snapshot
from ..core.effects import SystevisorScheduleDeadlineEffect
from ..core.effects import SystevisorSpawnProcessEffect
from ..core.engine import SystevisorEngine
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..core.inputs import SystevisorApplySnapshotCommand
from ..core.inputs import SystevisorEngineInput
from ..core.inputs import SystevisorShutdownCommand
from ..core.states import SystevisorDeadlineKind
from ..core.states import SystevisorProcessState
from ..resources.inject import systevisor_bind_resources
from ..runtime.clocks import SystevisorSystemClock
from ..runtime.coordinator import SystevisorRuntimeCoordinator
from ..runtime.events import SystevisorEventBus
from ..runtime.fdio import SystevisorDeadlineFdioHandler
from ..runtime.health import SystevisorFdioHealthProbeRunner
from ..runtime.inject import systevisor_bind_runtime
from ..runtime.logs import SystevisorByteRingBuffer
from ..runtime.logs import SystevisorChildSyslogWriter
from ..runtime.logs import SystevisorLogChannelState
from ..runtime.logs import SystevisorLogManager
from ..runtime.logs import SystevisorLogStream
from ..runtime.logs import SystevisorRotatingFileLogSink
from ..runtime.processes import SystevisorChildContext
from ..runtime.processes import SystevisorChildModifier
from ..runtime.processes import SystevisorPosixProcessSignalBackend
from ..runtime.processes import SystevisorProcessManager
from ..runtime.processes import SystevisorSignalLease
from ..runtime.signals import SystevisorSignalFdioHandler
from .fakes import SystevisorFakeClock


_SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS = 10.


class SystevisorTestChildSyslogWriter(SystevisorChildSyslogWriter):
    def __init__(self) -> None:
        self.records: ta.List[ta.Tuple[SystevisorInstanceId, SystevisorRunId, SystevisorLogStream, bytes]] = []

    def write(
            self,
            instance_id: SystevisorInstanceId,
            run_id: SystevisorRunId,
            stream: SystevisorLogStream,
            data: bytes,
    ) -> None:
        self.records.append((instance_id, run_id, stream, data))


def _systevisor_test_runtime_log_effect(
        output: SystevisorOutputConfig,
        run_id: int = 1,
) -> SystevisorSpawnProcessEffect:
    config = SystevisorConfig(units={
        'worker': SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('worker',)),
            stdio=SystevisorStdioConfig(stdout=output),
        ),
    })
    snapshot = systevisor_build_config_snapshot(config, (), ())
    spec = snapshot.instances[SystevisorInstanceId('worker:0')]
    return SystevisorSpawnProcessEffect(SystevisorRunId(run_id), spec.instance_id, spec)


class SystevisorTestRuntimeFixture:
    def __init__(
            self,
            *,
            engine: ta.Optional[SystevisorEngine] = None,
            process_manager: ta.Optional[SystevisorProcessManager] = None,
    ) -> None:
        self.poller = SelectFdioPoller()
        self.fdio_manager = FdioManager(self.poller)
        self.clock = SystevisorSystemClock()
        self.event_bus = SystevisorEventBus()
        self.process_manager = process_manager if process_manager is not None else SystevisorProcessManager()
        self.log_manager = SystevisorLogManager(self.event_bus, self.clock)
        self.coordinator = SystevisorRuntimeCoordinator(
            engine if engine is not None else SystevisorEngine(),
            self.process_manager,
            self.fdio_manager,
            self.clock,
            self.event_bus,
            self.log_manager,
            SystevisorFdioHealthProbeRunner(self.process_manager, self.fdio_manager, self.clock, self.log_manager),
        )

    def poll_until(self, predicate: ta.Callable[[], bool]) -> None:
        deadline = time.monotonic() + _SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS
        while not predicate():
            if time.monotonic() >= deadline:
                raise AssertionError('timed out waiting for the runtime')
            self.coordinator.poll(timeout=.1)

    def close(self) -> None:
        self.coordinator.close()
        self.poller.close()


class TestSystevisorEventBus(unittest.TestCase):
    def test_journal_stream_gap_and_callback_isolation(self) -> None:
        event_bus = SystevisorEventBus(journal_capacity=2)
        stream = event_bus.subscribe_stream(capacity=2)
        callback_events: ta.List[ta.Any] = []
        event_bus.subscribe_callback(callback_events.append)

        def fail_callback(event: object) -> None:
            raise RuntimeError('injected subscriber failure')

        event_bus.subscribe_callback(fail_callback)
        failures: ta.List[ta.Any] = []
        for index in range(3):
            _, current_failures = event_bus.publish('test', index, float(index))
            failures.extend(current_failures)

        self.assertEqual([event.payload for event in event_bus.journal()], [1, 2])
        batch = stream.read()
        self.assertEqual([event.payload for event in batch.events], [1, 2])
        self.assertEqual(batch.dropped_count, 1)
        self.assertEqual([event.payload for event in callback_events], [0, 1, 2])
        self.assertEqual(len(failures), 1)


class TestSystevisorLogs(unittest.TestCase):
    def test_byte_ring_reports_eviction_gap_and_preserves_offsets_on_resize(self) -> None:
        ring = SystevisorByteRingBuffer(5)
        self.assertEqual(ring.append(b'abc'), (0, 3))
        self.assertEqual(ring.append(b'defgh'), (3, 8))

        read = ring.read(0)
        self.assertEqual((read.start_offset, read.end_offset, read.data, read.gap_bytes), (3, 8, b'defgh', 3))

        ring.resize(3)
        read = ring.read(3)
        self.assertEqual((read.start_offset, read.end_offset, read.data, read.gap_bytes), (5, 8, b'fgh', 2))

    def test_rotating_file_sink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'child.log'
            sink = SystevisorRotatingFileLogSink(SystevisorOutputConfig(
                mode=SystevisorOutputMode.FILE,
                file=str(path),
                max_bytes=5,
                backups=2,
            ))
            sink.write(b'abc')
            sink.write(b'def')
            sink.close()

            self.assertEqual(path.read_bytes(), b'def')
            self.assertEqual((pathlib.Path(f'{path}.1')).read_bytes(), b'abc')

    def test_syslog_sink_is_injected_and_preserves_raw_channel_data(self) -> None:
        writer = SystevisorTestChildSyslogWriter()
        manager = SystevisorLogManager(SystevisorEventBus(), SystevisorFakeClock(), writer)
        effect = _systevisor_test_runtime_log_effect(SystevisorOutputConfig(syslog=True))
        read_fd, write_fd = os.pipe()
        handlers = manager.register_process(effect, read_fd, None)
        self.addCleanup(os.close, write_fd)
        self.addCleanup(handlers[0].close)
        self.addCleanup(manager.close)

        manager.append(effect.run_id, SystevisorLogStream.STDOUT, b'raw\x00bytes')

        self.assertEqual(writer.records, [(
            effect.instance_id,
            effect.run_id,
            SystevisorLogStream.STDOUT,
            b'raw\x00bytes',
        )])

    def test_automatic_child_log_files_and_scoped_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            stale = root / 'systevisor-child-worker:0-99-stdout.log.1'
            unrelated = root / 'application.log'
            stale.write_bytes(b'stale')
            unrelated.write_bytes(b'keep')
            manager = SystevisorLogManager(SystevisorEventBus(), SystevisorFakeClock())
            manager.configure_manager(SystevisorManagerConfig(
                child_log_directory=temp_dir,
                cleanup_auto_logs=True,
            ), cleanup=True)
            self.assertFalse(stale.exists())
            self.assertEqual(unrelated.read_bytes(), b'keep')

            effect = _systevisor_test_runtime_log_effect(SystevisorOutputConfig(
                mode=SystevisorOutputMode.FILE,
                file=None,
            ))
            read_fd, write_fd = os.pipe()
            handlers = manager.register_process(effect, read_fd, None)
            manager.append(effect.run_id, SystevisorLogStream.STDOUT, b'auto-log')
            manager.close()
            handlers[0].close()
            os.close(write_fd)

            generated = root / 'systevisor-child-worker:0-1-stdout.log'
            self.assertEqual(generated.read_bytes(), b'auto-log')

    def test_rehydrated_non_append_file_sink_does_not_truncate_pre_exec_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'child.log'
            path.write_bytes(b'before-exec')
            manager = SystevisorLogManager(SystevisorEventBus(), SystevisorFakeClock())
            manager.rehydrate((SystevisorLogChannelState(
                state_schema_version=1,
                run_id=SystevisorRunId(1),
                instance_id=SystevisorInstanceId('worker:0'),
                stream=SystevisorLogStream.STDOUT,
                config=SystevisorOutputConfig(
                    mode=SystevisorOutputMode.FILE,
                    file=str(path),
                    append=False,
                ),
                data=b'before-exec',
                end_offset=11,
                retired=False,
                created_at=0.,
                last_activity_at=0.,
            ),))

            manager.append(SystevisorRunId(1), SystevisorLogStream.STDOUT, b'-after-exec')
            manager.close()

            self.assertEqual(path.read_bytes(), b'before-exec-after-exec')


class TestSystevisorFdioRuntime(unittest.TestCase):
    def test_virtual_deadline_handler(self) -> None:
        clock = SystevisorFakeClock()
        facts: ta.List[ta.Any] = []
        handler = SystevisorDeadlineFdioHandler(clock, facts.append)
        handler.schedule(SystevisorScheduleDeadlineEffect(
            deadline_id=1,
            deadline_at=5.,
            kind=SystevisorDeadlineKind.BACKOFF,
            instance_id=SystevisorInstanceId('unit:0'),
            run_id=SystevisorRunId(1),
        ))

        handler.on_timeout()
        self.assertEqual(facts, [])
        clock.advance(5.)
        handler.on_timeout()
        self.assertEqual([fact.deadline_id for fact in facts], [1])

    def test_signal_wakeup_fd_dispatch(self) -> None:
        received: ta.List[ta.Any] = []
        handler = SystevisorSignalFdioHandler(received.append, (signal.SIGUSR1,))
        handler.install()
        self.addCleanup(handler.close)

        signal.raise_signal(signal.SIGUSR1)
        readable, _, _ = select.select([handler.fd()], [], [], _SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS)
        self.assertTrue(readable)
        handler.on_readable()
        self.assertEqual([item.signal_number for item in received], [signal.SIGUSR1])

        handler.reconfigure((signal.SIGWINCH,))
        signal.raise_signal(signal.SIGWINCH)
        readable, _, _ = select.select([handler.fd()], [], [], _SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS)
        self.assertTrue(readable)
        handler.on_readable()
        self.assertEqual([item.signal_number for item in received], [signal.SIGUSR1, signal.SIGWINCH])

    def test_engine_process_and_logs_run_end_to_end(self) -> None:
        poller = SelectFdioPoller()
        fdio_manager = FdioManager(poller)
        clock = SystevisorSystemClock()
        event_bus = SystevisorEventBus()
        process_manager = SystevisorProcessManager()
        log_manager = SystevisorLogManager(event_bus, clock)
        health_probe_runner = SystevisorFdioHealthProbeRunner(
            process_manager,
            fdio_manager,
            clock,
            log_manager,
        )
        coordinator = SystevisorRuntimeCoordinator(
            SystevisorEngine(),
            process_manager,
            fdio_manager,
            clock,
            event_bus,
            log_manager,
            health_probe_runner,
        )
        self.addCleanup(coordinator.close)
        self.addCleanup(poller.close)
        config = SystevisorConfig(units={
            'echo': SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=(
                    '/bin/sh',
                    '-c',
                    'printf systevisor-stdout; printf systevisor-stderr >&2',
                )),
                restart=SystevisorRestartConfig(start_secs=0.),
            ),
        })
        snapshot = systevisor_build_config_snapshot(config, (), ())

        coordinator.submit(SystevisorApplySnapshotCommand(snapshot))
        deadline = time.monotonic() + _SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS
        instance_id = SystevisorInstanceId('echo:0')
        run_id = SystevisorRunId(1)
        while time.monotonic() < deadline:
            coordinator.poll(timeout=1.)
            instance = coordinator.engine.state.instances[instance_id]
            if instance.process_state is SystevisorProcessState.EXITED:
                stdout = log_manager.read(run_id, SystevisorLogStream.STDOUT, 0).data
                stderr = log_manager.read(run_id, SystevisorLogStream.STDERR, 0).data
                if stdout == b'systevisor-stdout' and stderr == b'systevisor-stderr':
                    break
        else:
            self.fail('timed out waiting for coordinated process completion')

        self.assertFalse(process_manager.has_processes())
        self.assertIn('engine', {event.topic for event in event_bus.journal()})

    def test_lite_inject_assembles_singletons(self) -> None:
        injector = inj.create_injector(systevisor_bind_resources(), systevisor_bind_runtime())
        coordinator = injector.provide(SystevisorRuntimeCoordinator)
        self.addCleanup(coordinator.close)

        self.assertIs(coordinator.engine, injector.provide(SystevisorEngine))
        self.assertIs(injector.provide(FdioManager), injector.provide(FdioManager))
        self.assertIs(injector.provide(FdioPoller), injector.provide(FdioPoller))


class TestSystevisorRuntimeIsolation(unittest.TestCase):
    def test_failed_effect_does_not_strand_the_rest_of_the_step(self) -> None:
        class DenyingOnceSignalBackend(SystevisorPosixProcessSignalBackend):
            denials_left = 1

            def send_process(self, lease: SystevisorSignalLease, signal_number: int) -> bool:
                if self.denials_left:
                    self.denials_left -= 1
                    raise PermissionError(errno.EPERM, os.strerror(errno.EPERM))
                return super().send_process(lease, signal_number)

        fixture = SystevisorTestRuntimeFixture(
            process_manager=SystevisorProcessManager(signal_backend=DenyingOnceSignalBackend()),
        )
        self.addCleanup(fixture.close)
        unit = SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('/bin/sleep', '60')),
            restart=SystevisorRestartConfig(start_secs=0.),
            stop=SystevisorStopConfig(timeout_secs=.05),
        )
        snapshot = systevisor_build_config_snapshot(SystevisorConfig(units={'first': unit, 'second': unit}), (), ())
        fixture.coordinator.submit(SystevisorApplySnapshotCommand(snapshot))
        instances = fixture.coordinator.engine.state.instances
        fixture.poll_until(lambda: all(
            instance.process_state is SystevisorProcessState.RUNNING
            for instance in instances.values()
        ))

        # The first stop signal is refused. The second must still be sent, and the refused run is then reached by
        # its ordinary escalation rather than being forgotten.
        fixture.coordinator.submit(SystevisorShutdownCommand())

        self.assertIn('runtime.effect_failed', {event.topic for event in fixture.event_bus.journal()})
        fixture.poll_until(lambda: not fixture.process_manager.has_processes())
        self.assertIsNone(fixture.coordinator.fatal_error)

    def test_unexpected_spawn_failure_is_an_ordinary_start_failure(self) -> None:
        class RefusingModifier(SystevisorChildModifier):
            def parent_prepare(self, context: SystevisorChildContext) -> None:
                raise RuntimeError('resource preparation failed')

        fixture = SystevisorTestRuntimeFixture(
            process_manager=SystevisorProcessManager(child_modifiers=(RefusingModifier(),)),
        )
        self.addCleanup(fixture.close)
        snapshot = systevisor_build_config_snapshot(SystevisorConfig(units={
            'worker': SystevisorUnitConfig(exec=SystevisorExecConfig(argv=('/bin/sleep', '60'))),
        }), (), ())

        fixture.coordinator.submit(SystevisorApplySnapshotCommand(snapshot))

        instance = fixture.coordinator.engine.state.instances[SystevisorInstanceId('worker:0')]
        self.assertEqual(instance.process_state, SystevisorProcessState.BACKOFF)
        self.assertEqual(instance.start_failures, 1)
        self.assertFalse(fixture.process_manager.has_processes())

    def test_engine_failure_is_recorded_and_refuses_further_input(self) -> None:
        class FailingEngine(SystevisorEngine):
            def step(self, engine_input: SystevisorEngineInput, now: float) -> ta.Any:
                raise RuntimeError('engine invariant broken')

        fixture = SystevisorTestRuntimeFixture(engine=FailingEngine())
        self.addCleanup(fixture.close)
        self.assertIsNone(fixture.coordinator.fatal_error)

        with self.assertRaisesRegex(RuntimeError, 'engine invariant broken') as raised:
            fixture.coordinator.submit(SystevisorShutdownCommand())

        self.assertIs(fixture.coordinator.fatal_error, raised.exception)
        with self.assertRaisesRegex(RuntimeError, 'runtime coordinator has failed'):
            fixture.coordinator.submit(SystevisorShutdownCommand())


class TestSystevisorLogRetention(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.manager = SystevisorLogManager(SystevisorEventBus(), SystevisorFakeClock(), retained_runs=1)
        self.manager.configure_manager(SystevisorManagerConfig(child_log_directory=self.temp_dir.name), cleanup=True)
        self.addCleanup(self.manager.close)

    def _run(self, run_id: int) -> ta.Tuple[ta.Any, int]:
        effect = _systevisor_test_runtime_log_effect(
            SystevisorOutputConfig(mode=SystevisorOutputMode.FILE, file=None),
            run_id,
        )
        read_fd, write_fd = os.pipe()
        handler = self.manager.register_process(effect, read_fd, None)[0]
        self.manager.append(effect.run_id, SystevisorLogStream.STDOUT, b'output of run %d' % (run_id,))
        return handler, write_fd

    def _retained(self) -> ta.Sequence[int]:
        return [int(channel.run_id) for channel in self.manager.channels()]

    def _files(self) -> ta.Sequence[str]:
        return sorted(os.listdir(self.temp_dir.name))

    def test_ended_runs_release_their_sinks_and_only_the_newest_are_kept(self) -> None:
        open_fds = len(os.listdir('/dev/fd'))
        for run_id in (1, 2, 3):
            handler, write_fd = self._run(run_id)
            os.close(write_fd)
            handler.on_readable()
            self.assertTrue(handler.closed)
            self.manager.retire_process(SystevisorRunId(run_id))

        self.assertEqual(self._retained(), [3])
        self.assertEqual(self.manager.read(SystevisorRunId(3), SystevisorLogStream.STDOUT, 0).data, b'output of run 3')
        with self.assertRaises(KeyError):
            self.manager.read(SystevisorRunId(2), SystevisorLogStream.STDOUT, 0)
        self.assertEqual(self._files(), ['systevisor-child-worker:0-3-stdout.log'])
        self.assertEqual(len(os.listdir('/dev/fd')), open_fds)

    def test_run_is_kept_while_its_output_is_still_open(self) -> None:
        first_handler, first_write_fd = self._run(1)
        self.addCleanup(os.close, first_write_fd)
        self.manager.retire_process(SystevisorRunId(1))
        for run_id in (2, 3):
            handler, write_fd = self._run(run_id)
            os.close(write_fd)
            handler.on_readable()
            self.manager.retire_process(SystevisorRunId(run_id))

        # Something still holds the first run's pipe, so it can still produce output and keeps its place and file.
        self.assertEqual(self._retained(), [1, 3])
        self.manager.append(SystevisorRunId(1), SystevisorLogStream.STDOUT, b' and more')
        with open(os.path.join(self.temp_dir.name, 'systevisor-child-worker:0-1-stdout.log'), 'rb') as log_file:
            self.assertEqual(log_file.read(), b'output of run 1 and more')

        first_handler.close()
        self.assertEqual(self._retained(), [3])

    def test_unreadable_pipe_ends_its_channel_but_a_handling_fault_does_not_hide_there(self) -> None:
        handler, write_fd = self._run(1)
        self.addCleanup(os.close, write_fd)

        with self.assertRaises(ValueError):
            handler.on_error(ValueError('fault while handling output'))
        self.assertFalse(handler.closed)

        handler.on_error(OSError(errno.EIO, os.strerror(errno.EIO)))
        self.assertTrue(handler.closed)
        self.manager.retire_process(SystevisorRunId(1))
        self.assertEqual(self._retained(), [1])

    def test_running_instance_is_never_evicted_and_retention_is_live(self) -> None:
        handler, write_fd = self._run(1)
        self.addCleanup(os.close, write_fd)
        self.addCleanup(handler.close)
        self.manager.set_retained_runs(0)
        self.assertEqual(self._retained(), [1])

    def test_generated_files_are_kept_when_cleanup_is_disabled(self) -> None:
        self.manager.configure_manager(SystevisorManagerConfig(
            child_log_directory=self.temp_dir.name,
            cleanup_auto_logs=False,
        ), cleanup=True)
        for run_id in (1, 2):
            handler, write_fd = self._run(run_id)
            os.close(write_fd)
            handler.on_readable()
            self.manager.retire_process(SystevisorRunId(run_id))

        self.assertEqual(self._retained(), [2])
        self.assertEqual(self._files(), [
            'systevisor-child-worker:0-1-stdout.log',
            'systevisor-child-worker:0-2-stdout.log',
        ])
