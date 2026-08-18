# ruff: noqa: UP006 UP007 UP045
import typing as ta

from ..core.identities import systevisor_is_valid_name
from .diagnostics import SystevisorConfigDiagnostic
from .diagnostics import SystevisorConfigDiagnosticSeverity
from .diagnostics import SystevisorConfigDiagnosticStage
from .models import SystevisorConfig
from .models import SystevisorHealthProbeKind
from .models import SystevisorHealthRole
from .models import SystevisorOutputMode
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
        if unit.stdio.stdin.mode is SystevisorStdinMode.FILE and unit.stdio.stdin.file is None:
            errors.append(_systevisor_config_validation_error(
                'missing_input_file',
                'file stdin mode requires a file',
                *unit_path,
                'stdio',
                'stdin',
            ))
        for channel_name, output in (('stdout', unit.stdio.stdout), ('stderr', unit.stdio.stderr)):
            if output.mode is SystevisorOutputMode.FILE and output.file is None:
                errors.append(_systevisor_config_validation_error(
                    'missing_output_file',
                    'file output mode requires a file',
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
            if min(
                    probe.initial_delay_secs,
                    probe.interval_secs,
                    probe.timeout_secs,
                    probe.success_threshold,
                    probe.failure_threshold,
            ) < 0 or probe.success_threshold < 1 or probe.failure_threshold < 1:
                errors.append(_systevisor_config_validation_error(
                    'invalid_health_timing',
                    'health timing values must be non-negative and thresholds must be positive',
                    *probe_path,
                ))
            if probe.kind is SystevisorHealthProbeKind.COMMAND and not probe.argv:
                errors.append(_systevisor_config_validation_error(
                    'missing_health_argv',
                    'command health probes require argv',
                    *probe_path,
                    'argv',
                ))
            if probe.kind is SystevisorHealthProbeKind.HTTP and probe.url is None:
                errors.append(_systevisor_config_validation_error(
                    'missing_health_url',
                    'http health probes require a url',
                    *probe_path,
                    'url',
                ))
            if probe.kind is SystevisorHealthProbeKind.TCP and (probe.host is None or probe.port is None):
                errors.append(_systevisor_config_validation_error(
                    'missing_health_address',
                    'tcp health probes require host and port',
                    *probe_path,
                ))
            if probe.kind is SystevisorHealthProbeKind.LOG_ACTIVITY and (
                    probe.channel is None or probe.max_quiet_secs is None
            ):
                errors.append(_systevisor_config_validation_error(
                    'missing_health_log_policy',
                    'log activity health probes require channel and max_quiet_secs',
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

    for cycle in _systevisor_config_validation_cycles(config):
        errors.append(_systevisor_config_validation_error(
            'dependency_cycle',
            f'dependency ordering cycle: {" -> ".join(cycle)}',
            'units',
        ))

    return tuple(errors)
