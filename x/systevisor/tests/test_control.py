# ruff: noqa: PT009 UP006 UP007 UP045
import json
import os
import pathlib
import socket
import tempfile
import time
import typing as ta
import unittest

from omcore.http.pipelines.requests import FullIoPipelineHttpRequest
from omcore.io.fdio.manager import FdioManager
from omcore.io.fdio.pollers import SelectFdioPoller
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from x.systevisor.configs.compiling import SystevisorConfigCompiler
from x.systevisor.configs.diagnostics import SystevisorConfigDiagnosticStage
from x.systevisor.configs.models import SystevisorApiConfig
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.control.api import SystevisorApiApplication
from x.systevisor.control.api import SystevisorApiRequest
from x.systevisor.control.api import SystevisorApiResponse
from x.systevisor.control.api import SystevisorApiStreamResponse
from x.systevisor.control.client import SystevisorApiClient
from x.systevisor.control.client import SystevisorApiClientIoPipelineHandler
from x.systevisor.control.configs import SystevisorConfigController
from x.systevisor.control.http import SystevisorHttpConnectionIoPipelineHandler
from x.systevisor.control.http import SystevisorHttpServer
from x.systevisor.control.jsoncodec import SystevisorJsonCodec
from x.systevisor.control.operations import SystevisorOperationStatus
from x.systevisor.control.operations import SystevisorOperationStore
from x.systevisor.control.plane import SystevisorControlPlane
from x.systevisor.control.service import SystevisorControlService
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.engine import SystevisorEngine
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.states import SystevisorProcessState
from x.systevisor.runtime.clocks import SystevisorSystemClock
from x.systevisor.runtime.coordinator import SystevisorRuntimeCoordinator
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.runtime.health import SystevisorFdioHealthProbeRunner
from x.systevisor.runtime.logs import SystevisorLogManager
from x.systevisor.runtime.logs import SystevisorLogStream
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.scheduling.runtime import SystevisorJsonScheduleStateStore
from x.systevisor.scheduling.runtime import SystevisorScheduler


class SystevisorControlTestFixture:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        self.config_path = root / 'systevisor.json'
        self.state_directory = root / 'state'
        self.config_path.write_text(json.dumps({
            'manager': {'state_directory': str(self.state_directory)},
            'api': {'event_backlog': 32, 'stream_queue_bytes': 4096},
            'units': {
                'idle': {
                    'exec': {'argv': ['/bin/true']},
                    'autostart': False,
                    'kind': 'oneshot',
                    'restart': {'start_secs': 0},
                },
            },
            'collections': {
                'stack': {'units': ['idle']},
            },
            'schedules': {
                'annual': {
                    'cron': '0 0 1 1 *',
                    'action': {'kind': 'restart', 'target_kind': 'unit', 'target': 'idle'},
                },
            },
        }))
        self.poller = SelectFdioPoller()
        self.fdio_manager = FdioManager(self.poller)
        self.clock = SystevisorSystemClock()
        self.event_bus = SystevisorEventBus()
        self.process_manager = SystevisorProcessManager()
        self.log_manager = SystevisorLogManager(self.event_bus, self.clock)
        self.health_probe_runner = SystevisorFdioHealthProbeRunner(
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
            self.health_probe_runner,
        )
        self.codec = SystevisorJsonCodec()
        self.config_controller = SystevisorConfigController(
            SystevisorConfigCompiler(),
            self.coordinator,
            self.clock,
            self.codec,
            (str(self.config_path),),
        )
        self.operations = SystevisorOperationStore(self.event_bus, self.clock)
        self.control = SystevisorControlService(
            self.coordinator,
            self.config_controller,
            self.operations,
        )
        self.scheduler = SystevisorScheduler(
            self.config_controller,
            self.control,
            self.clock,
            self.fdio_manager,
            self.event_bus,
            SystevisorJsonScheduleStateStore(),
        )
        self.application = SystevisorApiApplication(
            self.control,
            self.config_controller,
            self.event_bus,
            self.log_manager,
            self.codec,
            self.scheduler,
        )

    def close(self) -> None:
        self.scheduler.close()
        self.control.close()
        self.config_controller.close()
        self.coordinator.close()
        self.poller.close()


