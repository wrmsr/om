"""
`ProcessManager` is the one top-level object: it owns the root `ProcessScope`, the registry of live handles, and the
event bus. There is no global instance - it is created (usually by an injector), started, used, and closed; a new one
may then be created. The interface is loop-agnostic. `base.py` holds the implementation-agnostic bulk of the manager
(`BaseProcessManager`); `../asyncio/` fills in the asyncio-specific primitives, and a threads-backed implementation with
the same async interface is an intended future extension.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...eventbus import EventPublisher
from ..handles import Process
from ..scopes.policies import ScopeClosePolicy
from ..scopes.scope import ProcessScope
from ..types.events import ProcessEvent
from ..types.ids import ProcessId
from ..types.options import ProcessOption


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ManagerConfig:
    # Interpreter argv prefix used to run the spawn shim. None means the current `sys.executable`.
    shim_python: ta.Sequence[str] | None = None

    # Directory under which spill files live. None means a manager-owned temp dir, removed on close.
    spill_dir: str | None = None

    # Manager-wide default options; scopes and spawns layer over these.
    default_options: ta.Sequence[ProcessOption] = ()

    close_policy: ScopeClosePolicy | None = None

    # Bound on the exec handshake - a shim that neither execs nor fails within this is killed.
    spawn_timeout_s: float = 30.


##


class ProcessManager(EventPublisher[ProcessEvent], lang.Abstract):
    @property
    @abc.abstractmethod
    def config(self) -> ManagerConfig:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def root(self) -> ProcessScope:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def processes(self) -> ta.Mapping[ProcessId, Process]:
        """All live (unreaped, unabandoned) handles across all scopes."""

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def started(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
