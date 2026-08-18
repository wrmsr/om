# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from ..configs.models import SystevisorOutputConfig
from ..configs.models import SystevisorOutputMode
from ..configs.models import SystevisorUnitConfig
from .states import SystevisorUnitChangeKind


@dc.dataclass(frozen=True)
class SystevisorUnitChange:
    kind: SystevisorUnitChangeKind
    changed_paths: ta.Sequence[str]
    restart_paths: ta.Sequence[str]
    live_paths: ta.Sequence[str]


def _systevisor_changes_output_topology(output: SystevisorOutputConfig) -> str:
    if output.mode in {SystevisorOutputMode.CAPTURE, SystevisorOutputMode.FILE, SystevisorOutputMode.STDOUT}:
        return 'pipe'
    return output.mode.value


def systevisor_classify_unit_change(old: SystevisorUnitConfig, new: SystevisorUnitConfig) -> SystevisorUnitChange:
    restart_paths: ta.List[str] = []
    live_paths: ta.List[str] = []

    restart_candidates: ta.Sequence[ta.Tuple[str, ta.Any, ta.Any]] = (
            ('exec', old.exec, new.exec),
            ('identity', old.identity, new.identity),
            ('kind', old.kind, new.kind),
            ('stdio.stdin', old.stdio.stdin, new.stdio.stdin),
            ('stdio.redirect_stderr', old.stdio.redirect_stderr, new.stdio.redirect_stderr),
            ('resources.cgroup', old.resources.cgroup, new.resources.cgroup),
            ('resources.namespaces', old.resources.namespaces, new.resources.namespaces),
            ('resources.inherited_sockets', old.resources.inherited_sockets, new.resources.inherited_sockets),
    )
    for path, old_value, new_value in restart_candidates:
        if old_value != new_value:
            restart_paths.append(path)

    for channel_name, old_output, new_output in (
            ('stdout', old.stdio.stdout, new.stdio.stdout),
            ('stderr', old.stdio.stderr, new.stdio.stderr),
    ):
        if old_output == new_output:
            continue
        path = f'stdio.{channel_name}'
        if _systevisor_changes_output_topology(old_output) != _systevisor_changes_output_topology(new_output):
            restart_paths.append(path)
        else:
            live_paths.append(path)

    live_candidates: ta.Sequence[ta.Tuple[str, ta.Any, ta.Any]] = (
            ('replicas', old.replicas, new.replicas),
            ('replica_start', old.replica_start, new.replica_start),
            ('autostart', old.autostart, new.autostart),
            ('priority', old.priority, new.priority),
            ('restart', old.restart, new.restart),
            ('stop', old.stop, new.stop),
            ('dependencies', old.dependencies, new.dependencies),
            ('health', old.health, new.health),
            ('resources.observe', old.resources.observe, new.resources.observe),
            ('tags', old.tags, new.tags),
    )
    for path, old_value, new_value in live_candidates:
        if old_value != new_value:
            live_paths.append(path)

    changed_paths = (*restart_paths, *live_paths)
    if restart_paths:
        kind = SystevisorUnitChangeKind.RESTART
    elif live_paths:
        kind = SystevisorUnitChangeKind.LIVE
    else:
        kind = SystevisorUnitChangeKind.NONE
    return SystevisorUnitChange(
        kind=kind,
        changed_paths=changed_paths,
        restart_paths=tuple(restart_paths),
        live_paths=tuple(live_paths),
    )
