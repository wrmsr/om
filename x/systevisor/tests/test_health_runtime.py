# ruff: noqa: PT009 UP006 UP007 UP045
import os
import socket
import time
import typing as ta
import unittest

from omcore.http.simple.pipelines.handlers import SimpleHttpHandlerServerIoPipelineHandler
from omcore.http.simple.types import SimpleHttpHandlerRequest
from omcore.http.simple.types import SimpleHttpHandlerResponse
from omcore.io.fdio.handlers import ServerSocketFdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.io.fdio.pollers import SelectFdioPoller
from omcore.io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorHealthProbeConfig
from x.systevisor.configs.models import SystevisorHealthProbeKind
from x.systevisor.configs.models import SystevisorHealthRole
from x.systevisor.configs.models import SystevisorRestartConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.core.effects import SystevisorRunHealthProbeEffect
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.engine import SystevisorEngine
from x.systevisor.core.identities import SystevisorHealthCheckId
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.inputs import SystevisorShutdownCommand
from x.systevisor.core.states import SystevisorHealthStatus
from x.systevisor.core.states import SystevisorProcessState
from x.systevisor.runtime.clocks import SystevisorSystemClock
from x.systevisor.runtime.coordinator import SystevisorRuntimeCoordinator
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.runtime.health import SystevisorFdioHealthProbeRunner
from x.systevisor.runtime.logs import SystevisorLogManager
from x.systevisor.runtime.logs import SystevisorLogStream
from x.systevisor.runtime.processes import SystevisorOwnedProcessPurpose
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.tests.fakes import SystevisorFakeClock


_SYSTEVISOR_TEST_HEALTH_RUNTIME_TIMEOUT_SECS = 10.


class SystevisorHealthRuntimeFixture:
    def __init__(self) -> None:
        self.poller = SelectFdioPoller()
        self.fdio_manager = FdioManager(self.poller)
        self.clock = SystevisorSystemClock()
        self.event_bus = SystevisorEventBus()
        self.process_manager = SystevisorProcessManager()
        self.log_manager = SystevisorLogManager(self.event_bus, self.clock)
        self.health_runner = SystevisorFdioHealthProbeRunner(
            self.process_manager,
            self.fdio_manager,
            self.clock,
            self.log_manager,
        )
        self.coordinator = SystevisorRuntimeCoordinator(
            SystevisorEngine(),
            self.process_manager,
            self.fdio_manager,
            self.clock,
            self.event_bus,
            self.log_manager,
            self.health_runner,
        )

    def poll_until(self, predicate: ta.Callable[[], bool]) -> None:
        deadline = time.monotonic() + _SYSTEVISOR_TEST_HEALTH_RUNTIME_TIMEOUT_SECS
        while time.monotonic() < deadline:
            self.coordinator.poll(timeout=.25)
            if predicate():
                return
        raise AssertionError('timed out waiting for health runtime checkpoint')

    def close(self) -> None:
        if self.process_manager.has_processes():
            self.coordinator.submit(SystevisorShutdownCommand())
            self.poll_until(lambda: not self.process_manager.has_processes())
        self.coordinator.close()
        self.poller.close()


