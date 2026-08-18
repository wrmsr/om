# @om-lite
# ruff: noqa: UP006 UP007 UP037 UP045
import abc
import dataclasses as dc
import fcntl
import os
import stat
import sys
import tempfile
import typing as ta

from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.lite.abstract import Abstract

from ..configs.marshal import systevisor_marshal_config_obj
from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorSignalScope
from ..configs.validation import systevisor_validate_config
from ..control.configs import SystevisorConfigController
from ..control.jsoncodec import SystevisorJsonCodec
from ..control.operations import SystevisorOperation
from ..control.operations import SystevisorOperationStatus
from ..control.operations import SystevisorOperationStore
from ..core.identities import SystevisorRunId
from ..core.states import SystevisorProcessState
from ..platforms.runtime import SystevisorManagerRuntime
from ..resources.cgroups import SystevisorCgroupManager
from ..resources.sockets import SystevisorInheritedSocketRegistry
from ..runtime.clocks import SystevisorClock
from ..runtime.coordinator import SystevisorInternalProcessCallbacks
from ..runtime.coordinator import SystevisorRuntimeCoordinator
from ..runtime.events import SystevisorEventBus
from ..runtime.logs import SystevisorLogManager
from ..runtime.processes import SystevisorObservedProcessExit
from ..runtime.processes import SystevisorOwnedProcessPurpose
from ..runtime.processes import SystevisorProcessExecResult
from ..runtime.processes import SystevisorProcessManager
from .codec import SystevisorSelfUpdateCodecError
from .codec import systevisor_decode_snapshot
from .codec import systevisor_encode_cgroup_state
from .codec import systevisor_encode_engine_state
from .codec import systevisor_encode_event_bus_state
from .codec import systevisor_encode_inherited_socket
from .codec import systevisor_encode_log_channel_state
from .codec import systevisor_encode_manager_runtime_state
from .codec import systevisor_encode_operation_store_state
from .codec import systevisor_encode_owned_process_state
from .codec import systevisor_handoff_manifest_to_obj
from .codec import systevisor_self_update_atomic_write_json
from .codec import systevisor_self_update_fd
from .codec import systevisor_self_update_is_amalgamated_source
from .codec import systevisor_self_update_probe_request_from_obj
from .codec import systevisor_self_update_probe_request_to_obj
from .codec import systevisor_self_update_probe_result_from_obj
from .codec import systevisor_self_update_probe_result_to_obj
from .codec import systevisor_self_update_read_json
from .codec import systevisor_self_update_source_sha256
from .codec import systevisor_validate_handoff_fds
from .models import SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION
from .models import SystevisorHandoffFd
from .models import SystevisorHandoffFdKind
from .models import SystevisorHandoffManifest
from .models import SystevisorSelfUpdatePhase
from .models import SystevisorSelfUpdateProbeRequest
from .models import SystevisorSelfUpdateProbeResult
from .models import SystevisorSelfUpdateState


_SYSTEVISOR_SELF_UPDATE_INTERNAL_RUN_START = -2_000_000_000


class SystevisorSelfUpdateError(RuntimeError):
    pass


class SystevisorSelfUpdateExecBackend(Abstract):
    @abc.abstractmethod
    def execve(
            self,
            executable: str,
            argv: ta.Sequence[str],
            environment: ta.Mapping[str, str],
    ) -> ta.NoReturn:
        raise NotImplementedError


class SystevisorPosixSelfUpdateExecBackend(SystevisorSelfUpdateExecBackend):
    def execve(
            self,
            executable: str,
            argv: ta.Sequence[str],
            environment: ta.Mapping[str, str],
    ) -> ta.NoReturn:
        os.execve(executable, tuple(argv), dict(environment))


