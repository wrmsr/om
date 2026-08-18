# @om-lite
# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import fcntl
import os
import sys
import typing as ta

from ..configs.snapshots import SystevisorConfigSnapshot
from ..control.operations import SystevisorOperationStatus
from ..control.operations import SystevisorOperationStoreState
from ..core.state import SystevisorEngineState
from ..platforms.runtime import SystevisorManagerRuntimeState
from ..resources.cgroups import SystevisorCgroupRunState
from ..resources.sockets import SystevisorInheritedSocket
from ..runtime.coordinator import SystevisorRuntimeOutputFd
from ..runtime.events import SystevisorEventBusState
from ..runtime.logs import SystevisorLogChannelState
from ..runtime.logs import SystevisorLogStream
from ..runtime.processes import SystevisorOwnedProcessState
from .codec import SystevisorSelfUpdateCodecError
from .codec import systevisor_decode_cgroup_state
from .codec import systevisor_decode_engine_state
from .codec import systevisor_decode_event_bus_state
from .codec import systevisor_decode_inherited_socket
from .codec import systevisor_decode_log_channel_state
from .codec import systevisor_decode_manager_runtime_state
from .codec import systevisor_decode_operation_store_state
from .codec import systevisor_decode_owned_process_state
from .codec import systevisor_decode_snapshot
from .codec import systevisor_self_update_atomic_write_json
from .codec import systevisor_self_update_source_sha256
from .codec import systevisor_validate_handoff_fds
from .models import SystevisorHandoffFdKind
from .models import SystevisorHandoffManifest


@dc.dataclass(frozen=True)
class SystevisorDecodedHandoff:
    manifest: SystevisorHandoffManifest
    snapshot: SystevisorConfigSnapshot
    engine: SystevisorEngineState
    processes: ta.Sequence[SystevisorOwnedProcessState]
    logs: ta.Sequence[SystevisorLogChannelState]
    output_fds: ta.Sequence[SystevisorRuntimeOutputFd]
    event_bus: SystevisorEventBusState
    operations: SystevisorOperationStoreState
    manager_runtime: SystevisorManagerRuntimeState
    pid_file_fd: ta.Optional[int]
    inherited_sockets: ta.Sequence[SystevisorInheritedSocket]
    cgroups: ta.Sequence[SystevisorCgroupRunState]