class TestSystevisorHealthRuntime(unittest.TestCase):
    def test_log_activity_uses_injected_clock_without_io_waiting(self) -> None:
        poller = SelectFdioPoller()
        self.addCleanup(poller.close)
        fdio_manager = FdioManager(poller)
        clock = SystevisorFakeClock(monotonic=10.)
        event_bus = SystevisorEventBus()
        process_manager = SystevisorProcessManager()
        log_manager = SystevisorLogManager(event_bus, clock)
        runner = SystevisorFdioHealthProbeRunner(process_manager, fdio_manager, clock, log_manager)
        self.addCleanup(runner.close)
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, write_fd)

        probe = SystevisorHealthProbeConfig(
            name='churn',
            role=SystevisorHealthRole.LIVENESS,
            kind=SystevisorHealthProbeKind.LOG_ACTIVITY,
            channel='stdout',
            max_quiet_secs=5.,
        )
        config = SystevisorConfig(units={
            'worker': SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('/bin/true',)),
                health=(probe,),
            ),
        })
        spec = systevisor_build_config_snapshot(config, (), ()).instances[SystevisorInstanceId('worker:0')]
        spawn = SystevisorSpawnProcessEffect(SystevisorRunId(1), spec.instance_id, spec)
        handlers = log_manager.register_process(spawn, read_fd, None)
        self.addCleanup(handlers[0].close)
        log_manager.append(spawn.run_id, SystevisorLogStream.STDOUT, b'checkpoint')
        clock.advance(4.)
        facts: ta.List[ta.Any] = []

        runner.start(SystevisorRunHealthProbeEffect(
            check_id=SystevisorHealthCheckId(1),
            run_id=spawn.run_id,
            instance_id=spawn.instance_id,
            probe=probe,
            spec=spec,
        ), facts.append)

        self.assertEqual(len(facts), 1)
        self.assertTrue(facts[0].success)
        self.assertEqual(facts[0].data['quiet_secs'], 4.)

    def test_command_probe_is_an_owned_child_and_gates_startup(self) -> None:
        fixture = SystevisorHealthRuntimeFixture()
        self.addCleanup(fixture.close)
        probe = SystevisorHealthProbeConfig(
            name='command',
            role=SystevisorHealthRole.STARTUP,
            kind=SystevisorHealthProbeKind.COMMAND,
            argv=('/bin/true',),
        )
        snapshot = systevisor_build_config_snapshot(SystevisorConfig(units={
            'worker': SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('/bin/sleep', '60')),
                restart=SystevisorRestartConfig(start_secs=0.),
                health=(probe,),
            ),
        }), (), ())
        fixture.coordinator.submit(SystevisorApplySnapshotCommand(snapshot))
        instance = fixture.coordinator.engine.state.instances[SystevisorInstanceId('worker:0')]

        def started() -> bool:
            return instance.process_state is SystevisorProcessState.RUNNING

        saw_owned_health_command = False
        deadline = time.monotonic() + _SYSTEVISOR_TEST_HEALTH_RUNTIME_TIMEOUT_SECS
        while time.monotonic() < deadline and not started():
            fixture.coordinator.poll(timeout=.1)
            saw_owned_health_command = saw_owned_health_command or any(
                state.purpose is SystevisorOwnedProcessPurpose.HEALTH_COMMAND
                for state in fixture.process_manager.snapshot_states()
            )
        self.assertTrue(started())
        self.assertTrue(saw_owned_health_command)
        self.assertEqual(instance.health['command'].status, SystevisorHealthStatus.PASSING)
        self.assertTrue(all(state.run_id > 0 for state in fixture.process_manager.snapshot_states()))

    def test_tcp_and_pipeline_http_probes_drive_readiness(self) -> None:
        fixture = SystevisorHealthRuntimeFixture()
        self.addCleanup(fixture.close)
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 0))
        port = ta.cast(ta.Tuple[str, int], server_socket.getsockname())[1]
        connections: ta.Set[IoPipelineDriverSocketFdioHandler] = set()

        def handle_request(request: SimpleHttpHandlerRequest) -> SimpleHttpHandlerResponse:
            return SimpleHttpHandlerResponse(status=204, data=b'')

        def connected(sock: socket.socket, address: ta.Any) -> None:
            connection = IoPipelineDriverSocketFdioHandler(
                sock,
                address,
                SimpleHttpHandlerServerIoPipelineHandler.build_standard_pipeline_spec(
                    sock,
                    address,
                    handle_request,
                ),
            )
            self.assertIsNone(connection.next())
            fixture.fdio_manager.register(connection)
            connections.add(connection)

        server = ServerSocketFdioHandler(server_socket, connected)
        fixture.fdio_manager.register(server)
        self.addCleanup(server.close)

        probes = (
            SystevisorHealthProbeConfig(
                name='socket',
                role=SystevisorHealthRole.READINESS,
                kind=SystevisorHealthProbeKind.TCP,
                host='127.0.0.1',
                port=port,
            ),
            SystevisorHealthProbeConfig(
                name='http',
                role=SystevisorHealthRole.READINESS,
                kind=SystevisorHealthProbeKind.HTTP,
                url=f'http://127.0.0.1:{port}/ready?full=1',
                expected_statuses=(204,),
            ),
            SystevisorHealthProbeConfig(
                name='owned',
                role=SystevisorHealthRole.LIVENESS,
                kind=SystevisorHealthProbeKind.PROCESS,
            ),
        )
        snapshot = systevisor_build_config_snapshot(SystevisorConfig(units={
            'web': SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('/bin/sleep', '60')),
                restart=SystevisorRestartConfig(start_secs=0.),
                health=probes,
            ),
        }), (), ())
        fixture.coordinator.submit(SystevisorApplySnapshotCommand(snapshot))
        instance = fixture.coordinator.engine.state.instances[SystevisorInstanceId('web:0')]
        fixture.poll_until(lambda: instance.ready)

        self.assertEqual(
            {name: health.status for name, health in instance.health.items()},
            {
                'socket': SystevisorHealthStatus.PASSING,
                'http': SystevisorHealthStatus.PASSING,
                'owned': SystevisorHealthStatus.PASSING,
            },
        )
        for connection in connections:
            connection.close()
