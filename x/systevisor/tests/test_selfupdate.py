# ruff: noqa: PT009 UP006 UP007 UP045
import argparse
import dataclasses as dc
import fcntl
import json
import os
import pathlib
import tempfile
import time
import typing as ta
import unittest

from x.systevisor.configs.marshal import systevisor_marshal_config_obj
from x.systevisor.configs.models import SystevisorConfig
from x.systevisor.configs.models import SystevisorExecConfig
from x.systevisor.configs.models import SystevisorManagerConfig
from x.systevisor.configs.models import SystevisorUnitConfig
from x.systevisor.configs.snapshots import SystevisorConfigSnapshot
from x.systevisor.configs.snapshots import systevisor_build_config_snapshot
from x.systevisor.control.jsoncodec import SystevisorJsonCodec
from x.systevisor.control.operations import SystevisorOperation
from x.systevisor.control.operations import SystevisorOperationStatus
from x.systevisor.control.operations import SystevisorOperationStoreState
from x.systevisor.core.effects import SystevisorSpawnProcessEffect
from x.systevisor.core.identities import SystevisorInstanceId
from x.systevisor.core.identities import SystevisorRunId
from x.systevisor.core.inputs import SystevisorApplySnapshotCommand
from x.systevisor.core.inputs import SystevisorSpawnSucceededFact
from x.systevisor.core.state import SystevisorEngineState
from x.systevisor.main import SystevisorMainServerContext
from x.systevisor.platforms.runtime import SystevisorManagerRuntimeState
from x.systevisor.platforms.runtime import SystevisorProcessBootstrapState
from x.systevisor.runtime.events import SystevisorEventBus
from x.systevisor.runtime.processes import SystevisorProcessManager
from x.systevisor.selfupdate.codec import SystevisorSelfUpdateCodecError
from x.systevisor.selfupdate.codec import systevisor_decode_engine_state
from x.systevisor.selfupdate.codec import systevisor_decode_snapshot
from x.systevisor.selfupdate.codec import systevisor_encode_engine_state
from x.systevisor.selfupdate.codec import systevisor_encode_event_bus_state
from x.systevisor.selfupdate.codec import systevisor_encode_manager_runtime_state
from x.systevisor.selfupdate.codec import systevisor_encode_operation_store_state
from x.systevisor.selfupdate.codec import systevisor_handoff_manifest_from_obj
from x.systevisor.selfupdate.codec import systevisor_handoff_manifest_to_obj
from x.systevisor.selfupdate.codec import systevisor_self_update_atomic_write_json
from x.systevisor.selfupdate.codec import systevisor_self_update_fd
from x.systevisor.selfupdate.codec import systevisor_self_update_is_amalgamated_source
from x.systevisor.selfupdate.codec import systevisor_self_update_read_json
from x.systevisor.selfupdate.codec import systevisor_self_update_source_sha256
from x.systevisor.selfupdate.codec import systevisor_validate_handoff_fds
from x.systevisor.selfupdate.models import SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION
from x.systevisor.selfupdate.models import SystevisorHandoffFdKind
from x.systevisor.selfupdate.models import SystevisorHandoffManifest
from x.systevisor.selfupdate.models import SystevisorSelfUpdatePhase
from x.systevisor.selfupdate.restore import systevisor_decode_handoff
from x.systevisor.selfupdate.runtime import SystevisorSelfUpdateExecBackend
from x.systevisor.selfupdate.runtime import systevisor_exec_handoff
from x.systevisor.tests.fakes import SystevisorEngineHarness


def _systevisor_test_self_update_snapshot() -> SystevisorConfigSnapshot:
    config = SystevisorConfig(units={
        'worker': SystevisorUnitConfig(exec=SystevisorExecConfig(argv=('worker',))),
    })
    return systevisor_build_config_snapshot(config, ('config/worker.yml',), ())


class SystevisorTestSelfUpdateExecBackend(SystevisorSelfUpdateExecBackend):
    def __init__(self, inherited_fd: int) -> None:
        self._inherited_fd = inherited_fd
        self.called = False

    def execve(
            self,
            executable: str,
            argv: ta.Sequence[str],
            environment: ta.Mapping[str, str],
    ) -> ta.NoReturn:
        self.called = True
        if not os.get_inheritable(self._inherited_fd):
            raise AssertionError('handoff descriptor was not made inheritable')
        raise OSError('injected exec failure')


