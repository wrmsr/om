# ruff: noqa: PT009 UP006 UP007 UP045
import dataclasses as dc
import os
import socket
import typing as ta
import unittest

from omcore.io.fdio.manager import FdioManager
from omcore.io.fdio.pollers import SelectFdioPoller
from x.systevisor.configs.models import SystevisorCgroupConfig
from x.systevisor.configs.models import SystevisorCgroupManagerConfig
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorManagerConfig
from x.systevisor.configs.models import SystevisorNamespaceConfig
from x.systevisor.configs.models import SystevisorObservationConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.models import SystevisorUnitResourcesConfig
from x.systevisor.configs.snapshots import SystevisorConfigSnapshot
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.configs.validation import systevisor_validate_config
from x.systevisor.core.changes import systevisor_classify_unit_change
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.states import SystevisorUnitChangeKind
from x.systevisor.resources.cgroups import SystevisorCgroupConfig as SystevisorCgroupConfigForType
from x.systevisor.resources.cgroups import SystevisorCgroupCounters
from x.systevisor.resources.cgroups import SystevisorCgroupFs
from x.systevisor.resources.cgroups import SystevisorCgroupManager
from x.systevisor.resources.cgroups import SystevisorCgroupPreparedRun
from x.systevisor.resources.cgroups import SystevisorCgroupRunStatus
from x.systevisor.resources.namespaces import SystevisorNamespaceBackend
from x.systevisor.resources.namespaces import SystevisorNamespaceChildModifier
from x.systevisor.resources.runtime import SystevisorResourceEvent
from x.systevisor.resources.runtime import SystevisorResourceEventKind
from x.systevisor.resources.runtime import SystevisorResourceObserver
from x.systevisor.resources.sampling import SystevisorProcessResourceCounters
from x.systevisor.resources.sampling import SystevisorProcessResourceSampler
from x.systevisor.resources.sampling import SystevisorResourceSampleSource
from x.systevisor.resources.sampling import systevisor_parse_linux_proc_stat
from x.systevisor.resources.sockets import SystevisorInheritedSocketChildModifier
from x.systevisor.resources.sockets import SystevisorInheritedSocketRegistry
from x.systevisor.resources.sockets import SystevisorSocketActivationError
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.runtime.processes import SystevisorChildContext
from x.systevisor.runtime.processes import SystevisorOwnedProcessPurpose
from x.systevisor.runtime.processes import SystevisorOwnedProcessState
from x.systevisor.runtime.processes import SystevisorOwnedProcessStatus
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.runtime.processes import SystevisorResolvedIdentity
from x.systevisor.tests.fakes import SystevisorFakeClock


class SystevisorTestResourceConfigController:
    def __init__(self) -> None:
        self.participants: ta.List[ta.Any] = []

    def add_participant(self, participant: ta.Any) -> None:
        self.participants.append(participant)


class SystevisorTestResourceProcessManager:
    def __init__(self, states: ta.Iterable[SystevisorOwnedProcessState] = ()) -> None:
        self.states = tuple(states)

    def snapshot_states(self) -> ta.Sequence[SystevisorOwnedProcessState]:
        return self.states


class SystevisorTestProcessResourceSampler(SystevisorProcessResourceSampler):
    def __init__(self, responses: ta.Iterable[ta.Union[SystevisorProcessResourceCounters, Exception]]) -> None:
        self.responses = list(responses)

    def sample(self, process: SystevisorOwnedProcessState) -> SystevisorProcessResourceCounters:
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class SystevisorTestCgroupFs(SystevisorCgroupFs):
    def __init__(self) -> None:
        self.validated_roots: ta.List[str] = []
        self.created: ta.List[ta.Tuple[str, str, SystevisorCgroupConfigForType]] = []
        self.read_fds: ta.Dict[str, int] = {}
        self.retire_results: ta.List[ta.Tuple[bool, bool]] = []

    def validate_root(self, root: str, configs: ta.Iterable[SystevisorCgroupConfigForType]) -> None:
        self.validated_roots.append(root)

    def create_run(
            self,
            root: str,
            name: str,
            config: SystevisorCgroupConfigForType,
    ) -> SystevisorCgroupPreparedRun:
        read_fd, write_fd = os.pipe()
        path = f'{root}/{name}'
        self.created.append((root, name, config))
        self.read_fds[path] = read_fd
        return SystevisorCgroupPreparedRun(path=path, procs_fd=write_fd)

    def finish_spawn(self, prepared: SystevisorCgroupPreparedRun) -> None:
        try:
            os.close(prepared.procs_fd)
        except OSError:
            pass

    def abort_run(self, prepared: SystevisorCgroupPreparedRun) -> None:
        self.finish_spawn(prepared)

    def retire_run(self, path: str) -> ta.Tuple[bool, bool]:
        return self.retire_results.pop(0) if self.retire_results else (True, False)

    def sample(self, path: str) -> SystevisorCgroupCounters:
        return SystevisorCgroupCounters(memory_current_bytes=123, populated=True)

    def close(self) -> None:
        for read_fd in self.read_fds.values():
            try:
                os.close(read_fd)
            except OSError:
                pass


