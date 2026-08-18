# ruff: noqa: UP006 UP007 UP045
import logging
import os
import typing as ta

from ..core.identities import systevisor_is_valid_name
from ..core.signals import SystevisorSignalNameError
from ..core.signals import systevisor_normalize_signal_name
from ..core.signals import systevisor_signal_is_catchable
from ..scheduling.cron import SystevisorCronError
from ..scheduling.cron import systevisor_parse_cron
from .diagnostics import SystevisorConfigDiagnostic
from .diagnostics import SystevisorConfigDiagnosticSeverity
from .diagnostics import SystevisorConfigDiagnosticStage
from .models import SystevisorConfig
from .models import SystevisorHealthProbeKind
from .models import SystevisorHealthRole
from .models import SystevisorOutputMode
from .models import SystevisorScheduleActionKind
from .models import SystevisorScheduleTargetKind
from .models import SystevisorStdinMode
from .models import SystevisorUnitKind


def _systevisor_config_validation_error(
        code: str,
        message: str,
        *object_path: str,
) -> SystevisorConfigDiagnostic:
    return SystevisorConfigDiagnostic(
        severity=SystevisorConfigDiagnosticSeverity.ERROR,
        stage=SystevisorConfigDiagnosticStage.VALIDATE,
        code=code,
        message=message,
        object_path=object_path,
    )


def _systevisor_config_validation_graph(config: SystevisorConfig) -> ta.Mapping[str, ta.Set[str]]:
    graph: ta.Dict[str, ta.Set[str]] = {unit_name: set() for unit_name in config.units}
    for unit_name, unit in config.units.items():
        dependencies = unit.dependencies
        graph[unit_name].update(dependencies.requires)
        graph[unit_name].update(dependencies.wants)
        graph[unit_name].update(dependencies.after)
        for target in dependencies.before:
            if target in graph:
                graph[target].add(unit_name)
    return graph


def _systevisor_config_validation_cycles(config: SystevisorConfig) -> ta.Sequence[ta.Sequence[str]]:
    graph = _systevisor_config_validation_graph(config)
    visiting: ta.Set[str] = set()
    visited: ta.Set[str] = set()
    stack: ta.List[str] = []
    cycles: ta.List[ta.Sequence[str]] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            index = stack.index(node)
            cycle = (*stack[index:], node)
            if cycle not in cycles:
                cycles.append(cycle)
            return

        visiting.add(node)
        stack.append(node)
        for dependency in sorted(graph[node]):
            if dependency in graph:
                visit(dependency)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for unit_name in sorted(graph):
        visit(unit_name)
    return tuple(cycles)