class TestSystevisorControl(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fixture = SystevisorControlTestFixture(pathlib.Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.fixture.close()
        self.temp_dir.cleanup()

    def test_transactional_reload_retains_active_snapshot_and_persists_diagnostics(self) -> None:
        initial = self.fixture.config_controller.reload(initial=True)
        self.assertTrue(initial.attempt.applied)
        assert initial.snapshot is not None
        active_digest = initial.snapshot.digest

        self.fixture.config_path.write_text('{broken json')
        rejected = self.fixture.config_controller.reload('bad-reload')

        self.assertFalse(rejected.attempt.valid)
        self.assertFalse(rejected.attempt.applied)
        active = self.fixture.config_controller.active_snapshot
        self.assertIsNotNone(active)
        assert active is not None
        self.assertEqual(active.digest, active_digest)
        status = json.loads((self.fixture.state_directory / 'config-status.json').read_text())
        self.assertFalse(status['valid'])
        self.assertEqual(status['request_id'], 'bad-reload')
        self.assertEqual(status['diagnostics'][0]['stage'], 'parse')

    def test_runtime_prepare_failure_rejects_snapshot_before_process_reconciliation(self) -> None:
        occupied_path = str(self.fixture.root / 'occupied.sock')
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as occupied_socket:
            occupied_socket.bind(occupied_path)
            occupied_socket.listen(1)
            self.fixture.config_path.write_text(json.dumps({
                'api': {'unix_socket': occupied_path},
                'units': {
                    'would-start': {
                        'exec': {'argv': ['/bin/true']},
                    },
                },
            }))
            server = SystevisorHttpServer(self.fixture.fdio_manager, self.fixture.application)
            control_plane = SystevisorControlPlane(self.fixture.config_controller, server)
            self.addCleanup(control_plane.close)

            result = self.fixture.config_controller.reload(initial=True)

        self.assertFalse(result.attempt.applied)
        self.assertEqual(result.attempt.diagnostics[0].stage, SystevisorConfigDiagnosticStage.PREPARE)
        self.assertIsNone(self.fixture.coordinator.engine.state.snapshot)
        self.assertFalse(self.fixture.process_manager.has_processes())

    def test_control_rejection_is_a_completed_operation(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        operation = self.fixture.control.set_unit('missing', True)

        self.assertIs(operation.status, SystevisorOperationStatus.REJECTED)
        self.assertIn('unknown unit', operation.message or '')
        self.assertTrue(any(event.topic == 'operation.completed' for event in self.fixture.event_bus.journal()))

    def test_oneshot_start_operation_completes_from_observed_exit(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        operation = self.fixture.control.set_unit('idle', True)
        deadline = time.monotonic() + 5.
        while operation.status is SystevisorOperationStatus.PENDING and time.monotonic() < deadline:
            self.fixture.coordinator.poll(timeout=.5)

        self.assertIs(operation.status, SystevisorOperationStatus.SUCCEEDED)
        self.assertFalse(self.fixture.process_manager.has_processes())

    def test_collection_operation_waits_for_ready_and_is_visible_in_api(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        operation = self.fixture.control.set_collection('stack', True)
        deadline = time.monotonic() + 5.
        while operation.status is SystevisorOperationStatus.PENDING and time.monotonic() < deadline:
            self.fixture.coordinator.poll(timeout=.5)

        self.assertIs(operation.status, SystevisorOperationStatus.SUCCEEDED)
        response = self.fixture.application.handle(SystevisorApiRequest('GET', '/v1/collections'))
        self.assertIsInstance(response, SystevisorApiResponse)
        assert isinstance(response, SystevisorApiResponse)
        body = json.loads(response.body)
        self.assertEqual(body['collections'][0]['name'], 'stack')
        self.assertEqual(body['collections'][0]['status'], 'ready')

    def test_json_api_and_event_follow_stream(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        root = self.fixture.application.handle(SystevisorApiRequest('GET', '/'))
        self.assertIsInstance(root, SystevisorApiResponse)
        assert isinstance(root, SystevisorApiResponse)
        self.assertEqual(root.status, 200)
        root_body = json.loads(root.body)
        self.assertEqual(root_body['api_version'], 1)

        schedules = self.fixture.application.handle(SystevisorApiRequest('GET', '/v1/schedules'))
        self.assertIsInstance(schedules, SystevisorApiResponse)
        assert isinstance(schedules, SystevisorApiResponse)
        self.assertEqual(json.loads(schedules.body)['schedules'][0]['name'], 'annual')

        response = self.fixture.application.handle(SystevisorApiRequest(
            'GET',
            '/v1/events?after=0&follow=true&topic=test',
        ))
        self.assertIsInstance(response, SystevisorApiStreamResponse)
        assert isinstance(response, SystevisorApiStreamResponse)
        received: ta.List[bytes] = []
        subscription = response.stream.subscribe(received.append)
        self.fixture.event_bus.publish('ignored', {}, self.fixture.clock.monotonic())
        self.fixture.event_bus.publish(
            'test',
            {'state': SystevisorProcessState.RUNNING},
            self.fixture.clock.monotonic(),
        )
        subscription.close()

        self.assertEqual(len(received), 1)
        self.assertEqual(json.loads(received[0])['payload']['state'], 'running')

    def test_log_back_buffer_and_follow_are_independent_of_event_emission(self) -> None:
        config = SystevisorConfig(units={
            'log': SystevisorUnitConfig(
                exec=SystevisorExecConfig(argv=('/bin/true',)),
                autostart=False,
            ),
        })
        snapshot = systevisor_build_config_snapshot(config, (), ())
        effect = SystevisorSpawnProcessEffect(
            SystevisorRunId(7),
            SystevisorInstanceId('log:0'),
            snapshot.instances[SystevisorInstanceId('log:0')],
        )
        read_fd, write_fd = os.pipe()
        handlers = self.fixture.log_manager.register_process(effect, read_fd, None)
        self.addCleanup(os.close, write_fd)
        self.addCleanup(handlers[0].close)
        self.fixture.log_manager.append(SystevisorRunId(7), SystevisorLogStream.STDOUT, b'old')

        response = self.fixture.application.handle(SystevisorApiRequest(
            'GET',
            '/v1/logs/7/stdout?offset=0&follow=true',
        ))
        self.assertIsInstance(response, SystevisorApiStreamResponse)
        assert isinstance(response, SystevisorApiStreamResponse)
        initial = json.loads(response.stream.initial()[0])
        self.assertEqual(initial['data_base64'], 'b2xk')

        received: ta.List[bytes] = []
        subscription = response.stream.subscribe(received.append)
        self.fixture.log_manager.append(SystevisorRunId(7), SystevisorLogStream.STDOUT, b'new')
        subscription.close()
        self.assertEqual(json.loads(received[0])['data_base64'], 'bmV3')
        self.assertFalse(any(event.topic == 'process.log' for event in self.fixture.event_bus.journal()))

    def test_http_pipeline_streams_incrementally_over_a_socket(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        server_socket, peer_socket = socket.socketpair()
        self.addCleanup(server_socket.close)
        self.addCleanup(peer_socket.close)
        peer_socket.settimeout(1.)
        driver = IoPipelineDriverSocketFdioHandler(
            server_socket,
            '',
            SystevisorHttpConnectionIoPipelineHandler.build_pipeline_spec(
                self.fixture.application,
                4096,
            ),
        )
        self.addCleanup(driver.close)
        driver.next(read=False)

        after_sequence = self.fixture.event_bus.next_sequence - 1
        peer_socket.sendall(
            (
                f'GET /v1/events?after={after_sequence}&follow=true&topic=wire HTTP/1.1\r\n'
                'Host: localhost\r\nConnection: close\r\n\r\n'
            ).encode(),
        )
        driver.on_readable()
        head = peer_socket.recv(65536)
        self.assertIn(b'HTTP/1.1 200 OK', head)
        self.assertIn(b'Transfer-Encoding: chunked', head)

        _, failures = self.fixture.event_bus.publish('wire', {'value': 42}, self.fixture.clock.monotonic())
        self.assertEqual(failures, ())
        driver.next(read=False)
        body = peer_socket.recv(65536)
        self.assertIn(b'"topic":"wire"', body)
        self.assertIn(b'"value":42', body)

    def test_api_client_pipeline_encodes_request_and_decodes_chunked_response(self) -> None:
        handler = SystevisorApiClientIoPipelineHandler(
            FullIoPipelineHttpRequest.simple('localhost', '/v1/state'),
        )
        pipeline = IoPipeline(SystevisorApiClient._pipeline_spec(handler))  # noqa: SLF001
        pipeline.feed_initial_input()
        request_bytes = b''.join(
            bytes(item)
            for item in pipeline.output.drain()
            if isinstance(item, (bytes, bytearray, memoryview))
        )
        self.assertIn(b'GET /v1/state HTTP/1.1', request_bytes)

        pipeline.feed_in(
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n'
            b'7\r\n{"x":1}\r\n0\r\n\r\n',
        )
        self.assertTrue(handler.complete)
        self.assertEqual(handler.status, 200)
        self.assertEqual(b''.join(handler.body_parts), b'{"x":1}')

    def test_unix_socket_server_runs_on_the_shared_fdio_manager(self) -> None:
        self.assertTrue(self.fixture.config_controller.reload(initial=True).attempt.applied)
        socket_path = str(self.fixture.root / 'api.sock')
        server = SystevisorHttpServer(self.fixture.fdio_manager, self.fixture.application)
        server.start(SystevisorApiConfig(unix_socket=socket_path, unix_socket_mode=0o620))
        self.addCleanup(server.close)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(1.)
            client_socket.connect(socket_path)
            client_socket.sendall(b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
            client_socket.setblocking(False)
            response = bytearray()
            deadline = time.monotonic() + 5.
            while time.monotonic() < deadline:
                self.fixture.fdio_manager.poll(timeout=.1)
                try:
                    data = client_socket.recv(65536)
                except BlockingIOError:
                    continue
                if not data:
                    break
                response.extend(data)
            else:
                self.fail('timed out waiting for Unix-socket HTTP response')

        self.assertIn(b'HTTP/1.1 200 OK', response)
        self.assertIn(b'"name":"systevisor"', response)
        self.assertEqual(os.stat(socket_path).st_mode & 0o777, 0o620)
        server.close()
        self.assertFalse(os.path.exists(socket_path))

    def test_http_server_reconfigures_listener_set_without_dropping_retained_socket(self) -> None:
        first_path = str(self.fixture.root / 'first.sock')
        second_path = str(self.fixture.root / 'second.sock')
        server = SystevisorHttpServer(self.fixture.fdio_manager, self.fixture.application)
        self.addCleanup(server.close)
        server.start(SystevisorApiConfig(unix_socket=first_path, unix_socket_mode=0o600))
        first_inode = os.stat(first_path).st_ino

        server.reconfigure(SystevisorApiConfig(unix_socket=first_path, unix_socket_mode=0o660))
        self.assertEqual(os.stat(first_path).st_ino, first_inode)
        self.assertEqual(os.stat(first_path).st_mode & 0o777, 0o660)

        server.reconfigure(SystevisorApiConfig(unix_socket=second_path))
        self.assertFalse(os.path.exists(first_path))
        self.assertTrue(os.path.exists(second_path))

        server.reconfigure(SystevisorApiConfig())
        self.assertFalse(os.path.exists(second_path))

    def test_http_server_never_unlinks_a_non_socket_collision(self) -> None:
        collision_path = self.fixture.root / 'not-a-socket'
        collision_path.write_text('keep me')
        server = SystevisorHttpServer(self.fixture.fdio_manager, self.fixture.application)
        self.addCleanup(server.close)

        with self.assertRaises(OSError):
            server.start(SystevisorApiConfig(unix_socket=str(collision_path)))

        self.assertEqual(collision_path.read_text(), 'keep me')