def systevisor_decode_handoff(
        manifest: SystevisorHandoffManifest,
        current_source_path: str,
        *,
        previous_source: bool = False,
) -> SystevisorDecodedHandoff:
    current_source = os.path.realpath(current_source_path)
    expected_source = manifest.previous_source_path if previous_source else manifest.source_path
    expected_digest = manifest.previous_source_sha256 if previous_source else manifest.source_sha256
    if current_source != expected_source:
        raise SystevisorSelfUpdateCodecError(
            f'resume source path mismatch: {current_source!r} != {expected_source!r}',
        )
    if systevisor_self_update_source_sha256(current_source) != expected_digest:
        raise SystevisorSelfUpdateCodecError('resume source digest mismatch')
    if manifest.manager_pid != os.getpid():
        raise SystevisorSelfUpdateCodecError(
            f'handoff belongs to manager pid {manifest.manager_pid}, not {os.getpid()}',
        )
    if manifest.mode not in {'serve', 'run'}:
        raise SystevisorSelfUpdateCodecError(f'invalid handoff mode: {manifest.mode!r}')
    if (manifest.mode == 'run') != (manifest.startup_collection is not None):
        raise SystevisorSelfUpdateCodecError('handoff mode and startup collection do not match')
    systevisor_validate_handoff_fds(manifest.fds)

    snapshot = systevisor_decode_snapshot(
        manifest.config,
        manifest.config_digest,
        manifest.source_paths,
        manifest.provenance,
    )
    engine = systevisor_decode_engine_state(manifest.engine, snapshot)
    processes = tuple(systevisor_decode_owned_process_state(value) for value in manifest.processes)

    logs: ta.List[SystevisorLogChannelState] = []
    output_fds: ta.List[SystevisorRuntimeOutputFd] = []
    for value in manifest.logs:
        log_state, fd = systevisor_decode_log_channel_state(value)
        logs.append(log_state)
        if fd is not None:
            output_fds.append(SystevisorRuntimeOutputFd(log_state.run_id, log_state.stream, fd))
    event_bus = systevisor_decode_event_bus_state(manifest.event_bus)
    operations = systevisor_decode_operation_store_state(manifest.operations)
    manager_runtime = systevisor_decode_manager_runtime_state(manifest.manager_runtime)
    inherited_sockets = tuple(
        systevisor_decode_inherited_socket(value)
        for value in manifest.inherited_sockets
    )
    cgroups = tuple(systevisor_decode_cgroup_state(value) for value in manifest.cgroups)

    expected_fds: ta.Dict[ta.Tuple[SystevisorHandoffFdKind, str], int] = {}
    for process in processes:
        if process.pidfd is not None:
            expected_fds[(SystevisorHandoffFdKind.PROCESS_PIDFD, str(int(process.run_id)))] = process.pidfd
    for output in output_fds:
        kind = (
            SystevisorHandoffFdKind.PROCESS_STDOUT
            if output.stream is SystevisorLogStream.STDOUT else
            SystevisorHandoffFdKind.PROCESS_STDERR
        )
        key = (kind, str(int(output.run_id)))
        if key in expected_fds:
            raise SystevisorSelfUpdateCodecError(f'duplicate semantic handoff descriptor: {kind.value}:{key[1]}')
        expected_fds[key] = output.fd
    pid_file_fd: ta.Optional[int] = None
    if manager_runtime.pid_file is not None:
        pid_items = [
            item
            for item in manifest.fds
            if item.kind is SystevisorHandoffFdKind.PID_FILE and item.owner == 'manager'
        ]
        if len(pid_items) != 1:
            raise SystevisorSelfUpdateCodecError('pidfile handoff descriptor is missing or duplicated')
        pid_file_fd = pid_items[0].fd
        expected_fds[(SystevisorHandoffFdKind.PID_FILE, 'manager')] = pid_file_fd
    for inherited in inherited_sockets:
        key = (SystevisorHandoffFdKind.ACTIVATION_SOCKET, inherited.name)
        if key in expected_fds:
            raise SystevisorSelfUpdateCodecError(f'duplicate activation socket: {inherited.name!r}')
        expected_fds[key] = inherited.fd

    actual_fds = {(item.kind, item.owner): item.fd for item in manifest.fds}
    if actual_fds != expected_fds:
        missing = sorted(f'{kind.value}:{owner}' for kind, owner in set(expected_fds) - set(actual_fds))
        extra = sorted(f'{kind.value}:{owner}' for kind, owner in set(actual_fds) - set(expected_fds))
        raise SystevisorSelfUpdateCodecError(
            f'handoff descriptor semantics do not match state; missing={missing!r}; extra={extra!r}',
        )

    update_operation = next(
        (operation for operation in operations.operations if operation.operation_id == manifest.operation_id),
        None,
    )
    if (
            update_operation is None or
            update_operation.kind != 'manager.self_update' or
            update_operation.status is not SystevisorOperationStatus.PENDING
    ):
        raise SystevisorSelfUpdateCodecError('pending self-update operation is absent from handoff')

    return SystevisorDecodedHandoff(
        manifest=manifest,
        snapshot=snapshot,
        engine=engine,
        processes=processes,
        logs=tuple(logs),
        output_fds=tuple(output_fds),
        event_bus=event_bus,
        operations=operations,
        manager_runtime=manager_runtime,
        pid_file_fd=pid_file_fd,
        inherited_sockets=inherited_sockets,
        cgroups=cgroups,
    )


def systevisor_restore_handoff_cloexec(handoff: SystevisorDecodedHandoff) -> None:
    systevisor_validate_handoff_fds(handoff.manifest.fds)
    for item in handoff.manifest.fds:
        flags = fcntl.fcntl(item.fd, fcntl.F_GETFD)
        fcntl.fcntl(item.fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)


def systevisor_cleanup_handoff_files(manifest_path: str) -> None:
    workspace = os.path.dirname(os.path.abspath(manifest_path))
    for name in ('probe-request.json', 'probe-result.json', 'resume-error.json', 'handoff.json'):
        path = os.path.join(workspace, name)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    try:
        os.rmdir(workspace)
    except OSError:
        pass


def systevisor_rollback_handoff(
        manifest: SystevisorHandoffManifest,
        manifest_path: str,
        message: str,
) -> ta.NoReturn:
    if systevisor_self_update_source_sha256(
            manifest.previous_source_path,
    ) != manifest.previous_source_sha256:
        raise SystevisorSelfUpdateCodecError('previous source changed before rollback')
    error_path = os.path.join(os.path.dirname(os.path.abspath(manifest_path)), 'resume-error.json')
    systevisor_self_update_atomic_write_json(error_path, {'message': message})
    systevisor_validate_handoff_fds(manifest.fds)
    for item in manifest.fds:
        flags = fcntl.fcntl(item.fd, fcntl.F_GETFD)
        fcntl.fcntl(item.fd, fcntl.F_SETFD, flags & ~fcntl.FD_CLOEXEC)
    os.execve(
        sys.executable,
        (
            sys.executable,
            manifest.previous_source_path,
            '_self-update-rollback',
            '--manifest',
            manifest_path,
            '--error-file',
            error_path,
        ),
        os.environ,
    )
