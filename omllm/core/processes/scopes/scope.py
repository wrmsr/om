"""
A `ProcessScope` is a node in the lifetime tree. It owns processes (and child scopes) and tears them down when it
closes: child scopes first (reverse creation order, sequentially), then all its own processes concurrently. Moving a
handle between scopes (`adopt`) is how a tool-call process becomes a background one.

The scope itself is loop-agnostic; concurrency and spawning are delegated to `ScopeOps`, implemented by the manager.
"""
import abc
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ..handles import Process
from ..spool.spool import SpoolRead
from ..types.errors import ProcessTimeoutError
from ..types.errors import ScopeClosedError
from ..types.ids import ProcessId
from ..types.options import ProcessOption
from ..types.options import ProcessOptions
from ..types.options import RunTimeout
from ..types.options import layer_options
from ..types.specs import ProcessSpec
from .policies import DEFAULT_SCOPE_CLOSE_POLICY
from .policies import ScopeClosePolicy


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScopeCloseResult:
    num_processes: int
    num_abandoned: int = 0
    errors: ta.Sequence[Exception] = ()


class ScopeOps(lang.Abstract):
    """The manager-side implementation hooks a scope needs."""

    @abc.abstractmethod
    def spawn(self, scope: ProcessScope, spec: ProcessSpec, options: ProcessOptions) -> ta.Awaitable[Process]:
        raise NotImplementedError

    @abc.abstractmethod
    def close_processes(
            self,
            processes: ta.Sequence[Process],
            policy: ScopeClosePolicy,
    ) -> ta.Awaitable[ScopeCloseResult]:
        raise NotImplementedError

    @abc.abstractmethod
    def reparent(self, process: Process, new_scope: ProcessScope) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def scope_opened(self, scope: ProcessScope) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def scope_closed(self, scope: ProcessScope, result: ScopeCloseResult) -> ta.Awaitable[None]:
        raise NotImplementedError


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessRun:
    """The result of `ProcessScope.run`: the process has exited and been fully closed; its spool remains readable."""

    process: Process
    returncode: int
    output: SpoolRead

    @property
    def stdout(self) -> bytes:
        return self.output.data(1)

    @property
    def stderr(self) -> bytes:
        return self.output.data(2)


##


class ProcessScope:
    def __init__(
            self,
            name: str,
            *,
            parent: ProcessScope | None,
            ops: ScopeOps,
            options: ta.Iterable[ProcessOption] | None = None,
            close_policy: ScopeClosePolicy | None = None,
    ) -> None:
        super().__init__()

        self._name = check.non_empty_str(name)
        self._parent = parent
        self._ops = ops
        self._own_options: ProcessOptions = layer_options(None, options)
        self._close_policy = close_policy

        self._children: dict[str, ProcessScope] = {}
        self._processes: dict[ProcessId, Process] = {}

        self._closing = False
        self._closed = False

        if parent is not None:
            check.state(not parent._closing)  # noqa: SLF001
            check.not_in(name, parent._children)  # noqa: SLF001
            parent._children[name] = self  # noqa: SLF001

        self._path: tuple[str, ...] = (*(parent._path if parent is not None else ()), name)  # noqa: SLF001

        ops.scope_opened(self)

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'{"/".join(self._path)!r}, '
            f'processes={len(self._processes)}, '
            f'children={len(self._children)}'
            f')'
        )

    #

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> ta.Sequence[str]:
        return self._path

    @property
    def parent(self) -> ProcessScope | None:
        return self._parent

    @property
    def children(self) -> ta.Mapping[str, ProcessScope]:
        return self._children

    @property
    def processes(self) -> ta.Mapping[ProcessId, Process]:
        return self._processes

    @property
    def closing(self) -> bool:
        return self._closing

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def options(self) -> ProcessOptions:
        """Effective option defaults for spawns in this scope: ancestors' layered with this scope's own."""

        if (p := self._parent) is None:
            return self._own_options
        return layer_options(p.options, self._own_options)

    @property
    def close_policy(self) -> ScopeClosePolicy:
        if (cp := self._close_policy) is not None:
            return cp
        if (p := self._parent) is not None:
            return p.close_policy
        return DEFAULT_SCOPE_CLOSE_POLICY

    def ancestors(self) -> ta.Iterator[ProcessScope]:
        p = self._parent
        while p is not None:
            yield p
            p = p._parent  # noqa: SLF001

    def is_ancestor_of(self, other: ProcessScope) -> bool:
        return any(a is self for a in other.ancestors())

    #

    def _check_open(self) -> None:
        if self._closing or self._closed:
            raise ScopeClosedError('/'.join(self._path))

    def child(
            self,
            name: str,
            *,
            options: ta.Iterable[ProcessOption] | None = None,
            close_policy: ScopeClosePolicy | None = None,
    ) -> ProcessScope:
        self._check_open()
        return ProcessScope(
            name,
            parent=self,
            ops=self._ops,
            options=options,
            close_policy=close_policy,
        )

    #

    async def spawn(self, spec: ProcessSpec, *options: ProcessOption) -> Process:
        self._check_open()
        opts = layer_options(self.options, options)
        proc = await self._ops.spawn(self, spec, opts)
        return proc

    async def run(
            self,
            spec: ProcessSpec,
            *options: ProcessOption,
            timeout: float | None = None,
    ) -> ProcessRun:
        """
        Spawns, waits for exit (bounded by `timeout` or a `RunTimeout` option), then fully closes the handle - sweeping
        the process group per its TerminationPolicy - and returns the collected output.
        """

        proc = await self.spawn(spec, *options)
        if timeout is None and (rt := proc.options.get(RunTimeout)) is not None:
            timeout = rt.v
        try:
            try:
                rc = await proc.wait(timeout)
            except ProcessTimeoutError:
                await proc.aclose()
                raise
            await proc.aclose()
        except BaseException:
            await proc.aclose()
            raise
        return ProcessRun(
            process=proc,
            returncode=rc,
            output=proc.spool.read_available(0),
        )

    #

    def adopt(self, process: Process) -> None:
        """Moves a live handle from its current scope into this one (typically an ancestor: 'background this')."""

        self._check_open()
        old = process.scope
        if old is self:
            return
        check.in_(process.id, old._processes)  # noqa: SLF001
        self._ops.reparent(process, self)

    def _register(self, process: Process) -> None:
        check.not_in(process.id, self._processes)
        self._processes[process.id] = process

    def _unregister(self, process: Process) -> None:
        self._processes.pop(process.id, None)

    #

    async def aclose(self) -> None:
        if self._closed:
            return
        if self._closing:
            return
        self._closing = True

        errors: list[Exception] = []
        for child in reversed(list(self._children.values())):
            try:
                await child.aclose()
            except Exception as e:  # noqa
                errors.append(e)

        procs = list(self._processes.values())
        try:
            result = await self._ops.close_processes(procs, self.close_policy)
        except Exception as e:  # noqa
            result = ScopeCloseResult(num_processes=len(procs), errors=[e])
        errors.extend(result.errors)

        self._processes.clear()
        if (p := self._parent) is not None:
            p._children.pop(self._name, None)  # noqa: SLF001
        self._closed = True

        await self._ops.scope_closed(self, dc.replace(result, errors=errors))

        if errors:
            if len(errors) == 1:
                raise errors[0]
            raise ExceptionGroup(f'Errors closing process scope {"/".join(self._path)!r}', errors)

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
