# @om-lite
# ruff: noqa: UP006 UP007 UP037 UP045
import base64
import dataclasses as dc
import fcntl
import hashlib
import json
import os
import stat
import tempfile
import typing as ta

from ..configs.marshal import systevisor_marshal_config_obj
from ..configs.marshal import systevisor_unmarshal_config
from ..configs.models import SystevisorCgroupConfig
from ..configs.models import SystevisorConfig
from ..configs.models import SystevisorHealthRole
from ..configs.models import SystevisorManagerConfig
from ..configs.models import SystevisorOutputConfig
from ..configs.models import SystevisorUnitConfig
from ..configs.snapshots import SystevisorConfigSnapshot
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from ..configs.snapshots import systevisor_build_config_snapshot
from ..configs.sources import SystevisorConfigProvenance
from ..control.operations import SystevisorOperation
from ..control.operations import SystevisorOperationStatus
from ..control.operations import SystevisorOperationStoreState
from ..core.identities import SystevisorCollectionName
from ..core.identities import SystevisorHealthCheckId
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..core.identities import SystevisorUnitName
from ..core.state import SystevisorCollectionState
from ..core.state import SystevisorEngineState
from ..core.state import SystevisorHealthProbeState
from ..core.state import SystevisorInstanceState
from ..core.states import SystevisorCollectionStatus
from ..core.states import SystevisorDeadlineKind
from ..core.states import SystevisorDesiredOrigin
from ..core.states import SystevisorDesiredState
from ..core.states import SystevisorHealthStatus
from ..core.states import SystevisorProcessState
from ..platforms.runtime import SystevisorManagerRuntimeState
from ..platforms.runtime import SystevisorPidFileState
from ..platforms.runtime import SystevisorProcessBootstrapState
from ..resources.cgroups import SystevisorCgroupRunState
from ..resources.cgroups import SystevisorCgroupRunStatus
from ..resources.sockets import SystevisorInheritedSocket
from ..runtime.events import SystevisorBusEvent
from ..runtime.events import SystevisorEventBusState
from ..runtime.logs import SystevisorLogChannelState
from ..runtime.logs import SystevisorLogStream
from ..runtime.processes import SystevisorOwnedProcessPurpose
from ..runtime.processes import SystevisorOwnedProcessState
from ..runtime.processes import SystevisorOwnedProcessStatus
from .models import SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION
from .models import SystevisorHandoffFd
from .models import SystevisorHandoffFdKind
from .models import SystevisorHandoffManifest
from .models import SystevisorSelfUpdateProbeRequest
from .models import SystevisorSelfUpdateProbeResult


_SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES = 64 * 1024 * 1024


class SystevisorSelfUpdateCodecError(ValueError):
    pass