def systevisor_validate_config(config: SystevisorConfig) -> ta.Sequence[SystevisorConfigDiagnostic]:
    errors: ta.List[SystevisorConfigDiagnostic] = []

    if config.schema_version != 1:
        errors.append(_systevisor_config_validation_error(
            'unsupported_schema_version',
            f'unsupported schema version: {config.schema_version}',
            'schema_version',
        ))

    if not systevisor_is_valid_name(config.manager.identifier):
        errors.append(_systevisor_config_validation_error(
            'invalid_identifier',
            f'invalid manager identifier: {config.manager.identifier!r}',
            'manager',
            'identifier',
        ))

    if config.manager.umask < 0 or config.manager.umask > 0o777:
        errors.append(_systevisor_config_validation_error(
            'invalid_umask',
            f'invalid manager umask: {config.manager.umask!r}',
            'manager',
            'umask',
        ))

    if config.manager.min_fds < 0 or config.manager.min_procs < 0:
        errors.append(_systevisor_config_validation_error(
            'invalid_resource_minimum',
            'manager min_fds and min_procs must be non-negative',
            'manager',
        ))

    if config.manager.observation.interval_secs <= 0 or config.manager.observation.retained_runs < 0:
        errors.append(_systevisor_config_validation_error(
            'invalid_observation_policy',
            'observation interval_secs must be positive and retained_runs must be non-negative',
            'manager',
            'observation',
        ))

    if (
            config.manager.self_update.probe_timeout_secs <= 0 or
            config.manager.self_update.response_grace_secs < 0
    ):
        errors.append(_systevisor_config_validation_error(
            'invalid_self_update_policy',
            'self-update probe timeout must be positive and response grace must be non-negative',
            'manager',
            'self_update',
        ))

    cgroup_root = config.manager.cgroups.root
    if cgroup_root is not None and (not cgroup_root or not cgroup_root.startswith('/')):
        errors.append(_systevisor_config_validation_error(
            'invalid_cgroup_root',
            'manager cgroup root must be an absolute path',
            'manager',
            'cgroups',
            'root',
        ))

    if config.manager.process_title is not None and '\x00' in config.manager.process_title:
        errors.append(_systevisor_config_validation_error(
            'invalid_process_title',
            'manager process title may not contain NUL',
            'manager',
            'process_title',
        ))

    if config.manager.pid_file == '':
        errors.append(_systevisor_config_validation_error(
            'invalid_pid_file',
            'manager pid_file may not be empty',
            'manager',
            'pid_file',
        ))

    if (
            config.manager.child_log_directory is not None and
            not os.path.isabs(config.manager.child_log_directory)
    ):
        errors.append(_systevisor_config_validation_error(
            'invalid_child_log_directory',
            'manager child_log_directory must be an absolute path',
            'manager',
            'child_log_directory',
        ))

    manager_log_level = logging.getLevelName(config.manager.log.level.upper())
    if not isinstance(manager_log_level, int):
        errors.append(_systevisor_config_validation_error(
            'invalid_log_level',
            f'invalid manager log level: {config.manager.log.level!r}',
            'manager',
            'log',
            'level',
        ))
    if config.manager.log.file == '':
        errors.append(_systevisor_config_validation_error(
            'invalid_log_file',
            'manager log file may not be empty',
            'manager',
            'log',
            'file',
        ))
    if config.manager.log.max_bytes < 0 or config.manager.log.backups < 0:
        errors.append(_systevisor_config_validation_error(
            'invalid_manager_log_limit',
            'manager log max_bytes and backups must be non-negative',
            'manager',
            'log',
        ))

    if (config.api.tcp_host is None) != (config.api.tcp_port is None):
        errors.append(_systevisor_config_validation_error(
            'incomplete_tcp_listener',
            'api tcp_host and tcp_port must be set together',
            'api',
        ))
    if config.api.tcp_port is not None and not 0 < config.api.tcp_port < 65536:
        errors.append(_systevisor_config_validation_error(
            'invalid_tcp_port',
            f'invalid api tcp port: {config.api.tcp_port}',
            'api',
            'tcp_port',
        ))
    if not 0 <= config.api.unix_socket_mode <= 0o777:
        errors.append(_systevisor_config_validation_error(
            'invalid_unix_socket_mode',
            f'invalid api unix socket mode: {config.api.unix_socket_mode!r}',
            'api',
            'unix_socket_mode',
        ))
    if config.api.event_backlog < 1 or config.api.stream_queue_bytes < 1:
        errors.append(_systevisor_config_validation_error(
            'invalid_api_buffer_limit',
            'api event_backlog and stream_queue_bytes must be positive',
            'api',
        ))

    for unit_name, unit in config.units.items():
        unit_path = ('units', unit_name)
        if not systevisor_is_valid_name(unit_name):
            errors.append(_systevisor_config_validation_error(
                'invalid_unit_name',
                f'invalid unit name: {unit_name!r}',
                *unit_path,
            ))
        if not unit.exec.argv:
            errors.append(_systevisor_config_validation_error(
                'empty_argv',
                'exec argv must contain at least one item',
                *unit_path,
                'exec',
                'argv',
            ))
        elif any(not isinstance(argument, str) or '\x00' in argument for argument in unit.exec.argv):
            errors.append(_systevisor_config_validation_error(
                'invalid_argv',
                'exec argv items must be NUL-free strings',
                *unit_path,
                'exec',
                'argv',
            ))
        if unit.replicas < 1:
            errors.append(_systevisor_config_validation_error(
                'invalid_replicas',
                'replicas must be at least one',
                *unit_path,
                'replicas',
            ))
        if unit.replica_start < 0:
            errors.append(_systevisor_config_validation_error(
                'invalid_replica_start',
                'replica_start must be non-negative',
                *unit_path,
                'replica_start',
            ))
        if unit.exec.umask is not None and not 0 <= unit.exec.umask <= 0o777:
            errors.append(_systevisor_config_validation_error(
                'invalid_umask',
                f'invalid exec umask: {unit.exec.umask!r}',
                *unit_path,
                'exec',
                'umask',
            ))
        if unit.identity.user is not None and unit.identity.uid is not None:
            errors.append(_systevisor_config_validation_error(
                'ambiguous_user',
                'identity user and uid are mutually exclusive',
                *unit_path,
                'identity',
            ))
        if unit.identity.group is not None and unit.identity.gid is not None:
            errors.append(_systevisor_config_validation_error(
                'ambiguous_group',
                'identity group and gid are mutually exclusive',
                *unit_path,
                'identity',
            ))
        if unit.restart.start_secs < 0 or unit.restart.start_retries < 0:
            errors.append(_systevisor_config_validation_error(
                'invalid_start_policy',
                'start_secs and start_retries must be non-negative',
                *unit_path,
                'restart',
            ))
        if (
                unit.restart.backoff_initial_secs < 0 or
                unit.restart.backoff_multiplier < 1 or
                unit.restart.backoff_max_secs < unit.restart.backoff_initial_secs
        ):
            errors.append(_systevisor_config_validation_error(
                'invalid_backoff_policy',
                'backoff values must be non-negative, non-decreasing, and use a multiplier of at least one',
                *unit_path,
                'restart',
            ))
        if unit.stop.timeout_secs < 0:
            errors.append(_systevisor_config_validation_error(
                'invalid_stop_timeout',
                'stop timeout must be non-negative',
                *unit_path,
                'stop',
                'timeout_secs',
            ))

        cgroup = unit.resources.cgroup
        if cgroup.enabled and cgroup_root is None:
            errors.append(_systevisor_config_validation_error(
                'missing_cgroup_root',
                'cgroup-enabled units require manager.cgroups.root',
                *unit_path,
                'resources',
                'cgroup',
            ))
        if not cgroup.enabled and any(value is not None for value in (
                cgroup.cpu_weight,
                cgroup.cpu_quota_usec,
                cgroup.memory_low_bytes,
                cgroup.memory_high_bytes,
                cgroup.memory_max_bytes,
                cgroup.pids_max,
        )):
            errors.append(_systevisor_config_validation_error(
                'disabled_cgroup_policy',
                'cgroup resource controls require enabled=true',
                *unit_path,
                'resources',
                'cgroup',
            ))
        if cgroup.cpu_weight is not None and not 1 <= cgroup.cpu_weight <= 10_000:
            errors.append(_systevisor_config_validation_error(
                'invalid_cgroup_cpu_weight',
                'cgroup cpu_weight must be between 1 and 10000',
                *unit_path,
                'resources',
                'cgroup',
                'cpu_weight',
            ))
        if cgroup.cpu_quota_usec is not None and cgroup.cpu_quota_usec <= 0:
            errors.append(_systevisor_config_validation_error(
                'invalid_cgroup_cpu_quota',
                'cgroup cpu_quota_usec must be positive',
                *unit_path,
                'resources',
                'cgroup',
                'cpu_quota_usec',
            ))
        if not 1_000 <= cgroup.cpu_period_usec <= 1_000_000:
            errors.append(_systevisor_config_validation_error(
                'invalid_cgroup_cpu_period',
                'cgroup cpu_period_usec must be between 1000 and 1000000',
                *unit_path,
                'resources',
                'cgroup',
                'cpu_period_usec',
            ))
        if any(value is not None and value < 0 for value in (
                cgroup.memory_low_bytes,
                cgroup.memory_high_bytes,
                cgroup.memory_max_bytes,
        )):
            errors.append(_systevisor_config_validation_error(
                'invalid_cgroup_memory_limit',
                'cgroup memory limits must be non-negative',
                *unit_path,
                'resources',
                'cgroup',
            ))
        if cgroup.pids_max is not None and cgroup.pids_max < 1:
            errors.append(_systevisor_config_validation_error(
                'invalid_cgroup_pids_limit',
                'cgroup pids_max must be positive',
                *unit_path,
                'resources',
                'cgroup',
                'pids_max',
            ))
        namespaces = unit.resources.namespaces
        if namespaces.hostname is not None and not namespaces.uts:
            errors.append(_systevisor_config_validation_error(
                'namespace_hostname_without_uts',
                'namespace hostname requires uts=true',
                *unit_path,
                'resources',
                'namespaces',
                'hostname',
            ))
        if len(set(unit.resources.inherited_sockets)) != len(unit.resources.inherited_sockets):
            errors.append(_systevisor_config_validation_error(
                'duplicate_inherited_socket',
                'inherited socket names must be unique within a unit',
                *unit_path,
                'resources',
                'inherited_sockets',
            ))
        for socket_name in unit.resources.inherited_sockets:
            if not systevisor_is_valid_name(socket_name):
                errors.append(_systevisor_config_validation_error(
                    'invalid_inherited_socket_name',
                    f'invalid inherited socket name: {socket_name!r}',
                    *unit_path,
                    'resources',
                    'inherited_sockets',
                ))
        if namespaces.hostname is not None and (
                not namespaces.hostname or
                '\x00' in namespaces.hostname or
                len(namespaces.hostname.encode('utf-8')) > 64
        ):
            errors.append(_systevisor_config_validation_error(
                'invalid_namespace_hostname',
                'namespace hostname must be non-empty, NUL-free, and at most 64 UTF-8 bytes',
                *unit_path,
                'resources',
                'namespaces',
                'hostname',
            ))
        if unit.stdio.stdin.mode is SystevisorStdinMode.FILE and unit.stdio.stdin.file is None:
            errors.append(_systevisor_config_validation_error(
                'missing_input_file',
                'file stdin mode requires a file',
                *unit_path,
                'stdio',
                'stdin',
            ))
        for channel_name, output in (('stdout', unit.stdio.stdout), ('stderr', unit.stdio.stderr)):
            if (
                    output.mode is SystevisorOutputMode.FILE and
                    output.file is None and
                    config.manager.child_log_directory is None
            ):
                errors.append(_systevisor_config_validation_error(
                    'missing_output_file',
                    'file output mode requires a file or manager child_log_directory',
                    *unit_path,
                    'stdio',
                    channel_name,
                ))
            if min(output.max_bytes, output.backups, output.back_buffer_bytes) < 0:
                errors.append(_systevisor_config_validation_error(
                    'invalid_output_limit',
                    'output limits must be non-negative',
                    *unit_path,
                    'stdio',
                    channel_name,
                ))

        for field_name, signal_name in (
                ('signal', unit.stop.signal),
                ('kill_signal', unit.stop.kill_signal),
        ):
            try:
                systevisor_normalize_signal_name(signal_name)
            except (SystevisorSignalNameError, ValueError):
                errors.append(_systevisor_config_validation_error(
                    'invalid_stop_signal',
                    f'invalid stop signal: {signal_name!r}',
                    *unit_path,
                    'stop',
                    field_name,
                ))

        forwarded_inputs: ta.Set[str] = set()
        for incoming, outgoing in unit.signals.forward.items():
            incoming_valid = True
            try:
                normalized_incoming = systevisor_normalize_signal_name(incoming)
                incoming_catchable = systevisor_signal_is_catchable(incoming)
            except (SystevisorSignalNameError, ValueError):
                incoming_valid = False
                normalized_incoming = incoming.upper()
                incoming_catchable = False
                errors.append(_systevisor_config_validation_error(
                    'invalid_forward_signal',
                    f'invalid incoming signal: {incoming!r}',
                    *unit_path,
                    'signals',
                    'forward',
                    incoming,
                ))
            try:
                systevisor_normalize_signal_name(outgoing)
            except (SystevisorSignalNameError, ValueError):
                errors.append(_systevisor_config_validation_error(
                    'invalid_forward_signal',
                    f'invalid outgoing signal: {outgoing!r}',
                    *unit_path,
                    'signals',
                    'forward',
                    incoming,
                ))
            if incoming_valid and (
                    normalized_incoming in {'CHLD', 'TERM', 'INT', 'HUP', 'QUIT'} or
                    not incoming_catchable
            ):
                errors.append(_systevisor_config_validation_error(
                    'reserved_forward_signal',
                    f'incoming signal is reserved by the manager: {incoming!r}',
                    *unit_path,
                    'signals',
                    'forward',
                    incoming,
                ))
            if normalized_incoming in forwarded_inputs:
                errors.append(_systevisor_config_validation_error(
                    'duplicate_forward_signal',
                    f'incoming signal is configured more than once: {normalized_incoming}',
                    *unit_path,
                    'signals',
                    'forward',
                    incoming,
                ))
            forwarded_inputs.add(normalized_incoming)

        dependency_names = set(unit.dependencies.requires)
        dependency_names.update(unit.dependencies.wants)
        dependency_names.update(unit.dependencies.after)
        dependency_names.update(unit.dependencies.before)
        for dependency_name in sorted(dependency_names):
            if dependency_name not in config.units:
                errors.append(_systevisor_config_validation_error(
                    'unknown_dependency',
                    f'unknown unit dependency: {dependency_name!r}',
                    *unit_path,
                    'dependencies',
                ))
            elif dependency_name == unit_name:
                errors.append(_systevisor_config_validation_error(
                    'self_dependency',
                    'a unit may not depend on itself',
                    *unit_path,
                    'dependencies',
                ))

        health_names: ta.Set[str] = set()
        health_roles: ta.Set[SystevisorHealthRole] = set()
        for index, probe in enumerate(unit.health):
            probe_path = (*unit_path, 'health', str(index))
            if not systevisor_is_valid_name(probe.name):
                errors.append(_systevisor_config_validation_error(
                    'invalid_health_name',
                    f'invalid health probe name: {probe.name!r}',
                    *probe_path,
                    'name',
                ))
            if probe.name in health_names:
                errors.append(_systevisor_config_validation_error(
                    'duplicate_health_name',
                    f'duplicate health probe name: {probe.name!r}',
                    *probe_path,
                    'name',
                ))
            health_names.add(probe.name)
            health_roles.add(probe.role)
            if (
                    probe.initial_delay_secs < 0 or
                    probe.interval_secs <= 0 or
                    probe.timeout_secs <= 0 or
                    probe.success_threshold < 1 or
                    probe.failure_threshold < 1
            ):
                errors.append(_systevisor_config_validation_error(
                    'invalid_health_timing',
                    'health initial delay must be non-negative; interval, timeout, and thresholds must be positive',
                    *probe_path,
                ))
            if probe.kind is SystevisorHealthProbeKind.COMMAND:
                if not probe.argv:
                    errors.append(_systevisor_config_validation_error(
                        'missing_health_argv',
                        'command health probes require argv',
                        *probe_path,
                        'argv',
                    ))
                elif any(not isinstance(argument, str) or '\x00' in argument for argument in probe.argv):
                    errors.append(_systevisor_config_validation_error(
                        'invalid_health_argv',
                        'command health probe argv items must be NUL-free strings',
                        *probe_path,
                        'argv',
                    ))
            if probe.kind is SystevisorHealthProbeKind.HTTP:
                if probe.url is None:
                    errors.append(_systevisor_config_validation_error(
                        'missing_health_url',
                        'http health probes require a url',
                        *probe_path,
                        'url',
                    ))
                elif not probe.url.startswith('http://'):
                    errors.append(_systevisor_config_validation_error(
                        'unsupported_health_url',
                        'http health probe urls must use the http scheme',
                        *probe_path,
                        'url',
                    ))
                if not probe.method or any(character.isspace() for character in probe.method):
                    errors.append(_systevisor_config_validation_error(
                        'invalid_health_method',
                        'http health probe methods must be non-empty and contain no whitespace',
                        *probe_path,
                        'method',
                    ))
                if not probe.expected_statuses or any(
                        status < 100 or status > 599
                        for status in probe.expected_statuses
                ):
                    errors.append(_systevisor_config_validation_error(
                        'invalid_health_statuses',
                        'http health probe expected statuses must contain valid HTTP status codes',
                        *probe_path,
                        'expected_statuses',
                    ))
            if probe.kind is SystevisorHealthProbeKind.TCP:
                if probe.host is None or probe.port is None:
                    errors.append(_systevisor_config_validation_error(
                        'missing_health_address',
                        'tcp health probes require host and port',
                        *probe_path,
                    ))
                elif not 0 < probe.port < 65536:
                    errors.append(_systevisor_config_validation_error(
                        'invalid_health_port',
                        'tcp health probe ports must be between 1 and 65535',
                        *probe_path,
                        'port',
                    ))
            if probe.kind is SystevisorHealthProbeKind.LOG_ACTIVITY:
                if probe.channel is None or probe.max_quiet_secs is None:
                    errors.append(_systevisor_config_validation_error(
                        'missing_health_log_policy',
                        'log activity health probes require a stdout/stderr channel and max_quiet_secs',
                        *probe_path,
                    ))
                elif probe.channel not in {'stdout', 'stderr'} or probe.max_quiet_secs < 0:
                    errors.append(_systevisor_config_validation_error(
                        'invalid_health_log_policy',
                        'log activity channel must be stdout/stderr and max_quiet_secs must be non-negative',
                        *probe_path,
                    ))
        if SystevisorHealthRole.STARTUP in health_roles and unit.kind is SystevisorUnitKind.ONESHOT:
            errors.append(_systevisor_config_validation_error(
                'oneshot_startup_probe',
                'oneshot units may not have startup probes',
                *unit_path,
                'health',
            ))

    for collection_name, collection in config.collections.items():
        collection_path = ('collections', collection_name)
        if not systevisor_is_valid_name(collection_name):
            errors.append(_systevisor_config_validation_error(
                'invalid_collection_name',
                f'invalid collection name: {collection_name!r}',
                *collection_path,
            ))
        if not collection.units:
            errors.append(_systevisor_config_validation_error(
                'empty_collection',
                'collections must contain at least one unit',
                *collection_path,
                'units',
            ))
        if len(set(collection.units)) != len(collection.units):
            errors.append(_systevisor_config_validation_error(
                'duplicate_collection_unit',
                'collection unit names must be unique',
                *collection_path,
                'units',
            ))
        for unit_name in collection.units:
            if unit_name not in config.units:
                errors.append(_systevisor_config_validation_error(
                    'unknown_collection_unit',
                    f'unknown collection unit: {unit_name!r}',
                    *collection_path,
                    'units',
                ))

    instance_ids = {
        f'{unit_name}:{replica}'
        for unit_name, unit in config.units.items()
        for replica in range(unit.replica_start, unit.replica_start + unit.replicas)
    }
    for schedule_name, schedule in config.schedules.items():
        schedule_path = ('schedules', schedule_name)
        if not systevisor_is_valid_name(schedule_name):
            errors.append(_systevisor_config_validation_error(
                'invalid_schedule_name',
                f'invalid schedule name: {schedule_name!r}',
                *schedule_path,
            ))
        try:
            systevisor_parse_cron(schedule.cron)
        except SystevisorCronError as exc:
            errors.append(_systevisor_config_validation_error(
                'invalid_cron',
                str(exc),
                *schedule_path,
                'cron',
            ))
        if schedule.timezone != 'UTC':
            errors.append(_systevisor_config_validation_error(
                'unsupported_schedule_timezone',
                'the initial scheduler supports only UTC',
                *schedule_path,
                'timezone',
            ))
        if schedule.max_catch_up < 1:
            errors.append(_systevisor_config_validation_error(
                'invalid_schedule_catch_up',
                'schedule max_catch_up must be positive',
                *schedule_path,
                'max_catch_up',
            ))
        action = schedule.action
        if action.kind is SystevisorScheduleActionKind.SHUTDOWN:
            if action.target_kind is not None or action.target is not None:
                errors.append(_systevisor_config_validation_error(
                    'invalid_schedule_shutdown_target',
                    'shutdown schedule actions may not have a target',
                    *schedule_path,
                    'action',
                ))
            continue
        if action.target_kind is None or action.target is None:
            errors.append(_systevisor_config_validation_error(
                'missing_schedule_target',
                'non-shutdown schedule actions require target_kind and target',
                *schedule_path,
                'action',
            ))
            continue
        if (
                action.kind is SystevisorScheduleActionKind.RESTART and
                action.target_kind is SystevisorScheduleTargetKind.COLLECTION
        ):
            errors.append(_systevisor_config_validation_error(
                'unsupported_schedule_action',
                'collection restart is not supported; schedule an instance or unit restart',
                *schedule_path,
                'action',
            ))
        targets = (
            config.units if action.target_kind is SystevisorScheduleTargetKind.UNIT else
            config.collections if action.target_kind is SystevisorScheduleTargetKind.COLLECTION else
            instance_ids
        )
        if action.target not in targets:
            errors.append(_systevisor_config_validation_error(
                'unknown_schedule_target',
                f'unknown schedule target: {action.target!r}',
                *schedule_path,
                'action',
                'target',
            ))

    for cycle in _systevisor_config_validation_cycles(config):
        errors.append(_systevisor_config_validation_error(
            'dependency_cycle',
            f'dependency ordering cycle: {" -> ".join(cycle)}',
            'units',
        ))

    return tuple(errors)