class SystevisorTestNamespaceBackend(SystevisorNamespaceBackend):
    def __init__(self) -> None:
        self.calls: ta.List[ta.Tuple[int, bool, ta.Optional[str]]] = []

    def apply(self, flags: int, *, private_mounts: bool, hostname: ta.Optional[str]) -> None:
        self.calls.append((flags, private_mounts, hostname))


def _systevisor_test_resource_snapshot(
        *,
        resources: SystevisorUnitResourcesConfig = SystevisorUnitResourcesConfig(),
        observation: SystevisorObservationConfig = SystevisorObservationConfig(interval_secs=1.),
        cgroup_root: ta.Optional[str] = None,
) -> SystevisorConfigSnapshot:
    return systevisor_build_config_snapshot(SystevisorConfig(
        manager=SystevisorManagerConfig(
            observation=observation,
            cgroups=SystevisorCgroupManagerConfig(root=cgroup_root),
        ),
        units={'service': SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('/bin/true',)),
            autostart=False,
            resources=resources,
        )},
    ), (), ())


def _systevisor_test_owned_process(run_id: int = 1) -> SystevisorOwnedProcessState:
    return SystevisorOwnedProcessState(
        state_schema_version=3,
        run_id=SystevisorRunId(run_id),
        instance_id=SystevisorInstanceId('service:0'),
        pid=4321,
        pidfd=None,
        session_requested=False,
        session_id=None,
        birth_identity='99',
        status=SystevisorOwnedProcessStatus.RUNNING,
        stdout_fd=None,
        stderr_fd=None,
        exec_error_fd=None,
        return_code=None,
        signal_lease_count=0,
        purpose=SystevisorOwnedProcessPurpose.SERVICE,
        health_check_id=None,
        observe_resources=True,
    )


def _systevisor_test_resource_counters(cpu: float, read_bytes: int) -> SystevisorProcessResourceCounters:
    return SystevisorProcessResourceCounters(
        source=SystevisorResourceSampleSource.LINUX_PROCFS,
        birth_identity='99',
        cpu_user_secs=cpu,
        cpu_system_secs=0.,
        memory_rss_bytes=100,
        read_bytes=read_bytes,
        write_bytes=read_bytes * 2,
    )