def systevisor_exec_handoff(
        manifest: SystevisorHandoffManifest,
        manifest_path: str,
        backend: SystevisorSelfUpdateExecBackend,
) -> ta.NoReturn:
    if systevisor_self_update_source_sha256(manifest.source_path) != manifest.source_sha256:
        raise SystevisorSelfUpdateError('candidate source changed before exec')
    systevisor_self_update_atomic_write_json(
        manifest_path,
        systevisor_handoff_manifest_to_obj(manifest),
    )
    systevisor_validate_handoff_fds(manifest.fds)
    saved_fd_flags: ta.Dict[int, int] = {}
    try:
        for item in manifest.fds:
            flags = fcntl.fcntl(item.fd, fcntl.F_GETFD)
            saved_fd_flags[item.fd] = flags
            fcntl.fcntl(item.fd, fcntl.F_SETFD, flags & ~fcntl.FD_CLOEXEC)
        backend.execve(
            sys.executable,
            (
                sys.executable,
                manifest.source_path,
                '_self-update-resume',
                '--manifest',
                manifest_path,
            ),
            os.environ,
        )
    except BaseException:
        for fd, flags in saved_fd_flags.items():
            try:
                fcntl.fcntl(fd, fcntl.F_SETFD, flags)
            except OSError:
                pass
        raise


@dc.dataclass
class SystevisorSelfUpdateRequestRuntime:
    operation: SystevisorOperation
    source_path: str
    source_sha256: str
    config_digest: str
    workspace: str
    probe_request_path: str
    probe_result_path: str
    manifest_path: str
    probe_run_id: SystevisorRunId
    requested_at: float
    probe_deadline_at: ta.Optional[float]
    exec_ready: bool = False
    probe_exec_error: ta.Optional[str] = None


