import abc
import datetime

from .... import lang
from ...api.core import Db
from ...api.queriers import Querier
from .config import SandboxesConfig
from .registry import SandboxRegistry


##


class SandboxBackend(lang.Abstract):
    """
    The dialect-specific half of the machinery: how to connect, what the safety checks look like on this server, how a
    sandbox (a schema here, a database there) is created and dropped, and the server-side coordination primitives - an
    advisory lock and a liveness probe. Everything else (leases, the registry, the reaper's algorithm) is generic.
    """

    @property
    @abc.abstractmethod
    def config(self) -> SandboxesConfig:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def open_db(self, run_id: str) -> Db:
        """A `Db` connected as the sandbox role to the sandbox database, stamped with the run's application name."""

        raise NotImplementedError

    @abc.abstractmethod
    def sandbox_db(self, run_id: str, name: str) -> Db:
        """A `Db` scoped to one sandbox: bare names resolve inside it, and nothing else is visible unqualified."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def guard(self, q: Querier) -> None:
        """Raises `SandboxSafetyError` unless this session is who and where the config says it must be."""

        raise NotImplementedError

    @abc.abstractmethod
    def ensure_registry(self, q: Querier, registry: SandboxRegistry) -> None:
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

    @abc.abstractmethod
    def run_is_live(self, q: Querier, run_id: str) -> bool:
        raise NotImplementedError

    #

    @abc.abstractmethod
    def create_sandbox(self, q: Querier, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def drop_sandbox(self, q: Querier, name: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def list_unregistered(self, q: Querier, registry: SandboxRegistry) -> list[str]:
        """Prefixed, non-internal sandbox objects with no registry row, read in a single snapshot."""

        raise NotImplementedError
