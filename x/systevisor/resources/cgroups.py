# @om-lite
# ruff: noqa: UP006 UP007 UP045
import abc
import dataclasses as dc
import enum
import hashlib
import os
import os.path
import stat
import sys
import typing as ta

from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorCgroupConfig
from ..configs.snapshots import SystevisorConfigSnapshot
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..runtime.processes import SystevisorChildContext
from ..runtime.processes import SystevisorChildModifier


class SystevisorCgroupError(Exception):
    pass


class SystevisorCgroupRunStatus(enum.Enum):
    PREPARED = 'prepared'
    ACTIVE = 'active'
    RETIRED_POPULATED = 'retired_populated'
    REMOVED = 'removed'
    CLEANUP_FAILED = 'cleanup_failed'


@dc.dataclass(frozen=True)
class SystevisorCgroupPreparedRun:
    path: str
    procs_fd: int


@dc.dataclass(frozen=True)
class SystevisorCgroupCounters:
    cpu_usage_usec: ta.Optional[int] = None
    cpu_user_usec: ta.Optional[int] = None
    cpu_system_usec: ta.Optional[int] = None
    cpu_throttled_usec: ta.Optional[int] = None
    cpu_nr_throttled: ta.Optional[int] = None
    memory_current_bytes: ta.Optional[int] = None
    memory_peak_bytes: ta.Optional[int] = None
    memory_swap_current_bytes: ta.Optional[int] = None
    pids_current: ta.Optional[int] = None
    io_read_bytes: ta.Optional[int] = None
    io_write_bytes: ta.Optional[int] = None
    io_read_operations: ta.Optional[int] = None
    io_write_operations: ta.Optional[int] = None
    populated: ta.Optional[bool] = None


@dc.dataclass(frozen=True)
class SystevisorCgroupRunState:
    state_schema_version: int
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    path: str
    config: SystevisorCgroupConfig
    status: SystevisorCgroupRunStatus
    pid: ta.Optional[int] = None
    cleanup_error: ta.Optional[str] = None