class SystevisorSelfUpdateManager(FdioHandler):
    def __init__(
            self,
            coordinator: SystevisorRuntimeCoordinator,
            process_manager: SystevisorProcessManager,
            config_controller: SystevisorConfigController,
            operations: SystevisorOperationStore,
            clock: SystevisorClock,
            fdio_manager: FdioManager,
            json_codec: SystevisorJsonCodec,
            log_manager: SystevisorLogManager,
            event_bus: SystevisorEventBus,
            manager_runtime: SystevisorManagerRuntime,
            inherited_sockets: SystevisorInheritedSocketRegistry,
            cgroup_manager: SystevisorCgroupManager,
            exec_backend: SystevisorSelfUpdateExecBackend,
    ) -> None:
        self._coordinator = coordinator
        self._process_manager = process_manager
        self._config_controller = config_controller
        self._operations = operations
        self._clock = clock
        self._json_codec = json_codec
        self._log_manager = log_manager
        self._event_bus = event_bus
        self._manager_runtime = manager_runtime
        self._inherited_sockets = inherited_sockets
        self._cgroup_manager = cgroup_manager
        self._exec_backend = exec_backend
        self._phase = SystevisorSelfUpdatePhase.IDLE
        self._request: ta.Optional[SystevisorSelfUpdateRequestRuntime] = None
        self._next_internal_run_id = _SYSTEVISOR_SELF_UPDATE_INTERNAL_RUN_START
        self._message: ta.Optional[str] = None
        self._mode = 'serve'
        self._startup_collection: ta.Optional[str] = None
        self._running_source_path = os.path.realpath(sys.argv[0])
        self._closed = False
        fdio_manager.register(self)

    def configure_mode(
            self,
            mode: str,
            startup_collection: ta.Optional[str],
            running_source_path: ta.Optional[str] = None,
    ) -> None:
        if mode not in {'serve', 'run'}:
            raise ValueError(mode)
        if self._request is not None:
            raise RuntimeError('self-update mode cannot change during an update')
        self._mode = mode
        self._startup_collection = startup_collection
        if running_source_path is not None:
            self._running_source_path = os.path.realpath(running_source_path)

    @property
    def state(self) -> SystevisorSelfUpdateState:
        request = self._request
        return SystevisorSelfUpdateState(
            state_schema_version=1,
            phase=self._phase,
            operation_id=None if request is None else request.operation.operation_id,
            source_path=None if request is None else request.source_path,
            source_sha256=None if request is None else request.source_sha256,
            requested_at=None if request is None else request.requested_at,
            probe_run_id=None if request is None else int(request.probe_run_id),
            deadline_at=None if request is None else request.probe_deadline_at,
            message=self._message,
        )

    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return self._closed

    def next_deadline(self) -> ta.Optional[float]:
        if self._closed or self._request is None:
            return None
        return self._request.probe_deadline_at

    def _effective_state_directory(self) -> ta.Optional[str]:
        snapshot = self._config_controller.active_snapshot
        if self._config_controller.state_directory is not None:
            return self._config_controller.state_directory
        if snapshot is not None:
            return snapshot.config.manager.state_directory
        return None

    def _new_workspace(self) -> str:
        state_directory = self._effective_state_directory()
        if state_directory is not None:
            os.makedirs(state_directory, mode=0o700, exist_ok=True)
        return tempfile.mkdtemp(prefix='systevisor-self-update-', dir=state_directory)

    def _stable_issues(self, operation_id: ta.Optional[str] = None) -> ta.Sequence[str]:
        issues = list(self._coordinator.handoff_issues())
        engine_state = self._coordinator.engine.state
        if engine_state.shutting_down:
            issues.append('the manager is shutting down')
        for instance in engine_state.instances.values():
            if instance.process_state in {
                    SystevisorProcessState.STARTING,
                    SystevisorProcessState.STOPPING,
            }:
                issues.append(f'instance {instance.instance_id} is {instance.process_state.value}')
            for health in instance.health.values():
                if health.in_flight_check_id is not None:
                    issues.append(f'health check is in flight for {instance.instance_id}:{health.name}')
        for operation in self._operations.list():
            if (
                    operation.status is SystevisorOperationStatus.PENDING and
                    operation.operation_id != operation_id
            ):
                issues.append(f'operation {operation.operation_id} is pending')
        return tuple(issues)

    def request(self, source_path: str) -> SystevisorOperation:
        operation = self._operations.create('manager.self_update', source_path)
        if self._phase not in {SystevisorSelfUpdatePhase.IDLE, SystevisorSelfUpdatePhase.FAILED}:
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message='another self-update is already active',
            )
            return operation
        snapshot = self._config_controller.active_snapshot
        if snapshot is None:
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message='no active configuration is available',
            )
            return operation
        if not snapshot.config.manager.self_update.enabled:
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message='self-update is disabled by configuration',
            )
            return operation
        issues = self._stable_issues(operation.operation_id)
        if issues:
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message='; '.join(issues),
            )
            return operation

        if not os.path.isabs(source_path):
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message='self-update source path must be absolute',
            )
            return operation
        canonical_source = os.path.realpath(source_path)
        try:
            if not systevisor_self_update_is_amalgamated_source(self._running_source_path):
                raise SystevisorSelfUpdateError(
                    'the running program is not a self-contained amalgamated artifact',
                )
            if not systevisor_self_update_is_amalgamated_source(canonical_source):
                raise SystevisorSelfUpdateError(
                    'candidate source is not a self-contained amalgamated artifact',
                )
            source_stat = os.stat(canonical_source)
            if not stat.S_ISREG(source_stat.st_mode):
                raise SystevisorSelfUpdateError('candidate source is not a regular file')
            source_digest = systevisor_self_update_source_sha256(canonical_source)
            workspace = self._new_workspace()
        except (OSError, SystevisorSelfUpdateError) as exc:
            self._operations.finish(
                operation,
                SystevisorOperationStatus.REJECTED,
                message=f'{type(exc).__name__}: {exc}',
            )
            return operation

        run_id = SystevisorRunId(self._next_internal_run_id)
        self._next_internal_run_id -= 1
        request = SystevisorSelfUpdateRequestRuntime(
            operation=operation,
            source_path=canonical_source,
            source_sha256=source_digest,
            config_digest=snapshot.digest,
            workspace=workspace,
            probe_request_path=os.path.join(workspace, 'probe-request.json'),
            probe_result_path=os.path.join(workspace, 'probe-result.json'),
            manifest_path=os.path.join(workspace, 'handoff.json'),
            probe_run_id=run_id,
            requested_at=self._clock.monotonic(),
            probe_deadline_at=self._clock.monotonic() + snapshot.config.manager.self_update.probe_timeout_secs,
        )
        probe = SystevisorSelfUpdateProbeRequest(
            schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
            source_path=canonical_source,
            source_sha256=source_digest,
            config=systevisor_marshal_config_obj(snapshot.config, SystevisorConfig),
            config_digest=snapshot.digest,
        )
        try:
            systevisor_self_update_atomic_write_json(
                request.probe_request_path,
                systevisor_self_update_probe_request_to_obj(probe),
            )
            self._request = request
            self._phase = SystevisorSelfUpdatePhase.PROBING
            self._message = None
            self._coordinator.start_internal_process(
                run_id,
                (
                    sys.executable,
                    canonical_source,
                    '_self-update-probe',
                    '--request',
                    request.probe_request_path,
                    '--result',
                    request.probe_result_path,
                ),
                SystevisorOwnedProcessPurpose.SELF_UPDATE_PROBE,
                SystevisorInternalProcessCallbacks(self._on_probe_exec, self._on_probe_exit),
            )
        except Exception as exc:  # noqa: BLE001
            self._fail(f'could not start candidate probe: {type(exc).__name__}: {exc}')
        return operation

    def _on_probe_exec(self, result: SystevisorProcessExecResult) -> None:
        if self._closed:
            return
        request = self._request
        if request is None or result.run_id != request.probe_run_id:
            raise SystevisorSelfUpdateError('unexpected candidate exec result')
        if not result.succeeded:
            request.probe_exec_error = result.message or 'candidate exec failed'

    def _on_probe_exit(self, observed: SystevisorObservedProcessExit) -> None:
        if self._closed:
            return
        request = self._request
        if request is None or observed.run_id != request.probe_run_id:
            raise SystevisorSelfUpdateError('unexpected candidate exit')
        if request.probe_exec_error is not None:
            self._fail(request.probe_exec_error)
            return
        if observed.return_code != 0:
            self._fail(f'candidate probe exited with status {observed.return_code}')
            return
        try:
            result = systevisor_self_update_probe_result_from_obj(
                systevisor_self_update_read_json(request.probe_result_path),
            )
            if result.source_sha256 != request.source_sha256:
                raise SystevisorSelfUpdateError('candidate probe returned a different source digest')
            if not result.accepted:
                raise SystevisorSelfUpdateError(result.message or 'candidate rejected the handoff')
            issues = self._stable_issues(request.operation.operation_id)
            if issues:
                raise SystevisorSelfUpdateError('; '.join(issues))
        except Exception as exc:  # noqa: BLE001
            self._fail(f'candidate probe failed: {type(exc).__name__}: {exc}')
            return
        snapshot = self._config_controller.active_snapshot
        if snapshot is None or snapshot.digest != request.config_digest:
            self._fail('active configuration changed during candidate probe')
            return
        self._phase = SystevisorSelfUpdatePhase.PREPARED
        request.probe_deadline_at = self._clock.monotonic() + snapshot.config.manager.self_update.response_grace_secs
        self._event_bus.publish('self_update.prepared', self.state, self._clock.monotonic())

    def on_timeout(self) -> None:
        request = self._request
        if request is None or request.probe_deadline_at is None:
            return
        if self._phase is SystevisorSelfUpdatePhase.PROBING:
            request.probe_deadline_at = None
            try:
                self._process_manager.signal(request.probe_run_id, 'KILL', SystevisorSignalScope.PROCESS)
            except Exception as exc:  # noqa: BLE001
                self._fail(f'candidate probe timeout termination failed: {type(exc).__name__}: {exc}')
            else:
                request.probe_exec_error = 'candidate probe timed out'
        elif self._phase is SystevisorSelfUpdatePhase.PREPARED:
            request.probe_deadline_at = None
            request.exec_ready = True

    def ready_to_exec(self) -> bool:
        return (
            self._phase is SystevisorSelfUpdatePhase.PREPARED and
            self._request is not None and
            self._request.exec_ready
        )

    def _build_manifest(self) -> SystevisorHandoffManifest:
        request = self._request
        snapshot = self._config_controller.active_snapshot
        manager_state = self._manager_runtime.state
        if request is None or snapshot is None or manager_state is None:
            raise SystevisorSelfUpdateError('self-update state is incomplete')
        if snapshot.digest != request.config_digest:
            raise SystevisorSelfUpdateError('active configuration changed during self-update')
        issues = self._stable_issues(request.operation.operation_id)
        if issues:
            raise SystevisorSelfUpdateError('; '.join(issues))
        if systevisor_self_update_source_sha256(request.source_path) != request.source_sha256:
            raise SystevisorSelfUpdateError('candidate source changed after probing')
        try:
            previous_source_stat = os.stat(self._running_source_path)
        except OSError as exc:
            raise SystevisorSelfUpdateError(f'cannot inspect running source: {exc}') from exc
        if not stat.S_ISREG(previous_source_stat.st_mode):
            raise SystevisorSelfUpdateError('running source is not a regular file')
        previous_source_digest = systevisor_self_update_source_sha256(self._running_source_path)

        output_fds = {
            (output.run_id, output.stream): output.fd
            for output in self._coordinator.snapshot_output_fds()
        }
        log_states = self._log_manager.snapshot_states()
        logs = tuple(
            systevisor_encode_log_channel_state(state, output_fds.get((state.run_id, state.stream)))
            for state in log_states
        )
        active_log_keys = {
            (state.run_id, state.stream)
            for state in log_states
            if not state.retired
        }
        if not set(output_fds).issubset(active_log_keys):
            raise SystevisorSelfUpdateError('an output descriptor has no active log channel')

        fds: ta.List[SystevisorHandoffFd] = []
        for process in self._process_manager.snapshot_states():
            if process.pidfd is not None:
                fds.append(systevisor_self_update_fd(
                    SystevisorHandoffFdKind.PROCESS_PIDFD,
                    str(int(process.run_id)),
                    process.pidfd,
                ))
        for (run_id, stream), fd in sorted(output_fds.items(), key=lambda item: (int(item[0][0]), item[0][1].value)):
            fds.append(systevisor_self_update_fd(
                (
                    SystevisorHandoffFdKind.PROCESS_STDOUT
                    if stream.value == 'stdout' else
                    SystevisorHandoffFdKind.PROCESS_STDERR
                ),
                str(int(run_id)),
                fd,
            ))
        pid_file_fd = self._manager_runtime.pid_file_fd
        if pid_file_fd is not None:
            fds.append(systevisor_self_update_fd(SystevisorHandoffFdKind.PID_FILE, 'manager', pid_file_fd))
        for name, inherited in sorted(self._inherited_sockets.sockets.items()):
            fds.append(systevisor_self_update_fd(
                SystevisorHandoffFdKind.ACTIVATION_SOCKET,
                name,
                inherited.fd,
            ))
        systevisor_validate_handoff_fds(fds)

        return SystevisorHandoffManifest(
            schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
            source_path=request.source_path,
            source_sha256=request.source_sha256,
            previous_source_path=self._running_source_path,
            previous_source_sha256=previous_source_digest,
            created_at=self._clock.monotonic(),
            manager_pid=os.getpid(),
            operation_id=request.operation.operation_id,
            mode=self._mode,
            startup_collection=self._startup_collection,
            config_paths=self._config_controller.paths,
            recursive=self._config_controller.recursive,
            state_directory=self._config_controller.state_directory,
            config=systevisor_marshal_config_obj(snapshot.config, SystevisorConfig),
            config_digest=snapshot.digest,
            source_paths=snapshot.source_paths,
            provenance=tuple({
                'object_path': list(item.object_path),
                'source': item.source,
            } for item in snapshot.provenance),
            engine=systevisor_encode_engine_state(self._coordinator.engine.state),
            processes=tuple(
                systevisor_encode_owned_process_state(state)
                for state in self._process_manager.snapshot_states()
            ),
            logs=logs,
            event_bus=systevisor_encode_event_bus_state(
                self._event_bus.snapshot_state(),
                self._json_codec.to_obj,
            ),
            operations=systevisor_encode_operation_store_state(
                self._operations.snapshot_state(),
                self._json_codec.to_obj,
            ),
            manager_runtime=systevisor_encode_manager_runtime_state(manager_state),
            inherited_sockets=tuple(
                systevisor_encode_inherited_socket(inherited)
                for _, inherited in sorted(self._inherited_sockets.sockets.items())
            ),
            cgroups=tuple(
                systevisor_encode_cgroup_state(state)
                for _, state in sorted(self._cgroup_manager.states.items())
            ),
            fds=tuple(fds),
        )

    def execute_prepared(self) -> ta.NoReturn:
        request = self._request
        if request is None or not self.ready_to_exec():
            raise SystevisorSelfUpdateError('self-update is not ready to execute')
        try:
            manifest = self._build_manifest()
            self._phase = SystevisorSelfUpdatePhase.EXECUTING
            systevisor_exec_handoff(manifest, request.manifest_path, self._exec_backend)
        except BaseException as exc:
            self._fail(f'self-update exec failed: {type(exc).__name__}: {exc}')
            raise SystevisorSelfUpdateError(self._message or 'self-update exec failed') from exc

    def _cleanup_workspace(self) -> None:
        request = self._request
        if request is None:
            return
        for path in (request.probe_request_path, request.probe_result_path, request.manifest_path):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        try:
            os.rmdir(request.workspace)
        except OSError:
            pass

    def _fail(self, message: str) -> None:
        request = self._request
        self._phase = SystevisorSelfUpdatePhase.FAILED
        self._message = message
        if request is not None:
            request.probe_deadline_at = None
            self._operations.finish(
                request.operation,
                SystevisorOperationStatus.FAILED,
                message=message,
            )
        self._event_bus.publish('self_update.failed', self.state, self._clock.monotonic())
        self._cleanup_workspace()

    def complete_resume(self, operation_id: str, source_sha256: str) -> None:
        operation = self._operations.get(operation_id)
        if operation is None or operation.kind != 'manager.self_update':
            raise SystevisorSelfUpdateError(f'self-update operation was not restored: {operation_id}')
        if operation.status is not SystevisorOperationStatus.PENDING:
            raise SystevisorSelfUpdateError(f'self-update operation is not pending: {operation_id}')
        self._operations.finish(
            operation,
            SystevisorOperationStatus.SUCCEEDED,
            data={'source_sha256': source_sha256, 'manager_pid': os.getpid()},
        )
        self._event_bus.publish('self_update.completed', {
            'operation_id': operation_id,
            'source_sha256': source_sha256,
        }, self._clock.monotonic())

    def fail_resume(self, operation_id: str, message: str) -> None:
        operation = self._operations.get(operation_id)
        if operation is None or operation.kind != 'manager.self_update':
            raise SystevisorSelfUpdateError(f'self-update operation was not restored: {operation_id}')
        if operation.status is not SystevisorOperationStatus.PENDING:
            raise SystevisorSelfUpdateError(f'self-update operation is not pending: {operation_id}')
        self._operations.finish(operation, SystevisorOperationStatus.FAILED, message=message)
        self._event_bus.publish('self_update.rolled_back', {
            'operation_id': operation_id,
            'message': message,
        }, self._clock.monotonic())

    def close(self) -> None:
        self._closed = True
        request = self._request
        if self._phase is SystevisorSelfUpdatePhase.PROBING and request is not None:
            message = 'manager closed during the candidate probe'
            try:
                self._process_manager.signal(request.probe_run_id, 'KILL', SystevisorSignalScope.PROCESS)
            except Exception as exc:  # noqa: BLE001
                message += f'; probe termination failed: {type(exc).__name__}: {exc}'
            self._fail(message)
        elif self._phase is SystevisorSelfUpdatePhase.PREPARED:
            self._fail('manager closed before the prepared self-update executed')