def _systevisor_self_update_mapping(value: ta.Any, name: str) -> ta.Mapping[str, ta.Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise SystevisorSelfUpdateCodecError(f'{name} must be an object')
    return ta.cast(ta.Mapping[str, ta.Any], value)


def _systevisor_self_update_sequence(value: ta.Any, name: str) -> ta.Sequence[ta.Any]:
    if not isinstance(value, list):
        raise SystevisorSelfUpdateCodecError(f'{name} must be an array')
    return value


def _systevisor_self_update_string(value: ta.Any, name: str) -> str:
    if not isinstance(value, str):
        raise SystevisorSelfUpdateCodecError(f'{name} must be a string')
    return value


def _systevisor_self_update_optional_string(value: ta.Any, name: str) -> ta.Optional[str]:
    if value is None:
        return None
    return _systevisor_self_update_string(value, name)


def _systevisor_self_update_int(value: ta.Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SystevisorSelfUpdateCodecError(f'{name} must be an integer')
    return value


def _systevisor_self_update_optional_int(value: ta.Any, name: str) -> ta.Optional[int]:
    if value is None:
        return None
    return _systevisor_self_update_int(value, name)


def _systevisor_self_update_float(value: ta.Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SystevisorSelfUpdateCodecError(f'{name} must be a number')
    return float(value)


def _systevisor_self_update_optional_float(value: ta.Any, name: str) -> ta.Optional[float]:
    if value is None:
        return None
    return _systevisor_self_update_float(value, name)


def _systevisor_self_update_bool(value: ta.Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise SystevisorSelfUpdateCodecError(f'{name} must be a boolean')
    return value


def _systevisor_self_update_enum(
        enum_type: ta.Type[ta.Any],
        value: ta.Any,
        name: str,
) -> ta.Any:
    raw = _systevisor_self_update_string(value, name)
    try:
        return enum_type(raw)
    except ValueError as exc:
        raise SystevisorSelfUpdateCodecError(f'invalid {name}: {raw!r}') from exc


def systevisor_self_update_source_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as source_file:
        while True:
            chunk = source_file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def systevisor_self_update_is_amalgamated_source(path: str) -> bool:
    try:
        with open(path, 'rb') as source_file:
            header = source_file.read(4096)
    except OSError:
        return False
    return b'# @om-generated' in header and b'# @om-amalg-output ' in header


def systevisor_self_update_fd(
        kind: SystevisorHandoffFdKind,
        owner: str,
        fd: int,
) -> SystevisorHandoffFd:
    if fd < 3:
        raise SystevisorSelfUpdateCodecError(f'cannot hand off reserved descriptor {fd}')
    fd_stat = os.fstat(fd)
    return SystevisorHandoffFd(
        kind=kind,
        owner=owner,
        fd=fd,
        device=fd_stat.st_dev,
        inode=fd_stat.st_ino,
        mode=fd_stat.st_mode,
        status_flags=fcntl.fcntl(fd, fcntl.F_GETFL),
    )


def systevisor_validate_handoff_fds(fds: ta.Iterable[SystevisorHandoffFd]) -> None:
    seen_fds: ta.Set[int] = set()
    seen_owners: ta.Set[ta.Tuple[SystevisorHandoffFdKind, str]] = set()
    for item in fds:
        if item.fd < 3:
            raise SystevisorSelfUpdateCodecError(f'handoff contains reserved descriptor {item.fd}')
        if item.fd in seen_fds:
            raise SystevisorSelfUpdateCodecError(f'handoff descriptor is listed more than once: {item.fd}')
        owner_key = (item.kind, item.owner)
        if owner_key in seen_owners:
            raise SystevisorSelfUpdateCodecError(
                f'handoff owner is listed more than once: {item.kind.value}:{item.owner}',
            )
        seen_fds.add(item.fd)
        seen_owners.add(owner_key)
        try:
            fd_stat = os.fstat(item.fd)
            status_flags = fcntl.fcntl(item.fd, fcntl.F_GETFL)
        except OSError as exc:
            raise SystevisorSelfUpdateCodecError(
                f'handoff descriptor is not open: {item.kind.value}:{item.owner}:{item.fd}',
            ) from exc
        if (
                fd_stat.st_dev != item.device or
                fd_stat.st_ino != item.inode or
                stat.S_IFMT(fd_stat.st_mode) != stat.S_IFMT(item.mode) or
                status_flags != item.status_flags
        ):
            raise SystevisorSelfUpdateCodecError(
                f'handoff descriptor identity changed: {item.kind.value}:{item.owner}:{item.fd}',
            )


def _systevisor_self_update_encode_spec(spec: SystevisorDesiredInstanceSpec) -> ta.Mapping[str, ta.Any]:
    return {
        'instance_id': spec.instance_id,
        'unit_name': spec.unit_name,
        'slot': spec.slot,
        'spec_digest': spec.spec_digest,
        'unit': systevisor_marshal_config_obj(spec.unit, SystevisorUnitConfig),
    }


def _systevisor_self_update_decode_spec(value: ta.Any) -> SystevisorDesiredInstanceSpec:
    obj = _systevisor_self_update_mapping(value, 'desired spec')
    unit = systevisor_unmarshal_config(obj.get('unit'), SystevisorUnitConfig)
    return SystevisorDesiredInstanceSpec(
        instance_id=SystevisorInstanceId(_systevisor_self_update_string(obj.get('instance_id'), 'instance id')),
        unit_name=SystevisorUnitName(_systevisor_self_update_string(obj.get('unit_name'), 'unit name')),
        slot=_systevisor_self_update_int(obj.get('slot'), 'slot'),
        spec_digest=_systevisor_self_update_string(obj.get('spec_digest'), 'spec digest'),
        unit=unit,
    )


def _systevisor_self_update_encode_health(state: SystevisorHealthProbeState) -> ta.Mapping[str, ta.Any]:
    return {
        'name': state.name,
        'role': state.role.value,
        'config_digest': state.config_digest,
        'status': state.status.value,
        'consecutive_successes': state.consecutive_successes,
        'consecutive_failures': state.consecutive_failures,
        'last_started_at': state.last_started_at,
        'last_completed_at': state.last_completed_at,
        'last_success_at': state.last_success_at,
        'last_message': state.last_message,
        'last_data': dict(state.last_data),
        'scheduled_deadline_id': state.scheduled_deadline_id,
        'next_check_at': state.next_check_at,
        'in_flight_check_id': state.in_flight_check_id,
        'recovery_applied': state.recovery_applied,
    }


def _systevisor_self_update_decode_health(value: ta.Any) -> SystevisorHealthProbeState:
    obj = _systevisor_self_update_mapping(value, 'health state')
    check_id = _systevisor_self_update_optional_int(obj.get('in_flight_check_id'), 'in-flight check id')
    return SystevisorHealthProbeState(
        name=_systevisor_self_update_string(obj.get('name'), 'health name'),
        role=_systevisor_self_update_enum(SystevisorHealthRole, obj.get('role'), 'health role'),
        config_digest=_systevisor_self_update_string(obj.get('config_digest'), 'health config digest'),
        status=_systevisor_self_update_enum(SystevisorHealthStatus, obj.get('status'), 'health status'),
        consecutive_successes=_systevisor_self_update_int(
            obj.get('consecutive_successes'),
            'consecutive successes',
        ),
        consecutive_failures=_systevisor_self_update_int(
            obj.get('consecutive_failures'),
            'consecutive failures',
        ),
        last_started_at=_systevisor_self_update_optional_float(obj.get('last_started_at'), 'last started at'),
        last_completed_at=_systevisor_self_update_optional_float(
            obj.get('last_completed_at'),
            'last completed at',
        ),
        last_success_at=_systevisor_self_update_optional_float(obj.get('last_success_at'), 'last success at'),
        last_message=_systevisor_self_update_optional_string(obj.get('last_message'), 'last message'),
        last_data=_systevisor_self_update_mapping(obj.get('last_data'), 'last data'),
        scheduled_deadline_id=_systevisor_self_update_optional_int(
            obj.get('scheduled_deadline_id'),
            'scheduled deadline id',
        ),
        next_check_at=_systevisor_self_update_optional_float(obj.get('next_check_at'), 'next check at'),
        in_flight_check_id=None if check_id is None else SystevisorHealthCheckId(check_id),
        recovery_applied=_systevisor_self_update_bool(obj.get('recovery_applied'), 'recovery applied'),
    )


def systevisor_encode_engine_state(state: SystevisorEngineState) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'config_generation': state.config_generation,
        'instances': [
            {
                'instance_id': instance.instance_id,
                'unit_name': instance.unit_name,
                'slot': instance.slot,
                'desired_spec': _systevisor_self_update_encode_spec(instance.desired_spec),
                'desired_state': instance.desired_state.value,
                'desired_origin': instance.desired_origin.value,
                'process_state': instance.process_state.value,
                'run_id': instance.run_id,
                'applied_spec_digest': instance.applied_spec_digest,
                'spawn_confirmed': instance.spawn_confirmed,
                'start_failures': instance.start_failures,
                'started_at': instance.started_at,
                'ready': instance.ready,
                'completed_successfully': instance.completed_successfully,
                'last_return_code': instance.last_return_code,
                'deadline_id': instance.deadline_id,
                'deadline_kind': None if instance.deadline_kind is None else instance.deadline_kind.value,
                'deadline_at': instance.deadline_at,
                'restart_requested': instance.restart_requested,
                'blocked_reason': instance.blocked_reason,
                'start_stable': instance.start_stable,
                'health': [
                    _systevisor_self_update_encode_health(health)
                    for _, health in sorted(instance.health.items())
                ],
            }
            for _, instance in sorted(state.instances.items())
        ],
        'collections': [
            {
                'name': collection.name,
                'desired_active': collection.desired_active,
                'desired_origin': collection.desired_origin.value,
                'status': collection.status.value,
                'activation_sequence': collection.activation_sequence,
                'failure_instance_id': collection.failure_instance_id,
                'failure_reason': collection.failure_reason,
            }
            for _, collection in sorted(state.collections.items())
        ],
        'unit_desired_overrides': dict(state.unit_desired_overrides),
        'startup_collection': state.startup_collection,
        'shutting_down': state.shutting_down,
        'next_run_id': state.next_run_id,
        'next_deadline_id': state.next_deadline_id,
        'event_sequence': state.event_sequence,
        'last_now': state.last_now,
        'next_health_check_id': state.next_health_check_id,
    }


def _systevisor_self_update_decode_instance(value: ta.Any) -> SystevisorInstanceState:
    obj = _systevisor_self_update_mapping(value, 'instance state')
    raw_deadline_kind = obj.get('deadline_kind')
    raw_run_id = _systevisor_self_update_optional_int(obj.get('run_id'), 'run id')
    health = tuple(
        _systevisor_self_update_decode_health(item)
        for item in _systevisor_self_update_sequence(obj.get('health'), 'health states')
    )
    return SystevisorInstanceState(
        instance_id=SystevisorInstanceId(_systevisor_self_update_string(obj.get('instance_id'), 'instance id')),
        unit_name=SystevisorUnitName(_systevisor_self_update_string(obj.get('unit_name'), 'unit name')),
        slot=_systevisor_self_update_int(obj.get('slot'), 'slot'),
        desired_spec=_systevisor_self_update_decode_spec(obj.get('desired_spec')),
        desired_state=_systevisor_self_update_enum(SystevisorDesiredState, obj.get('desired_state'), 'desired state'),
        desired_origin=_systevisor_self_update_enum(
            SystevisorDesiredOrigin,
            obj.get('desired_origin'),
            'desired origin',
        ),
        process_state=_systevisor_self_update_enum(
            SystevisorProcessState,
            obj.get('process_state'),
            'process state',
        ),
        run_id=None if raw_run_id is None else SystevisorRunId(raw_run_id),
        applied_spec_digest=_systevisor_self_update_optional_string(
            obj.get('applied_spec_digest'),
            'applied spec digest',
        ),
        spawn_confirmed=_systevisor_self_update_bool(obj.get('spawn_confirmed'), 'spawn confirmed'),
        start_failures=_systevisor_self_update_int(obj.get('start_failures'), 'start failures'),
        started_at=_systevisor_self_update_optional_float(obj.get('started_at'), 'started at'),
        ready=_systevisor_self_update_bool(obj.get('ready'), 'ready'),
        completed_successfully=_systevisor_self_update_bool(
            obj.get('completed_successfully'),
            'completed successfully',
        ),
        last_return_code=_systevisor_self_update_optional_int(obj.get('last_return_code'), 'last return code'),
        deadline_id=_systevisor_self_update_optional_int(obj.get('deadline_id'), 'deadline id'),
        deadline_kind=(
            None if raw_deadline_kind is None else
            _systevisor_self_update_enum(SystevisorDeadlineKind, raw_deadline_kind, 'deadline kind')
        ),
        deadline_at=_systevisor_self_update_optional_float(obj.get('deadline_at'), 'deadline at'),
        restart_requested=_systevisor_self_update_bool(obj.get('restart_requested'), 'restart requested'),
        blocked_reason=_systevisor_self_update_optional_string(obj.get('blocked_reason'), 'blocked reason'),
        start_stable=_systevisor_self_update_bool(obj.get('start_stable'), 'start stable'),
        health={item.name: item for item in health},
    )


def _systevisor_self_update_decode_collection(value: ta.Any) -> SystevisorCollectionState:
    obj = _systevisor_self_update_mapping(value, 'collection state')
    return SystevisorCollectionState(
        name=SystevisorCollectionName(_systevisor_self_update_string(obj.get('name'), 'collection name')),
        desired_active=_systevisor_self_update_bool(obj.get('desired_active'), 'desired active'),
        desired_origin=_systevisor_self_update_enum(
            SystevisorDesiredOrigin,
            obj.get('desired_origin'),
            'desired origin',
        ),
        status=_systevisor_self_update_enum(
            SystevisorCollectionStatus,
            obj.get('status'),
            'collection status',
        ),
        activation_sequence=_systevisor_self_update_int(
            obj.get('activation_sequence'),
            'activation sequence',
        ),
        failure_instance_id=(
            None if obj.get('failure_instance_id') is None else
            SystevisorInstanceId(_systevisor_self_update_string(
                obj.get('failure_instance_id'),
                'failure instance id',
            ))
        ),
        failure_reason=_systevisor_self_update_optional_string(obj.get('failure_reason'), 'failure reason'),
    )


def systevisor_decode_engine_state(
        value: ta.Any,
        snapshot: SystevisorConfigSnapshot,
) -> SystevisorEngineState:
    obj = _systevisor_self_update_mapping(value, 'engine state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'engine schema version')
    if schema_version != 2:
        raise SystevisorSelfUpdateCodecError(f'unsupported engine state schema: {schema_version}')
    instances = tuple(
        _systevisor_self_update_decode_instance(item)
        for item in _systevisor_self_update_sequence(obj.get('instances'), 'instances')
    )
    collections = tuple(
        _systevisor_self_update_decode_collection(item)
        for item in _systevisor_self_update_sequence(obj.get('collections'), 'collections')
    )
    raw_overrides = _systevisor_self_update_mapping(obj.get('unit_desired_overrides'), 'unit desired overrides')
    overrides = {
        SystevisorUnitName(name): _systevisor_self_update_bool(active, f'unit override {name!r}')
        for name, active in raw_overrides.items()
    }
    startup = _systevisor_self_update_optional_string(obj.get('startup_collection'), 'startup collection')
    return SystevisorEngineState(
        state_schema_version=schema_version,
        snapshot=snapshot,
        config_generation=_systevisor_self_update_int(obj.get('config_generation'), 'config generation'),
        instances={item.instance_id: item for item in instances},
        collections={item.name: item for item in collections},
        unit_desired_overrides=overrides,
        startup_collection=None if startup is None else SystevisorCollectionName(startup),
        shutting_down=_systevisor_self_update_bool(obj.get('shutting_down'), 'shutting down'),
        next_run_id=_systevisor_self_update_int(obj.get('next_run_id'), 'next run id'),
        next_deadline_id=_systevisor_self_update_int(obj.get('next_deadline_id'), 'next deadline id'),
        event_sequence=_systevisor_self_update_int(obj.get('event_sequence'), 'event sequence'),
        last_now=_systevisor_self_update_float(obj.get('last_now'), 'last now'),
        next_health_check_id=_systevisor_self_update_int(
            obj.get('next_health_check_id'),
            'next health check id',
        ),
    )


def systevisor_encode_owned_process_state(state: SystevisorOwnedProcessState) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'run_id': state.run_id,
        'instance_id': state.instance_id,
        'pid': state.pid,
        'pidfd': state.pidfd,
        'session_requested': state.session_requested,
        'session_id': state.session_id,
        'birth_identity': state.birth_identity,
        'status': state.status.value,
        'stdout_fd': state.stdout_fd,
        'stderr_fd': state.stderr_fd,
        'exec_error_fd': state.exec_error_fd,
        'return_code': state.return_code,
        'signal_lease_count': state.signal_lease_count,
        'purpose': state.purpose.value,
        'health_check_id': state.health_check_id,
        'observe_resources': state.observe_resources,
    }


def systevisor_decode_owned_process_state(value: ta.Any) -> SystevisorOwnedProcessState:
    obj = _systevisor_self_update_mapping(value, 'owned process state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'process schema version')
    if schema_version != 3:
        raise SystevisorSelfUpdateCodecError(f'unsupported owned process schema: {schema_version}')
    run_id = _systevisor_self_update_int(obj.get('run_id'), 'process run id')
    check_id = _systevisor_self_update_optional_int(obj.get('health_check_id'), 'health check id')
    return SystevisorOwnedProcessState(
        state_schema_version=schema_version,
        run_id=SystevisorRunId(run_id),
        instance_id=SystevisorInstanceId(_systevisor_self_update_string(
            obj.get('instance_id'),
            'process instance id',
        )),
        pid=_systevisor_self_update_int(obj.get('pid'), 'process pid'),
        pidfd=_systevisor_self_update_optional_int(obj.get('pidfd'), 'process pidfd'),
        session_requested=_systevisor_self_update_bool(obj.get('session_requested'), 'session requested'),
        session_id=_systevisor_self_update_optional_int(obj.get('session_id'), 'session id'),
        birth_identity=_systevisor_self_update_optional_string(obj.get('birth_identity'), 'birth identity'),
        status=_systevisor_self_update_enum(SystevisorOwnedProcessStatus, obj.get('status'), 'process status'),
        stdout_fd=_systevisor_self_update_optional_int(obj.get('stdout_fd'), 'stdout fd'),
        stderr_fd=_systevisor_self_update_optional_int(obj.get('stderr_fd'), 'stderr fd'),
        exec_error_fd=_systevisor_self_update_optional_int(obj.get('exec_error_fd'), 'exec error fd'),
        return_code=_systevisor_self_update_optional_int(obj.get('return_code'), 'return code'),
        signal_lease_count=_systevisor_self_update_int(obj.get('signal_lease_count'), 'signal lease count'),
        purpose=_systevisor_self_update_enum(SystevisorOwnedProcessPurpose, obj.get('purpose'), 'process purpose'),
        health_check_id=None if check_id is None else SystevisorHealthCheckId(check_id),
        observe_resources=_systevisor_self_update_bool(obj.get('observe_resources'), 'observe resources'),
    )


def systevisor_encode_log_channel_state(
        state: SystevisorLogChannelState,
        fd: ta.Optional[int],
) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'run_id': state.run_id,
        'instance_id': state.instance_id,
        'stream': state.stream.value,
        'config': systevisor_marshal_config_obj(state.config, SystevisorOutputConfig),
        'data_base64': base64.b64encode(state.data).decode('ascii'),
        'end_offset': state.end_offset,
        'retired': state.retired,
        'created_at': state.created_at,
        'last_activity_at': state.last_activity_at,
        'fd': fd,
    }


def systevisor_decode_log_channel_state(
        value: ta.Any,
) -> ta.Tuple[SystevisorLogChannelState, ta.Optional[int]]:
    obj = _systevisor_self_update_mapping(value, 'log channel state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'log channel schema version')
    if schema_version != 1:
        raise SystevisorSelfUpdateCodecError(f'unsupported log channel schema: {schema_version}')
    raw_data = _systevisor_self_update_string(obj.get('data_base64'), 'log channel data')
    try:
        data = base64.b64decode(raw_data, validate=True)
    except ValueError as exc:
        raise SystevisorSelfUpdateCodecError('invalid log channel base64 data') from exc
    return SystevisorLogChannelState(
        state_schema_version=schema_version,
        run_id=SystevisorRunId(_systevisor_self_update_int(obj.get('run_id'), 'log channel run id')),
        instance_id=SystevisorInstanceId(_systevisor_self_update_string(
            obj.get('instance_id'),
            'log channel instance id',
        )),
        stream=_systevisor_self_update_enum(SystevisorLogStream, obj.get('stream'), 'log channel stream'),
        config=systevisor_unmarshal_config(obj.get('config'), SystevisorOutputConfig),
        data=data,
        end_offset=_systevisor_self_update_int(obj.get('end_offset'), 'log channel end offset'),
        retired=_systevisor_self_update_bool(obj.get('retired'), 'log channel retired'),
        created_at=_systevisor_self_update_float(obj.get('created_at'), 'log channel creation time'),
        last_activity_at=_systevisor_self_update_optional_float(
            obj.get('last_activity_at'),
            'log channel last activity time',
        ),
    ), _systevisor_self_update_optional_int(obj.get('fd'), 'log channel fd')


def systevisor_encode_event_bus_state(
        state: SystevisorEventBusState,
        normalize: ta.Callable[[ta.Any], ta.Any],
) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'journal_capacity': state.journal_capacity,
        'next_sequence': state.next_sequence,
        'journal': [
            {
                'sequence': event.sequence,
                'at': event.at,
                'topic': event.topic,
                'payload': normalize(event.payload),
            }
            for event in state.journal
        ],
    }


def systevisor_decode_event_bus_state(value: ta.Any) -> SystevisorEventBusState:
    obj = _systevisor_self_update_mapping(value, 'event bus state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'event bus schema version')
    if schema_version != 1:
        raise SystevisorSelfUpdateCodecError(f'unsupported event bus schema: {schema_version}')
    events: ta.List[SystevisorBusEvent] = []
    for value_event in _systevisor_self_update_sequence(obj.get('journal'), 'event journal'):
        raw_event = _systevisor_self_update_mapping(value_event, 'bus event')
        events.append(SystevisorBusEvent(
            sequence=_systevisor_self_update_int(raw_event.get('sequence'), 'bus event sequence'),
            at=_systevisor_self_update_float(raw_event.get('at'), 'bus event time'),
            topic=_systevisor_self_update_string(raw_event.get('topic'), 'bus event topic'),
            payload=raw_event.get('payload'),
        ))
    return SystevisorEventBusState(
        state_schema_version=schema_version,
        journal_capacity=_systevisor_self_update_int(obj.get('journal_capacity'), 'event journal capacity'),
        next_sequence=_systevisor_self_update_int(obj.get('next_sequence'), 'next bus event sequence'),
        journal=tuple(events),
    )


def systevisor_encode_operation_store_state(
        state: SystevisorOperationStoreState,
        normalize: ta.Callable[[ta.Any], ta.Any],
) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'capacity': state.capacity,
        'next_id': state.next_id,
        'operations': [
            {
                'operation_id': operation.operation_id,
                'kind': operation.kind,
                'target': operation.target,
                'created_at': operation.created_at,
                'status': operation.status.value,
                'completed_at': operation.completed_at,
                'message': operation.message,
                'data': normalize(operation.data),
            }
            for operation in state.operations
        ],
    }


def systevisor_decode_operation_store_state(value: ta.Any) -> SystevisorOperationStoreState:
    obj = _systevisor_self_update_mapping(value, 'operation store state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'operation store schema version')
    if schema_version != 1:
        raise SystevisorSelfUpdateCodecError(f'unsupported operation store schema: {schema_version}')
    operations: ta.List[SystevisorOperation] = []
    for value_operation in _systevisor_self_update_sequence(obj.get('operations'), 'operations'):
        raw_operation = _systevisor_self_update_mapping(value_operation, 'operation')
        operations.append(SystevisorOperation(
            operation_id=_systevisor_self_update_string(raw_operation.get('operation_id'), 'operation id'),
            kind=_systevisor_self_update_string(raw_operation.get('kind'), 'operation kind'),
            target=_systevisor_self_update_optional_string(raw_operation.get('target'), 'operation target'),
            created_at=_systevisor_self_update_float(raw_operation.get('created_at'), 'operation creation time'),
            status=_systevisor_self_update_enum(
                SystevisorOperationStatus,
                raw_operation.get('status'),
                'operation status',
            ),
            completed_at=_systevisor_self_update_optional_float(
                raw_operation.get('completed_at'),
                'operation completion time',
            ),
            message=_systevisor_self_update_optional_string(raw_operation.get('message'), 'operation message'),
            data=_systevisor_self_update_mapping(raw_operation.get('data'), 'operation data'),
        ))
    return SystevisorOperationStoreState(
        state_schema_version=schema_version,
        capacity=_systevisor_self_update_int(obj.get('capacity'), 'operation capacity'),
        next_id=_systevisor_self_update_int(obj.get('next_id'), 'next operation id'),
        operations=tuple(operations),
    )


def systevisor_encode_manager_runtime_state(state: SystevisorManagerRuntimeState) -> ta.Mapping[str, ta.Any]:
    pid_file = state.pid_file
    return {
        'bootstrap': {
            'pid': state.bootstrap.pid,
            'is_pid_one': state.bootstrap.is_pid_one,
            'subreaper_enabled': state.bootstrap.subreaper_enabled,
            'systemd_notify': state.bootstrap.systemd_notify,
            'launchd_job': state.bootstrap.launchd_job,
        },
        'config': systevisor_marshal_config_obj(state.config, SystevisorManagerConfig),
        'pid_file': None if pid_file is None else {
            'path': pid_file.path,
            'pid': pid_file.pid,
            'device': pid_file.device,
            'inode': pid_file.inode,
        },
        'ready': state.ready,
        'stopping': state.stopping,
    }


def systevisor_decode_manager_runtime_state(value: ta.Any) -> SystevisorManagerRuntimeState:
    obj = _systevisor_self_update_mapping(value, 'manager runtime state')
    raw_bootstrap = _systevisor_self_update_mapping(obj.get('bootstrap'), 'manager bootstrap state')
    raw_pid_file = obj.get('pid_file')
    pid_file: ta.Optional[SystevisorPidFileState]
    if raw_pid_file is None:
        pid_file = None
    else:
        pid_obj = _systevisor_self_update_mapping(raw_pid_file, 'pidfile state')
        pid_file = SystevisorPidFileState(
            path=_systevisor_self_update_string(pid_obj.get('path'), 'pidfile path'),
            pid=_systevisor_self_update_int(pid_obj.get('pid'), 'pidfile pid'),
            device=_systevisor_self_update_int(pid_obj.get('device'), 'pidfile device'),
            inode=_systevisor_self_update_int(pid_obj.get('inode'), 'pidfile inode'),
        )
    return SystevisorManagerRuntimeState(
        bootstrap=SystevisorProcessBootstrapState(
            pid=_systevisor_self_update_int(raw_bootstrap.get('pid'), 'bootstrap pid'),
            is_pid_one=_systevisor_self_update_bool(raw_bootstrap.get('is_pid_one'), 'bootstrap pid one'),
            subreaper_enabled=_systevisor_self_update_bool(
                raw_bootstrap.get('subreaper_enabled'),
                'bootstrap subreaper',
            ),
            systemd_notify=_systevisor_self_update_bool(
                raw_bootstrap.get('systemd_notify'),
                'bootstrap systemd notify',
            ),
            launchd_job=_systevisor_self_update_bool(raw_bootstrap.get('launchd_job'), 'bootstrap launchd job'),
        ),
        config=systevisor_unmarshal_config(obj.get('config'), SystevisorManagerConfig),
        pid_file=pid_file,
        ready=_systevisor_self_update_bool(obj.get('ready'), 'manager ready'),
        stopping=_systevisor_self_update_bool(obj.get('stopping'), 'manager stopping'),
    )


def systevisor_encode_inherited_socket(socket_state: SystevisorInheritedSocket) -> ta.Mapping[str, ta.Any]:
    return dc.asdict(socket_state)


def systevisor_decode_inherited_socket(value: ta.Any) -> SystevisorInheritedSocket:
    obj = _systevisor_self_update_mapping(value, 'inherited socket')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'socket schema version')
    if schema_version != 1:
        raise SystevisorSelfUpdateCodecError(f'unsupported inherited socket schema: {schema_version}')
    return SystevisorInheritedSocket(
        state_schema_version=schema_version,
        name=_systevisor_self_update_string(obj.get('name'), 'socket name'),
        fd=_systevisor_self_update_int(obj.get('fd'), 'socket fd'),
        family=_systevisor_self_update_int(obj.get('family'), 'socket family'),
        socket_type=_systevisor_self_update_int(obj.get('socket_type'), 'socket type'),
    )


def systevisor_encode_cgroup_state(state: SystevisorCgroupRunState) -> ta.Mapping[str, ta.Any]:
    return {
        'state_schema_version': state.state_schema_version,
        'run_id': state.run_id,
        'instance_id': state.instance_id,
        'path': state.path,
        'config': systevisor_marshal_config_obj(state.config, SystevisorCgroupConfig),
        'status': state.status.value,
        'pid': state.pid,
        'cleanup_error': state.cleanup_error,
    }


def systevisor_decode_cgroup_state(value: ta.Any) -> SystevisorCgroupRunState:
    obj = _systevisor_self_update_mapping(value, 'cgroup state')
    schema_version = _systevisor_self_update_int(obj.get('state_schema_version'), 'cgroup schema version')
    if schema_version != 1:
        raise SystevisorSelfUpdateCodecError(f'unsupported cgroup schema: {schema_version}')
    return SystevisorCgroupRunState(
        state_schema_version=schema_version,
        run_id=SystevisorRunId(_systevisor_self_update_int(obj.get('run_id'), 'cgroup run id')),
        instance_id=SystevisorInstanceId(_systevisor_self_update_string(
            obj.get('instance_id'),
            'cgroup instance id',
        )),
        path=_systevisor_self_update_string(obj.get('path'), 'cgroup path'),
        config=systevisor_unmarshal_config(obj.get('config'), SystevisorCgroupConfig),
        status=_systevisor_self_update_enum(SystevisorCgroupRunStatus, obj.get('status'), 'cgroup status'),
        pid=_systevisor_self_update_optional_int(obj.get('pid'), 'cgroup pid'),
        cleanup_error=_systevisor_self_update_optional_string(obj.get('cleanup_error'), 'cgroup cleanup error'),
    )


def systevisor_decode_snapshot(
        config_value: ta.Any,
        expected_digest: str,
        source_paths: ta.Sequence[str],
        provenance_values: ta.Iterable[ta.Any] = (),
) -> SystevisorConfigSnapshot:
    config = systevisor_unmarshal_config(config_value, SystevisorConfig)
    provenance: ta.List[SystevisorConfigProvenance] = []
    for value in provenance_values:
        obj = _systevisor_self_update_mapping(value, 'configuration provenance')
        object_path = tuple(
            _systevisor_self_update_string(item, 'configuration object path')
            for item in _systevisor_self_update_sequence(obj.get('object_path'), 'configuration object path')
        )
        provenance.append(SystevisorConfigProvenance(
            object_path=object_path,
            source=_systevisor_self_update_string(obj.get('source'), 'configuration provenance source'),
        ))
    snapshot = systevisor_build_config_snapshot(config, source_paths, provenance)
    if snapshot.digest != expected_digest:
        raise SystevisorSelfUpdateCodecError(
            f'configuration digest mismatch: {snapshot.digest} != {expected_digest}',
        )
    return snapshot


def _systevisor_self_update_fd_to_obj(item: SystevisorHandoffFd) -> ta.Mapping[str, ta.Any]:
    return {
        'kind': item.kind.value,
        'owner': item.owner,
        'fd': item.fd,
        'device': item.device,
        'inode': item.inode,
        'mode': item.mode,
        'status_flags': item.status_flags,
    }


def _systevisor_self_update_fd_from_obj(value: ta.Any) -> SystevisorHandoffFd:
    obj = _systevisor_self_update_mapping(value, 'handoff fd')
    return SystevisorHandoffFd(
        kind=_systevisor_self_update_enum(SystevisorHandoffFdKind, obj.get('kind'), 'handoff fd kind'),
        owner=_systevisor_self_update_string(obj.get('owner'), 'handoff fd owner'),
        fd=_systevisor_self_update_int(obj.get('fd'), 'handoff fd number'),
        device=_systevisor_self_update_int(obj.get('device'), 'handoff fd device'),
        inode=_systevisor_self_update_int(obj.get('inode'), 'handoff fd inode'),
        mode=_systevisor_self_update_int(obj.get('mode'), 'handoff fd mode'),
        status_flags=_systevisor_self_update_int(obj.get('status_flags'), 'handoff fd status flags'),
    )


def systevisor_self_update_probe_request_to_obj(
        request: SystevisorSelfUpdateProbeRequest,
) -> ta.Mapping[str, ta.Any]:
    return dc.asdict(request)


def systevisor_self_update_probe_request_from_obj(value: ta.Any) -> SystevisorSelfUpdateProbeRequest:
    obj = _systevisor_self_update_mapping(value, 'self-update probe request')
    schema_version = _systevisor_self_update_int(obj.get('schema_version'), 'probe request schema version')
    if schema_version != SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION:
        raise SystevisorSelfUpdateCodecError(f'unsupported probe request schema: {schema_version}')
    return SystevisorSelfUpdateProbeRequest(
        schema_version=schema_version,
        source_path=_systevisor_self_update_string(obj.get('source_path'), 'probe source path'),
        source_sha256=_systevisor_self_update_string(obj.get('source_sha256'), 'probe source digest'),
        config=_systevisor_self_update_mapping(obj.get('config'), 'probe configuration'),
        config_digest=_systevisor_self_update_string(obj.get('config_digest'), 'probe config digest'),
    )


def systevisor_self_update_probe_result_to_obj(
        result: SystevisorSelfUpdateProbeResult,
) -> ta.Mapping[str, ta.Any]:
    return dc.asdict(result)


def systevisor_self_update_probe_result_from_obj(value: ta.Any) -> SystevisorSelfUpdateProbeResult:
    obj = _systevisor_self_update_mapping(value, 'self-update probe result')
    schema_version = _systevisor_self_update_int(obj.get('schema_version'), 'probe result schema version')
    if schema_version != SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION:
        raise SystevisorSelfUpdateCodecError(f'unsupported probe result schema: {schema_version}')
    return SystevisorSelfUpdateProbeResult(
        schema_version=schema_version,
        accepted=_systevisor_self_update_bool(obj.get('accepted'), 'probe accepted'),
        source_sha256=_systevisor_self_update_string(obj.get('source_sha256'), 'probe result source digest'),
        message=_systevisor_self_update_optional_string(obj.get('message'), 'probe result message'),
    )


def systevisor_handoff_manifest_to_obj(manifest: SystevisorHandoffManifest) -> ta.Mapping[str, ta.Any]:
    return {
        'schema_version': manifest.schema_version,
        'source_path': manifest.source_path,
        'source_sha256': manifest.source_sha256,
        'previous_source_path': manifest.previous_source_path,
        'previous_source_sha256': manifest.previous_source_sha256,
        'created_at': manifest.created_at,
        'manager_pid': manifest.manager_pid,
        'operation_id': manifest.operation_id,
        'mode': manifest.mode,
        'startup_collection': manifest.startup_collection,
        'config_paths': list(manifest.config_paths),
        'recursive': manifest.recursive,
        'state_directory': manifest.state_directory,
        'config': manifest.config,
        'config_digest': manifest.config_digest,
        'source_paths': list(manifest.source_paths),
        'provenance': list(manifest.provenance),
        'engine': manifest.engine,
        'processes': list(manifest.processes),
        'logs': list(manifest.logs),
        'event_bus': manifest.event_bus,
        'operations': manifest.operations,
        'manager_runtime': manifest.manager_runtime,
        'inherited_sockets': list(manifest.inherited_sockets),
        'cgroups': list(manifest.cgroups),
        'fds': [_systevisor_self_update_fd_to_obj(item) for item in manifest.fds],
    }


def systevisor_handoff_manifest_from_obj(value: ta.Any) -> SystevisorHandoffManifest:
    obj = _systevisor_self_update_mapping(value, 'handoff manifest')
    schema_version = _systevisor_self_update_int(obj.get('schema_version'), 'handoff schema version')
    if schema_version != SYSTEVISOR_SELF_UPDATE_SCHEMA_VERSION:
        raise SystevisorSelfUpdateCodecError(f'unsupported handoff schema: {schema_version}')
    config_paths = tuple(
        _systevisor_self_update_string(item, 'config path')
        for item in _systevisor_self_update_sequence(obj.get('config_paths'), 'config paths')
    )
    source_paths = tuple(
        _systevisor_self_update_string(item, 'source path')
        for item in _systevisor_self_update_sequence(obj.get('source_paths'), 'source paths')
    )
    return SystevisorHandoffManifest(
        schema_version=schema_version,
        source_path=_systevisor_self_update_string(obj.get('source_path'), 'handoff source path'),
        source_sha256=_systevisor_self_update_string(obj.get('source_sha256'), 'handoff source digest'),
        previous_source_path=_systevisor_self_update_string(
            obj.get('previous_source_path'),
            'previous source path',
        ),
        previous_source_sha256=_systevisor_self_update_string(
            obj.get('previous_source_sha256'),
            'previous source digest',
        ),
        created_at=_systevisor_self_update_float(obj.get('created_at'), 'handoff creation time'),
        manager_pid=_systevisor_self_update_int(obj.get('manager_pid'), 'handoff manager pid'),
        operation_id=_systevisor_self_update_string(obj.get('operation_id'), 'handoff operation id'),
        mode=_systevisor_self_update_string(obj.get('mode'), 'handoff mode'),
        startup_collection=_systevisor_self_update_optional_string(
            obj.get('startup_collection'),
            'handoff startup collection',
        ),
        config_paths=config_paths,
        recursive=_systevisor_self_update_bool(obj.get('recursive'), 'handoff recursive'),
        state_directory=_systevisor_self_update_optional_string(
            obj.get('state_directory'),
            'handoff state directory',
        ),
        config=_systevisor_self_update_mapping(obj.get('config'), 'handoff configuration'),
        config_digest=_systevisor_self_update_string(obj.get('config_digest'), 'handoff config digest'),
        source_paths=source_paths,
        provenance=tuple(
            _systevisor_self_update_mapping(item, 'configuration provenance')
            for item in _systevisor_self_update_sequence(obj.get('provenance'), 'configuration provenance')
        ),
        engine=_systevisor_self_update_mapping(obj.get('engine'), 'handoff engine'),
        processes=tuple(
            _systevisor_self_update_mapping(item, 'handoff process')
            for item in _systevisor_self_update_sequence(obj.get('processes'), 'handoff processes')
        ),
        logs=tuple(
            _systevisor_self_update_mapping(item, 'handoff log')
            for item in _systevisor_self_update_sequence(obj.get('logs'), 'handoff logs')
        ),
        event_bus=_systevisor_self_update_mapping(obj.get('event_bus'), 'handoff event bus'),
        operations=_systevisor_self_update_mapping(obj.get('operations'), 'handoff operations'),
        manager_runtime=_systevisor_self_update_mapping(obj.get('manager_runtime'), 'handoff manager runtime'),
        inherited_sockets=tuple(
            _systevisor_self_update_mapping(item, 'handoff inherited socket')
            for item in _systevisor_self_update_sequence(
                obj.get('inherited_sockets'),
                'handoff inherited sockets',
            )
        ),
        cgroups=tuple(
            _systevisor_self_update_mapping(item, 'handoff cgroup')
            for item in _systevisor_self_update_sequence(obj.get('cgroups'), 'handoff cgroups')
        ),
        fds=tuple(
            _systevisor_self_update_fd_from_obj(item)
            for item in _systevisor_self_update_sequence(obj.get('fds'), 'handoff fds')
        ),
    )


def systevisor_self_update_read_json(path: str) -> ta.Any:
    file_size = os.stat(path).st_size
    if file_size > _SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES:
        raise SystevisorSelfUpdateCodecError(f'self-update document is too large: {file_size}')
    with open(path, 'rb') as input_file:
        data = input_file.read(_SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES + 1)
    if len(data) > _SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES:
        raise SystevisorSelfUpdateCodecError('self-update document exceeds its size limit')
    try:
        return json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystevisorSelfUpdateCodecError(f'invalid self-update JSON: {exc}') from exc


def systevisor_self_update_atomic_write_json(path: str, value: ta.Any) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, mode=0o700, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix='.systevisor-update.', dir=directory)
    try:
        os.fchmod(fd, 0o600)
        data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
        if len(data) > _SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES:
            raise SystevisorSelfUpdateCodecError('self-update document exceeds its size limit')
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(temporary_path, path)
        directory_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