class TestSystevisorResourceSampling(unittest.TestCase):
    def test_proc_stat_parser_handles_parentheses_and_field_offsets(self) -> None:
        fields = ['0'] * 50
        fields[0] = 'S'
        fields[7] = '12'
        fields[9] = '3'
        fields[11] = '100'
        fields[12] = '25'
        fields[17] = '4'
        fields[19] = '98765'
        fields[20] = '4096'
        fields[21] = '7'

        parsed = systevisor_parse_linux_proc_stat(f'123 (a ) name) {" ".join(fields)}', 123)

        self.assertEqual(parsed.birth_identity, '98765')
        self.assertEqual(parsed.cpu_user_ticks, 100)
        self.assertEqual(parsed.cpu_system_ticks, 25)
        self.assertEqual(parsed.rss_pages, 7)
        self.assertEqual(parsed.thread_count, 4)
        self.assertEqual(parsed.minor_faults, 12)
        self.assertEqual(parsed.major_faults, 3)

    def test_observer_computes_rates_and_reports_failure_recovery_without_sleep(self) -> None:
        clock = SystevisorFakeClock(monotonic=10., wall_time=1000.)
        process_manager = SystevisorTestResourceProcessManager((_systevisor_test_owned_process(),))
        sampler = SystevisorTestProcessResourceSampler((
            _systevisor_test_resource_counters(1., 100),
            _systevisor_test_resource_counters(1.5, 300),
            RuntimeError('injected sample failure'),
            _systevisor_test_resource_counters(2., 500),
        ))
        cgroup_fs = SystevisorTestCgroupFs()
        cgroup_manager = SystevisorCgroupManager(cgroup_fs)
        config_controller = SystevisorTestResourceConfigController()
        poller = SelectFdioPoller()
        fdio_manager = FdioManager(poller)
        event_bus = SystevisorEventBus()
        observer = SystevisorResourceObserver(
            ta.cast(ta.Any, config_controller),
            ta.cast(SystevisorProcessManager, process_manager),
            sampler,
            cgroup_manager,
            SystevisorInheritedSocketRegistry(environment={}, consume_environment=False),
            clock,
            fdio_manager,
            event_bus,
        )
        self.addCleanup(observer.close)
        self.addCleanup(poller.close)
        self.addCleanup(cgroup_fs.close)
        observer.prepare(_systevisor_test_resource_snapshot()).commit()

        observer.on_timeout()
        clock.advance(1.)
        observer.on_timeout()
        second = observer.states[SystevisorRunId(1)]
        assert second.sample is not None
        self.assertEqual(second.sample.rates.cpu_percent, 50.)
        self.assertEqual(second.sample.rates.read_bytes_per_sec, 200.)
        self.assertEqual(second.sample.rates.write_bytes_per_sec, 400.)

        clock.advance(1.)
        observer.on_timeout()
        failed = observer.states[SystevisorRunId(1)]
        self.assertEqual(failed.consecutive_failures, 1)
        self.assertIn('injected sample failure', failed.last_error or '')

        clock.advance(1.)
        observer.on_timeout()
        recovered = observer.states[SystevisorRunId(1)]
        self.assertEqual(recovered.consecutive_failures, 0)
        resource_kinds = tuple(
            ta.cast(SystevisorResourceEvent, event.payload).kind
            for event in event_bus.journal()
            if event.topic == 'resource'
        )
        self.assertIn(SystevisorResourceEventKind.FAILED, resource_kinds)
        self.assertIn(SystevisorResourceEventKind.RECOVERED, resource_kinds)

        process_manager.states = ()
        clock.advance(1.)
        observer.on_timeout()
        self.assertFalse(observer.states[SystevisorRunId(1)].active)
        self.assertEqual(observer.states[SystevisorRunId(1)].ended_at, clock.monotonic())

    def test_unknown_inherited_socket_rejects_candidate_before_activation(self) -> None:
        snapshot = _systevisor_test_resource_snapshot(
            resources=SystevisorUnitResourcesConfig(inherited_sockets=('missing',)),
        )
        controller = SystevisorTestResourceConfigController()
        poller = SelectFdioPoller()
        fdio_manager = FdioManager(poller)
        observer = SystevisorResourceObserver(
            ta.cast(ta.Any, controller),
            ta.cast(SystevisorProcessManager, SystevisorTestResourceProcessManager()),
            SystevisorTestProcessResourceSampler(()),
            SystevisorCgroupManager(SystevisorTestCgroupFs()),
            SystevisorInheritedSocketRegistry(environment={}, consume_environment=False),
            SystevisorFakeClock(),
            fdio_manager,
            SystevisorEventBus(),
        )
        self.addCleanup(observer.close)
        self.addCleanup(poller.close)

        with self.assertRaises(SystevisorSocketActivationError):
            observer.prepare(snapshot)


