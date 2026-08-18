# ruff: noqa: PT009 UP006 UP007 UP045
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
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorOutputConfig
from x.systevisor.configs.models import SystevisorOutputMode
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorScheduleDeadlineEffect
from x.systevisor.core.engine import SystevisorEngine
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.states import SystevisorDeadlineKind
from x.systevisor.core.states import SystevisorProcessState
from x.systevisor.runtime.clocks import SystevisorSystemClock
from x.systevisor.runtime.coordinator import SystevisorRuntimeCoordinator
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.runtime.fdio import SystevisorDeadlineFdioHandler
from x.systevisor.runtime.health import SystevisorFdioHealthProbeRunner
from x.systevisor.runtime.inject import systevisor_bind_runtime
from x.systevisor.runtime.logs import SystevisorByteRingBuffer
from x.systevisor.runtime.logs import SystevisorLogManager
from x.systevisor.runtime.logs import SystevisorLogStream
from x.systevisor.runtime.logs import SystevisorRotatingFileLogSink
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.runtime.signals import SystevisorSignalFdioHandler
from x.systevisor.tests.fakes import SystevisorFakeClock


_SYSTEVISOR_TEST_RUNTIME_TIMEOUT_SECS = 10.


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
        injector = inj.create_injector(systevisor_bind_runtime())
        coordinator = injector.provide(SystevisorRuntimeCoordinator)
        self.addCleanup(coordinator.close)

        self.assertIs(coordinator.engine, injector.provide(SystevisorEngine))
        self.assertIs(injector.provide(FdioManager), injector.provide(FdioManager))
        self.assertIs(injector.provide(FdioPoller), injector.provide(FdioPoller))
