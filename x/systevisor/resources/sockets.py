# @om-lite
# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import fcntl
import os
import socket
import stat
import typing as ta

from ..core.identities import SystevisorRunId
from ..runtime.processes import SystevisorChildContext
from ..runtime.processes import SystevisorChildModifier


_SYSTEVISOR_SOCKET_ACTIVATION_ENV_KEYS = ('LISTEN_PID', 'LISTEN_FDS', 'LISTEN_FDNAMES')
_SYSTEVISOR_SOCKET_DUPLICATE_FLOOR = 64


class SystevisorSocketActivationError(Exception):
    pass


@dc.dataclass(frozen=True)
class SystevisorInheritedSocket:
    state_schema_version: int
    name: str
    fd: int
    family: int
    socket_type: int


@dc.dataclass(frozen=True)
class SystevisorPreparedSocketMapping:
    name: str
    source_fd: int
    child_fd: int


class SystevisorInheritedSocketRegistry:
    def __init__(
            self,
            environment: ta.Optional[ta.MutableMapping[str, str]] = None,
            *,
            pid: ta.Optional[int] = None,
            fd_start: int = 3,
            consume_environment: bool = True,
    ) -> None:
        self._environment = os.environ if environment is None else environment
        self._pid = os.getpid() if pid is None else pid
        self._fd_start = fd_start
        had_activation_environment = any(key in self._environment for key in _SYSTEVISOR_SOCKET_ACTIVATION_ENV_KEYS)
        self._sockets = self._capture()
        self._closed = False
        if consume_environment and had_activation_environment:
            for key in _SYSTEVISOR_SOCKET_ACTIVATION_ENV_KEYS:
                self._environment.pop(key, None)

    @property
    def sockets(self) -> ta.Mapping[str, SystevisorInheritedSocket]:
        return self._sockets

    def _capture(self) -> ta.Dict[str, SystevisorInheritedSocket]:
        raw_pid = self._environment.get('LISTEN_PID')
        raw_count = self._environment.get('LISTEN_FDS')
        if raw_pid is None and raw_count is None:
            return {}
        try:
            listen_pid = int(raw_pid or '')
            count = int(raw_count or '')
        except ValueError as exc:
            raise SystevisorSocketActivationError('invalid LISTEN_PID/LISTEN_FDS') from exc
        if listen_pid != self._pid:
            return {}
        if count < 0 or count > 1024:
            raise SystevisorSocketActivationError('LISTEN_FDS must be between 0 and 1024')
        if count == 0:
            return {}

        raw_names = self._environment.get('LISTEN_FDNAMES')
        if raw_names is None:
            names = tuple(f'fd{self._fd_start + index}' for index in range(count))
        else:
            names = tuple(raw_names.split(':'))
            if len(names) != count or any(not name for name in names):
                raise SystevisorSocketActivationError('LISTEN_FDNAMES must name every inherited descriptor')
        if len(set(names)) != len(names):
            raise SystevisorSocketActivationError('LISTEN_FDNAMES contains duplicate names')

        inherited: ta.Dict[str, SystevisorInheritedSocket] = {}
        for index, name in enumerate(names):
            fd = self._fd_start + index
            try:
                fd_stat = os.fstat(fd)
            except OSError as exc:
                raise SystevisorSocketActivationError(f'inherited socket descriptor {fd} is not open') from exc
            if not stat.S_ISSOCK(fd_stat.st_mode):
                raise SystevisorSocketActivationError(f'inherited descriptor {fd} is not a socket')
            duplicate = socket.socket(fileno=os.dup(fd))
            try:
                family = duplicate.family
                socket_type = duplicate.type
            finally:
                duplicate.close()
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
            inherited[name] = SystevisorInheritedSocket(
                state_schema_version=1,
                name=name,
                fd=fd,
                family=family,
                socket_type=socket_type,
            )
        return inherited

    def require(self, names: ta.Iterable[str]) -> ta.Sequence[SystevisorInheritedSocket]:
        required: ta.List[SystevisorInheritedSocket] = []
        for name in names:
            try:
                required.append(self._sockets[name])
            except KeyError as exc:
                raise SystevisorSocketActivationError(f'unknown inherited socket: {name!r}') from exc
        return tuple(required)

    def close(self) -> None:
        if self._closed:
            return
        for inherited in self._sockets.values():
            try:
                os.close(inherited.fd)
            except OSError:
                pass
        self._sockets.clear()
        self._closed = True


class SystevisorInheritedSocketChildModifier(SystevisorChildModifier):
    def __init__(self, registry: SystevisorInheritedSocketRegistry) -> None:
        self._registry = registry
        self._prepared: ta.Dict[SystevisorRunId, ta.Sequence[SystevisorPreparedSocketMapping]] = {}

    def parent_prepare(self, context: SystevisorChildContext) -> None:
        names = context.spec.unit.resources.inherited_sockets
        if context.run_id <= 0 or not names:
            return
        inherited = self._registry.require(names)
        mappings: ta.List[SystevisorPreparedSocketMapping] = []
        try:
            for index, item in enumerate(inherited):
                source_fd = fcntl.fcntl(
                    item.fd,
                    fcntl.F_DUPFD_CLOEXEC,
                    _SYSTEVISOR_SOCKET_DUPLICATE_FLOOR,
                )
                mappings.append(SystevisorPreparedSocketMapping(
                    name=item.name,
                    source_fd=source_fd,
                    child_fd=3 + index,
                ))
        except BaseException:
            for mapping in mappings:
                os.close(mapping.source_fd)
            raise
        self._prepared[context.run_id] = tuple(mappings)

    def preserved_fds(self, context: SystevisorChildContext) -> ta.Sequence[int]:
        return tuple(mapping.source_fd for mapping in self._prepared.get(context.run_id, ()))

    def reserved_child_fds(self, context: SystevisorChildContext) -> ta.Sequence[int]:
        return tuple(mapping.child_fd for mapping in self._prepared.get(context.run_id, ()))

    def child_environment(self, context: SystevisorChildContext) -> ta.Mapping[str, str]:
        mappings = self._prepared.get(context.run_id, ())
        if not mappings:
            return {}
        return {
            'LISTEN_PID': str(os.getpid()),
            'LISTEN_FDS': str(len(mappings)),
            'LISTEN_FDNAMES': ':'.join(mapping.name for mapping in mappings),
        }

    def before_identity(self, context: SystevisorChildContext) -> None:
        mappings = self._prepared.get(context.run_id, ())
        try:
            for mapping in mappings:
                os.dup2(mapping.source_fd, mapping.child_fd)
                os.set_inheritable(mapping.child_fd, True)
        finally:
            for mapping in mappings:
                try:
                    os.close(mapping.source_fd)
                except OSError:
                    pass

    def _finish(self, run_id: SystevisorRunId) -> None:
        for mapping in self._prepared.pop(run_id, ()):
            try:
                os.close(mapping.source_fd)
            except OSError:
                pass

    def parent_spawned(self, context: SystevisorChildContext, pid: int) -> None:
        self._finish(context.run_id)

    def parent_spawn_failed(self, context: SystevisorChildContext) -> None:
        self._finish(context.run_id)