class TestSystevisorSelfUpdateCodec(unittest.TestCase):
    def test_engine_state_round_trip_preserves_stable_run(self) -> None:
        snapshot = _systevisor_test_self_update_snapshot()
        harness = SystevisorEngineHarness()
        output = harness.submit(SystevisorApplySnapshotCommand(snapshot))
        spawn = next(effect for effect in output.effects if isinstance(effect, SystevisorSpawnProcessEffect))
        harness.submit(SystevisorSpawnSucceededFact(spawn.run_id))

        encoded = systevisor_encode_engine_state(harness.engine.state)
        decoded_snapshot = systevisor_decode_snapshot(
            systevisor_marshal_config_obj(snapshot.config, SystevisorConfig),
            snapshot.digest,
            snapshot.source_paths,
        )
        decoded = systevisor_decode_engine_state(encoded, decoded_snapshot)

        self.assertEqual(decoded, harness.engine.state)
        self.assertEqual(decoded.instances[SystevisorInstanceId('worker:0')].run_id, SystevisorRunId(1))

    def test_manifest_json_round_trip_is_strict_and_atomic(self) -> None:
        snapshot = _systevisor_test_self_update_snapshot()
        manifest = SystevisorHandoffManifest(
            schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
            source_path='/opt/systevisor.py',
            source_sha256='a' * 64,
            previous_source_path='/opt/previous-systevisor.py',
            previous_source_sha256='b' * 64,
            created_at=12.5,
            manager_pid=123,
            operation_id='op-00000001',
            mode='serve',
            startup_collection=None,
            config_paths=('config',),
            recursive=True,
            state_directory='/state',
            config=systevisor_marshal_config_obj(snapshot.config, SystevisorConfig),
            config_digest=snapshot.digest,
            source_paths=snapshot.source_paths,
            provenance=(),
            engine={},
            processes=(),
            logs=(),
            event_bus={},
            operations={},
            manager_runtime={},
            inherited_sockets=(),
            cgroups=(),
            fds=(),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, 'handoff.json')
            systevisor_self_update_atomic_write_json(path, systevisor_handoff_manifest_to_obj(manifest))
            restored = systevisor_handoff_manifest_from_obj(systevisor_self_update_read_json(path))
            self.assertEqual(restored, manifest)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)

        bad = dict(systevisor_handoff_manifest_to_obj(manifest))
        bad['schema_version'] = 999
        with self.assertRaisesRegex(SystevisorSelfUpdateCodecError, 'unsupported handoff schema'):
            systevisor_handoff_manifest_from_obj(bad)

    def test_only_generated_amalgamations_are_update_artifacts(self) -> None:
        artifact = pathlib.Path(__file__).parent.parent / '_bin' / 'systevisor.py'
        self.assertTrue(systevisor_self_update_is_amalgamated_source(str(artifact)))
        self.assertFalse(systevisor_self_update_is_amalgamated_source(__file__))

    def test_fd_inventory_detects_duplicates_and_substitution(self) -> None:
        read_fd, write_fd = os.pipe()
        replacement_read_fd = -1
        try:
            item = systevisor_self_update_fd(SystevisorHandoffFdKind.PROCESS_STDOUT, 'run:1', read_fd)
            systevisor_validate_handoff_fds((item,))
            with self.assertRaisesRegex(SystevisorSelfUpdateCodecError, 'listed more than once'):
                systevisor_validate_handoff_fds((item, dc.replace(item, owner='run:2')))

            os.close(read_fd)
            replacement_read_fd = os.open(os.devnull, os.O_RDONLY)
            if replacement_read_fd != item.fd:
                os.dup2(replacement_read_fd, item.fd)
            with self.assertRaisesRegex(SystevisorSelfUpdateCodecError, 'identity changed'):
                systevisor_validate_handoff_fds((item,))
        finally:
            for fd in {read_fd, write_fd, replacement_read_fd}:
                if fd >= 0:
                    try:
                        os.close(fd)
                    except OSError:
                        pass

    def test_fd_inventory_records_status_flags(self) -> None:
        read_fd, write_fd = os.pipe()
        try:
            os.set_blocking(read_fd, False)
            item = systevisor_self_update_fd(SystevisorHandoffFdKind.PROCESS_STDOUT, 'run:1', read_fd)
            self.assertTrue(item.status_flags & os.O_NONBLOCK)
            fcntl.fcntl(read_fd, fcntl.F_SETFL, item.status_flags & ~os.O_NONBLOCK)
            with self.assertRaisesRegex(SystevisorSelfUpdateCodecError, 'identity changed'):
                systevisor_validate_handoff_fds((item,))
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_exec_failure_restores_cloexec_exactly(self) -> None:
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        self.addCleanup(os.close, write_fd)
        os.set_inheritable(read_fd, False)
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, 'candidate.py')
            with open(source_path, 'w') as source_file:
                source_file.write('print("candidate")\n')
            manifest = SystevisorHandoffManifest(
                schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
                source_path=source_path,
                source_sha256=systevisor_self_update_source_sha256(source_path),
                previous_source_path=source_path,
                previous_source_sha256=systevisor_self_update_source_sha256(source_path),
                created_at=1.,
                manager_pid=os.getpid(),
                operation_id='op-00000001',
                mode='serve',
                startup_collection=None,
                config_paths=(),
                recursive=False,
                state_directory=None,
                config={},
                config_digest='',
                source_paths=(),
                provenance=(),
                engine={},
                processes=(),
                logs=(),
                event_bus={},
                operations={},
                manager_runtime={},
                inherited_sockets=(),
                cgroups=(),
                fds=(systevisor_self_update_fd(
                    SystevisorHandoffFdKind.PROCESS_STDOUT,
                    '1',
                    read_fd,
                ),),
            )
            backend = SystevisorTestSelfUpdateExecBackend(read_fd)

            with self.assertRaisesRegex(OSError, 'injected exec failure'):
                systevisor_exec_handoff(manifest, os.path.join(temp_dir, 'handoff.json'), backend)

            self.assertTrue(backend.called)
            self.assertFalse(os.get_inheritable(read_fd))

    def test_semantic_handoff_decode_accepts_only_pending_update(self) -> None:
        config = SystevisorConfig(manager=SystevisorManagerConfig(process_title=None))
        snapshot = systevisor_build_config_snapshot(config, (), ())
        event_bus = SystevisorEventBus()
        event_bus.publish('before-update', {'ok': True}, 1.)
        operation = SystevisorOperation(
            operation_id='op-00000001',
            kind='manager.self_update',
            target='/candidate.py',
            created_at=1.,
            status=SystevisorOperationStatus.PENDING,
        )
        operations = SystevisorOperationStoreState(1, 16, 2, (operation,))
        manager_state = SystevisorManagerRuntimeState(
            bootstrap=SystevisorProcessBootstrapState(
                pid=os.getpid(),
                is_pid_one=os.getpid() == 1,
                subreaper_enabled=False,
                systemd_notify=False,
                launchd_job=False,
            ),
            config=config.manager,
            pid_file=None,
            ready=True,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, 'candidate.py')
            with open(source_path, 'w') as source_file:
                source_file.write('print("candidate")\n')
            manifest = SystevisorHandoffManifest(
                schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
                source_path=source_path,
                source_sha256=systevisor_self_update_source_sha256(source_path),
                previous_source_path=source_path,
                previous_source_sha256=systevisor_self_update_source_sha256(source_path),
                created_at=1.,
                manager_pid=os.getpid(),
                operation_id=operation.operation_id,
                mode='serve',
                startup_collection=None,
                config_paths=(),
                recursive=False,
                state_directory=None,
                config=systevisor_marshal_config_obj(config, SystevisorConfig),
                config_digest=snapshot.digest,
                source_paths=(),
                provenance=(),
                engine=systevisor_encode_engine_state(SystevisorEngineState(snapshot=snapshot)),
                processes=(),
                logs=(),
                event_bus=systevisor_encode_event_bus_state(
                    event_bus.snapshot_state(),
                    SystevisorJsonCodec().to_obj,
                ),
                operations=systevisor_encode_operation_store_state(
                    operations,
                    SystevisorJsonCodec().to_obj,
                ),
                manager_runtime=systevisor_encode_manager_runtime_state(manager_state),
                inherited_sockets=(),
                cgroups=(),
                fds=(),
            )

            decoded = systevisor_decode_handoff(manifest, source_path)
            self.assertEqual(decoded.snapshot.digest, snapshot.digest)
            self.assertEqual(decoded.event_bus.next_sequence, 2)
            rolled_back = systevisor_decode_handoff(manifest, source_path, previous_source=True)
            self.assertEqual(rolled_back.manifest.operation_id, operation.operation_id)

            rejected = dc.replace(
                manifest,
                operations=systevisor_encode_operation_store_state(
                    dc.replace(
                        operations,
                        operations=(dc.replace(operation, status=SystevisorOperationStatus.SUCCEEDED),),
                    ),
                    SystevisorJsonCodec().to_obj,
                ),
            )
            with self.assertRaisesRegex(SystevisorSelfUpdateCodecError, 'pending self-update operation'):
                systevisor_decode_handoff(rejected, source_path)