class SystevisorCgroupFs(Abstract):
    @abc.abstractmethod
    def validate_root(self, root: str, configs: ta.Iterable[SystevisorCgroupConfig]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def create_run(
            self,
            root: str,
            name: str,
            config: SystevisorCgroupConfig,
    ) -> SystevisorCgroupPreparedRun:
        raise NotImplementedError

    @abc.abstractmethod
    def finish_spawn(self, prepared: SystevisorCgroupPreparedRun) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def abort_run(self, prepared: SystevisorCgroupPreparedRun) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def retire_run(self, path: str) -> ta.Tuple[bool, bool]:
        raise NotImplementedError

    @abc.abstractmethod
    def sample(self, path: str) -> SystevisorCgroupCounters:
        raise NotImplementedError


def _systevisor_cgroup_read_text(path: str) -> str:
    with open(path) as input_file:
        return input_file.read().strip()


def _systevisor_cgroup_read_optional_int(path: str) -> ta.Optional[int]:
    try:
        value = _systevisor_cgroup_read_text(path)
    except OSError:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _systevisor_cgroup_read_keyed(path: str) -> ta.Mapping[str, int]:
    try:
        value = _systevisor_cgroup_read_text(path)
    except OSError:
        return {}
    result: ta.Dict[str, int] = {}
    for line in value.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            result[parts[0]] = int(parts[1])
        except ValueError:
            continue
    return result


def _systevisor_cgroup_write_file(path: str, value: str) -> None:
    flags = os.O_WRONLY | getattr(os, 'O_CLOEXEC', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    try:
        data = value.encode('ascii')
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
    finally:
        os.close(fd)


class SystevisorSystemCgroupFs(SystevisorCgroupFs):
    def validate_root(self, root: str, configs: ta.Iterable[SystevisorCgroupConfig]) -> None:
        if sys.platform != 'linux':
            raise SystevisorCgroupError('cgroup v2 isolation is supported only on Linux')
        try:
            root_stat = os.stat(root, follow_symlinks=False)
        except OSError as exc:
            raise SystevisorCgroupError(f'cannot inspect delegated cgroup root {root!r}: {exc}') from exc
        if not stat.S_ISDIR(root_stat.st_mode):
            raise SystevisorCgroupError(f'delegated cgroup root is not a directory: {root!r}')
        for name in ('cgroup.controllers', 'cgroup.procs'):
            if not os.path.isfile(os.path.join(root, name)):
                raise SystevisorCgroupError(f'not a delegated cgroup v2 root; missing {name}: {root!r}')
        enabled_controllers = frozenset(
            _systevisor_cgroup_read_text(os.path.join(root, 'cgroup.subtree_control')).split(),
        )
        required_controllers: ta.Set[str] = set()
        for config in configs:
            if config.cpu_weight is not None or config.cpu_quota_usec is not None:
                required_controllers.add('cpu')
            if any(value is not None for value in (
                    config.memory_low_bytes,
                    config.memory_high_bytes,
                    config.memory_max_bytes,
            )):
                required_controllers.add('memory')
            if config.pids_max is not None:
                required_controllers.add('pids')
        missing_controllers = required_controllers - enabled_controllers
        if missing_controllers:
            raise SystevisorCgroupError(
                f'delegated cgroup root has disabled controllers: {", ".join(sorted(missing_controllers))}',
            )

    def create_run(
            self,
            root: str,
            name: str,
            config: SystevisorCgroupConfig,
    ) -> SystevisorCgroupPreparedRun:
        path = os.path.join(root, name)
        try:
            os.mkdir(path, 0o700)
        except OSError as exc:
            raise SystevisorCgroupError(f'cannot create run cgroup {path!r}: {exc}') from exc

        procs_fd = -1
        try:
            settings: ta.List[ta.Tuple[str, str]] = []
            if config.cpu_weight is not None:
                settings.append(('cpu.weight', f'{config.cpu_weight}\n'))
            if config.cpu_quota_usec is not None:
                settings.append(('cpu.max', f'{config.cpu_quota_usec} {config.cpu_period_usec}\n'))
            for file_name, value in (
                    ('memory.low', config.memory_low_bytes),
                    ('memory.high', config.memory_high_bytes),
                    ('memory.max', config.memory_max_bytes),
                    ('pids.max', config.pids_max),
            ):
                if value is not None:
                    settings.append((file_name, f'{value}\n'))
            for file_name, setting_value in settings:
                _systevisor_cgroup_write_file(os.path.join(path, file_name), setting_value)
            procs_fd = os.open(
                os.path.join(path, 'cgroup.procs'),
                os.O_WRONLY | getattr(os, 'O_CLOEXEC', 0) | getattr(os, 'O_NOFOLLOW', 0),
            )
            return SystevisorCgroupPreparedRun(path=path, procs_fd=procs_fd)
        except BaseException:
            if procs_fd >= 0:
                os.close(procs_fd)
            try:
                os.rmdir(path)
            except OSError:
                pass
            raise

    def finish_spawn(self, prepared: SystevisorCgroupPreparedRun) -> None:
        try:
            os.close(prepared.procs_fd)
        except OSError:
            pass

    def abort_run(self, prepared: SystevisorCgroupPreparedRun) -> None:
        self.finish_spawn(prepared)
        try:
            os.rmdir(prepared.path)
        except OSError:
            pass

    def retire_run(self, path: str) -> ta.Tuple[bool, bool]:
        events = _systevisor_cgroup_read_keyed(os.path.join(path, 'cgroup.events'))
        populated = bool(events.get('populated', 0))
        if populated:
            return False, True
        try:
            os.rmdir(path)
        except FileNotFoundError:
            return True, False
        except OSError as exc:
            raise SystevisorCgroupError(f'cannot remove empty run cgroup {path!r}: {exc}') from exc
        return True, False

    def sample(self, path: str) -> SystevisorCgroupCounters:
        cpu = _systevisor_cgroup_read_keyed(os.path.join(path, 'cpu.stat'))
        events = _systevisor_cgroup_read_keyed(os.path.join(path, 'cgroup.events'))
        io_values: ta.Dict[str, int] = {}
        try:
            io_text = _systevisor_cgroup_read_text(os.path.join(path, 'io.stat'))
        except OSError:
            io_text = ''
        for line in io_text.splitlines():
            for item in line.split()[1:]:
                key, separator, raw_value = item.partition('=')
                if not separator:
                    continue
                try:
                    io_values[key] = io_values.get(key, 0) + int(raw_value)
                except ValueError:
                    continue
        return SystevisorCgroupCounters(
            cpu_usage_usec=cpu.get('usage_usec'),
            cpu_user_usec=cpu.get('user_usec'),
            cpu_system_usec=cpu.get('system_usec'),
            cpu_throttled_usec=cpu.get('throttled_usec'),
            cpu_nr_throttled=cpu.get('nr_throttled'),
            memory_current_bytes=_systevisor_cgroup_read_optional_int(os.path.join(path, 'memory.current')),
            memory_peak_bytes=_systevisor_cgroup_read_optional_int(os.path.join(path, 'memory.peak')),
            memory_swap_current_bytes=_systevisor_cgroup_read_optional_int(os.path.join(path, 'memory.swap.current')),
            pids_current=_systevisor_cgroup_read_optional_int(os.path.join(path, 'pids.current')),
            io_read_bytes=io_values.get('rbytes'),
            io_write_bytes=io_values.get('wbytes'),
            io_read_operations=io_values.get('rios'),
            io_write_operations=io_values.get('wios'),
            populated=(bool(events['populated']) if 'populated' in events else None),
        )


def _systevisor_cgroup_run_name(context: SystevisorChildContext) -> str:
    identity_digest = hashlib.sha256(str(context.instance_id).encode('utf-8')).hexdigest()[:16]
    return f'sv-{int(context.run_id)}-{identity_digest}'


class SystevisorCgroupManager(SystevisorChildModifier):
    def __init__(self, cgroup_fs: SystevisorCgroupFs) -> None:
        self._cgroup_fs = cgroup_fs
        self._active_root: ta.Optional[str] = None
        self._candidate_root: ta.Optional[str] = None
        self._has_candidate = False
        self._prepared: ta.Dict[SystevisorRunId, SystevisorCgroupPreparedRun] = {}
        self._states: ta.Dict[SystevisorRunId, SystevisorCgroupRunState] = {}
        self._wake_callback: ta.Optional[ta.Callable[[], None]] = None

    @property
    def states(self) -> ta.Mapping[SystevisorRunId, SystevisorCgroupRunState]:
        return self._states

    def set_wake_callback(self, callback: ta.Callable[[], None]) -> None:
        self._wake_callback = callback

    def needs_sweep(self) -> bool:
        return any(state.status in {
            SystevisorCgroupRunStatus.RETIRED_POPULATED,
            SystevisorCgroupRunStatus.CLEANUP_FAILED,
        } for state in self._states.values())

    def prepare_config(self, snapshot: SystevisorConfigSnapshot) -> None:
        if self._has_candidate:
            raise SystevisorCgroupError('a cgroup configuration candidate is already prepared')
        root = snapshot.config.manager.cgroups.root
        configs = tuple(
            unit.resources.cgroup
            for unit in snapshot.config.units.values()
            if unit.resources.cgroup.enabled
        )
        if configs:
            if root is None:
                raise SystevisorCgroupError('cgroup-enabled units require a delegated root')
            self._cgroup_fs.validate_root(root, configs)
        self._candidate_root = root
        self._has_candidate = True

    def commit_config(self) -> None:
        if not self._has_candidate:
            raise SystevisorCgroupError('no cgroup configuration candidate is prepared')
        self._active_root = self._candidate_root
        self._candidate_root = None
        self._has_candidate = False

    def rollback_config(self) -> None:
        self._candidate_root = None
        self._has_candidate = False

    def _root(self) -> ta.Optional[str]:
        return self._candidate_root if self._has_candidate else self._active_root

    def parent_prepare(self, context: SystevisorChildContext) -> None:
        config = context.spec.unit.resources.cgroup
        if context.run_id <= 0 or not config.enabled:
            return
        root = self._root()
        if root is None:
            raise SystevisorCgroupError('cgroup configuration is not active')
        prepared = self._cgroup_fs.create_run(root, _systevisor_cgroup_run_name(context), config)
        self._prepared[context.run_id] = prepared
        self._states[context.run_id] = SystevisorCgroupRunState(
            state_schema_version=1,
            run_id=context.run_id,
            instance_id=context.instance_id,
            path=prepared.path,
            config=config,
            status=SystevisorCgroupRunStatus.PREPARED,
        )

    def preserved_fds(self, context: SystevisorChildContext) -> ta.Sequence[int]:
        prepared = self._prepared.get(context.run_id)
        return (prepared.procs_fd,) if prepared is not None else ()

    def before_identity(self, context: SystevisorChildContext) -> None:
        prepared = self._prepared.get(context.run_id)
        if prepared is None:
            return
        try:
            os.write(prepared.procs_fd, b'0\n')
        finally:
            os.close(prepared.procs_fd)

    def parent_spawned(self, context: SystevisorChildContext, pid: int) -> None:
        prepared = self._prepared.pop(context.run_id, None)
        if prepared is None:
            return
        self._cgroup_fs.finish_spawn(prepared)
        state = self._states[context.run_id]
        self._states[context.run_id] = dc.replace(
            state,
            status=SystevisorCgroupRunStatus.ACTIVE,
            pid=pid,
        )

    def parent_spawn_failed(self, context: SystevisorChildContext) -> None:
        prepared = self._prepared.pop(context.run_id, None)
        if prepared is None:
            return
        self._cgroup_fs.abort_run(prepared)
        self._states.pop(context.run_id, None)

    def _retire(self, run_id: SystevisorRunId) -> None:
        state = self._states.get(run_id)
        if state is None or state.status is SystevisorCgroupRunStatus.REMOVED:
            return
        try:
            removed, populated = self._cgroup_fs.retire_run(state.path)
        except (OSError, SystevisorCgroupError) as exc:
            self._states[run_id] = dc.replace(
                state,
                status=SystevisorCgroupRunStatus.CLEANUP_FAILED,
                cleanup_error=f'{type(exc).__name__}: {exc}',
            )
            return
        self._states[run_id] = dc.replace(
            state,
            status=(
                SystevisorCgroupRunStatus.REMOVED if removed else
                SystevisorCgroupRunStatus.RETIRED_POPULATED if populated else
                SystevisorCgroupRunStatus.CLEANUP_FAILED
            ),
            cleanup_error=None,
        )

    def parent_retired(self, context: SystevisorChildContext) -> None:
        self._retire(context.run_id)
        if self.needs_sweep() and self._wake_callback is not None:
            self._wake_callback()

    def sweep(self) -> None:
        for run_id, state in tuple(self._states.items()):
            if state.status in {
                    SystevisorCgroupRunStatus.RETIRED_POPULATED,
                    SystevisorCgroupRunStatus.CLEANUP_FAILED,
            }:
                self._retire(run_id)

    def sample(self, run_id: SystevisorRunId) -> ta.Optional[SystevisorCgroupCounters]:
        state = self._states.get(run_id)
        if state is None or state.status is SystevisorCgroupRunStatus.REMOVED:
            return None
        return self._cgroup_fs.sample(state.path)

    def prune(self, retained_run_ids: ta.AbstractSet[SystevisorRunId]) -> None:
        for run_id, state in tuple(self._states.items()):
            if state.status is SystevisorCgroupRunStatus.REMOVED and run_id not in retained_run_ids:
                del self._states[run_id]

    def rehydrate(
            self,
            states: ta.Iterable[SystevisorCgroupRunState],
            contexts: ta.Mapping[SystevisorRunId, SystevisorChildContext],
    ) -> None:
        if self._states or self._prepared:
            raise SystevisorCgroupError('cgroup manager can only be rehydrated before use')
        restored: ta.Dict[SystevisorRunId, SystevisorCgroupRunState] = {}
        for state in states:
            if state.state_schema_version != 1:
                raise SystevisorCgroupError(f'unsupported cgroup run schema: {state.state_schema_version}')
            if state.run_id in restored:
                raise SystevisorCgroupError(f'duplicate cgroup run: {state.run_id}')
            context = contexts.get(state.run_id)
            if state.status is SystevisorCgroupRunStatus.ACTIVE:
                if context is None:
                    raise SystevisorCgroupError(f'active cgroup has no owned process: {state.run_id}')
                if self._active_root is None:
                    raise SystevisorCgroupError('active cgroup has no configured delegated root')
                expected_path = os.path.join(self._active_root, _systevisor_cgroup_run_name(context))
                if os.path.abspath(state.path) != os.path.abspath(expected_path):
                    raise SystevisorCgroupError(f'cgroup path changed for run {state.run_id}')
                if state.config != context.spec.unit.resources.cgroup or state.pid is None:
                    raise SystevisorCgroupError(f'cgroup configuration changed for run {state.run_id}')
            restored[state.run_id] = state
        self._states = restored