def systevisor_run_self_update_probe(
        request_path: str,
        result_path: str,
        current_source_path: str,
) -> int:
    source_digest = ''
    try:
        request = systevisor_self_update_probe_request_from_obj(
            systevisor_self_update_read_json(request_path),
        )
        current_source = os.path.realpath(current_source_path)
        if current_source != request.source_path:
            raise SystevisorSelfUpdateCodecError(
                f'candidate source path mismatch: {current_source!r} != {request.source_path!r}',
            )
        source_digest = systevisor_self_update_source_sha256(current_source)
        if source_digest != request.source_sha256:
            raise SystevisorSelfUpdateCodecError('candidate source digest mismatch')
        snapshot = systevisor_decode_snapshot(request.config, request.config_digest, ())
        diagnostics = systevisor_validate_config(snapshot.config)
        if diagnostics:
            raise SystevisorSelfUpdateCodecError(
                '; '.join(f'{diagnostic.code}: {diagnostic.message}' for diagnostic in diagnostics),
            )
        result = SystevisorSelfUpdateProbeResult(
            schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
            accepted=True,
            source_sha256=source_digest,
        )
        exit_code = 0
    except Exception as exc:  # noqa: BLE001
        result = SystevisorSelfUpdateProbeResult(
            schema_version=SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION,
            accepted=False,
            source_sha256=source_digest,
            message=f'{type(exc).__name__}: {exc}',
        )
        exit_code = 2
    try:
        systevisor_self_update_atomic_write_json(
            result_path,
            systevisor_self_update_probe_result_to_obj(result),
        )
    except OSError:
        return 2
    return exit_code
