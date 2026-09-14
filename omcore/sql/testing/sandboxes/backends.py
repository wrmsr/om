import abc
import datetime
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ...api.core import Conn
from ...api.core import Db
from ...api.queriers import Querier
from .config import SandboxesConfig
from .registry import SandboxKind
from .registry import SandboxRecord
from .registry import SandboxRegistry


##


@dc.dataclass(frozen=True)
class UnregisteredSandbox(lang.Final):
    name: str
    kind: SandboxKind


class SandboxBackend(lang.Abstract):
    """
    The dialect-specific half of the machinery: how to connect, what the safety checks look like on this server, how a
    sandbox (a schema here, a database there, a directory elsewhere) is created and dropped, and the server-side
    coordination primitives - an advisory lock and a liveness signal. Everything else (leases, the registry's shape,
    the reaper's algorithm) is generic.
    """

    @property
    @abc.abstractmethod
    def config(self) -> SandboxesConfig:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def registry(self) -> SandboxRegistry:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def supported_kinds(self) -> ta.AbstractSet[SandboxKind]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def default_kind(self) -> SandboxKind:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def open_db(self, run_id: str) -> Db:
        """A `Db` connected as the sandbox role to the sandbox database, identifiable as the run's."""

        raise NotImplementedError

    @abc.abstractmethod
    def sandbox_db(self, run_id: str, name: str, kind: SandboxKind) -> Db:
        """A `Db` scoped to one sandbox: bare names resolve inside it, and nothing else is visible unqualified."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def guard(self, q: Querier) -> None:
        """Raises `SandboxSafetyError` unless this session is who and where the config says it must be."""

        raise NotImplementedError

    @abc.abstractmethod
    def ensure_registry(self, q: Querier) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def try_lock(self, q: Querier, name: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def lock(self, q: Querier, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def unlock(self, q: Querier, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def server_now(self, q: Querier) -> datetime.datetime:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def mark_run_live(self, q: Querier, run_id: str) -> None:
        """
        Makes the run visible as alive to reapers for as long as this session (or the process) lives. A backend that
        can read that off the session itself needs nothing here.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def unmark_run_live(self, q: Querier, run_id: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def run_is_live(self, q: Querier, run_id: str) -> bool:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def create_sandbox(self, conn: Conn, rec: SandboxRecord) -> None:
        """
        Registers and creates the sandbox: in one transaction where the backend allows, and otherwise registered first,
        so that whatever exists is always registered.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def drop_sandbox(self, q: Querier, name: str, kind: SandboxKind) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def list_unregistered(self, q: Querier) -> list[UnregisteredSandbox]:
        """Prefixed, non-internal sandbox objects with no registry row, read so a sandbox mid-creation is never one."""

        raise NotImplementedError