class TestSystevisorIsolationCapabilities(unittest.TestCase):
    def test_cgroup_join_uses_prepared_fd_and_never_a_numeric_control_target(self) -> None:
        resources = SystevisorUnitResourcesConfig(cgroup=SystevisorCgroupConfig(
            enabled=True,
            cpu_weight=100,
            memory_max_bytes=1024,
            pids_max=8,
        ))
        snapshot = _systevisor_test_resource_snapshot(resources=resources, cgroup_root='/delegated')
        fs = SystevisorTestCgroupFs()
        self.addCleanup(fs.close)
        manager = SystevisorCgroupManager(fs)
        wakes: ta.List[bool] = []
        manager.set_wake_callback(lambda: wakes.append(True))
        manager.prepare_config(snapshot)
        manager.commit_config()
        spec = snapshot.instances[SystevisorInstanceId('service:0')]
        context = SystevisorChildContext(
            run_id=SystevisorRunId(7),
            instance_id=spec.instance_id,
            spec=spec,
            identity=SystevisorResolvedIdentity(None, None, None, None, None),
            environment={},
        )

        manager.parent_prepare(context)
        [procs_fd] = manager.preserved_fds(context)
        path = next(iter(fs.read_fds))
        read_fd = fs.read_fds[path]
        self.assertGreaterEqual(procs_fd, 0)
        manager.before_identity(context)
        self.assertEqual(os.read(read_fd, 16), b'0\n')
        manager.parent_spawned(context, 7654)
        self.assertEqual(manager.states[SystevisorRunId(7)].status, SystevisorCgroupRunStatus.ACTIVE)
        self.assertEqual(manager.states[SystevisorRunId(7)].pid, 7654)

        fs.retire_results.extend(((False, True), (True, False)))
        manager.parent_retired(context)
        self.assertEqual(
            manager.states[SystevisorRunId(7)].status,
            SystevisorCgroupRunStatus.RETIRED_POPULATED,
        )
        self.assertEqual(wakes, [True])
        manager.sweep()
        self.assertEqual(manager.states[SystevisorRunId(7)].status, SystevisorCgroupRunStatus.REMOVED)

    def test_namespace_modifier_is_injected_and_skips_internal_probe_runs(self) -> None:
        namespace = SystevisorNamespaceConfig(mount=True, uts=True, network=True, hostname='isolated')
        snapshot = _systevisor_test_resource_snapshot(
            resources=SystevisorUnitResourcesConfig(namespaces=namespace),
        )
        spec = snapshot.instances[SystevisorInstanceId('service:0')]
        backend = SystevisorTestNamespaceBackend()
        modifier = SystevisorNamespaceChildModifier(backend)
        context = SystevisorChildContext(
            run_id=SystevisorRunId(3),
            instance_id=spec.instance_id,
            spec=spec,
            identity=SystevisorResolvedIdentity(None, None, None, None, None),
            environment={},
        )

        modifier.before_identity(context)
        self.assertEqual(len(backend.calls), 1)
        flags, private_mounts, hostname = backend.calls[0]
        self.assertNotEqual(flags, 0)
        self.assertTrue(private_mounts)
        self.assertEqual(hostname, 'isolated')

        modifier.before_identity(dc.replace(context, run_id=SystevisorRunId(-1)))
        self.assertEqual(len(backend.calls), 1)

    def test_systemd_socket_adoption_duplicates_only_named_capabilities(self) -> None:
        inherited_socket, peer_socket = socket.socketpair()
        self.addCleanup(inherited_socket.close)
        self.addCleanup(peer_socket.close)
        inherited_fd = os.dup(inherited_socket.fileno())
        environment = {
            'LISTEN_PID': str(os.getpid()),
            'LISTEN_FDS': '1',
            'LISTEN_FDNAMES': 'api',
        }
        registry = SystevisorInheritedSocketRegistry(
            environment,
            fd_start=inherited_fd,
            consume_environment=False,
        )
        self.addCleanup(registry.close)
        resources = SystevisorUnitResourcesConfig(inherited_sockets=('api',))
        snapshot = _systevisor_test_resource_snapshot(resources=resources)
        spec = snapshot.instances[SystevisorInstanceId('service:0')]
        context = SystevisorChildContext(
            run_id=SystevisorRunId(8),
            instance_id=spec.instance_id,
            spec=spec,
            identity=SystevisorResolvedIdentity(None, None, None, None, None),
            environment={},
        )
        modifier = SystevisorInheritedSocketChildModifier(registry)

        modifier.parent_prepare(context)
        [source_fd] = modifier.preserved_fds(context)
        self.assertGreaterEqual(source_fd, 64)
        self.assertEqual(modifier.reserved_child_fds(context), (3,))
        self.assertEqual(modifier.child_environment(context)['LISTEN_FDNAMES'], 'api')
        modifier.parent_spawn_failed(context)
        with self.assertRaises(OSError):
            os.fstat(source_fd)

        with self.assertRaises(SystevisorSocketActivationError):
            registry.require(('missing',))

    def test_resource_validation_and_change_classification_are_explicit(self) -> None:
        invalid = SystevisorConfig(units={'bad': SystevisorUnitConfig(
            exec=SystevisorExecConfig(argv=('/bin/true',)),
            resources=SystevisorUnitResourcesConfig(
                cgroup=SystevisorCgroupConfig(enabled=True, cpu_weight=20_000),
                namespaces=SystevisorNamespaceConfig(hostname='missing-uts'),
            ),
        )})
        codes = {diagnostic.code for diagnostic in systevisor_validate_config(invalid)}
        self.assertIn('missing_cgroup_root', codes)
        self.assertIn('invalid_cgroup_cpu_weight', codes)
        self.assertIn('namespace_hostname_without_uts', codes)

        original = SystevisorUnitConfig(exec=SystevisorExecConfig(argv=('/bin/true',)))
        observed = dc.replace(original, resources=dc.replace(original.resources, observe=False))
        isolated = dc.replace(
            original,
            resources=dc.replace(
                original.resources,
                namespaces=SystevisorNamespaceConfig(mount=True),
            ),
        )
        self.assertIs(systevisor_classify_unit_change(original, observed).kind, SystevisorUnitChangeKind.LIVE)
        self.assertIs(systevisor_classify_unit_change(original, isolated).kind, SystevisorUnitChangeKind.RESTART)