class TestSystevisorSelfUpdateRuntime(unittest.TestCase):
    def test_amalgamated_candidate_probe_is_owned_and_sleepless(self) -> None:
        artifact = pathlib.Path(__file__).parent.parent / '_bin' / 'systevisor.py'
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = pathlib.Path(temp_dir) / 'config.json'
            config_path.write_text(json.dumps({
                'manager': {
                    'process_title': None,
                    'subreaper': False,
                    'min_fds': 0,
                    'min_procs': 0,
                    'state_directory': temp_dir,
                    'log': {'stderr': False},
                    'observation': {'enabled': False},
                    'self_update': {'response_grace_secs': 60},
                },
            }))
            context = SystevisorMainServerContext(argparse.Namespace(
                config=[str(config_path)],
                recursive=False,
                state_directory=temp_dir,
            ))
            try:
                started = context.start(context.compile())
                self.assertTrue(started.attempt.applied)
                manager = context.self_update
                coordinator = context.coordinator
                process_manager = context._injector.provide(SystevisorProcessManager)  # noqa: SLF001
                assert manager is not None
                assert coordinator is not None
                manager.configure_mode('serve', None, str(artifact))
                operation = manager.request(str(artifact))
                deadline = time.monotonic() + 10.
                while manager.state.phase is SystevisorSelfUpdatePhase.PROBING:
                    if time.monotonic() >= deadline:
                        self.fail('timed out waiting for managed candidate probe')
                    coordinator.poll(timeout=1.)

                self.assertEqual(manager.state.phase, SystevisorSelfUpdatePhase.PREPARED, manager.state.message)
                self.assertEqual(operation.status, SystevisorOperationStatus.PENDING)
                self.assertEqual(process_manager.handoff_issues(), ())
            finally:
                context.close()
