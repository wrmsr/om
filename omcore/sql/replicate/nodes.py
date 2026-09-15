import typing as ta
import uuid

from ... import check
from ... import lang
from ..api.core import Db
from ..qualifiedname import QualifiedName
from ..tabledefs.tabledefs import TableDef
from .errors import ReplicationInstallError
from .names import cursor_table_name
from .names import log_table_name
from .names import node_table_name
from .names import shadow_name


if ta.TYPE_CHECKING:
    from .backends.base import ReplicateBackend


##


class Node(lang.Final):
    """
    A participating database: a name the config refers to, a live `Db`, and the dialect's replicate backend. The node
    qualifies the schema's bare table names for its own layout, and learns its own id from its node table once
    installed.
    """

    def __init__(
            self,
            name: str,
            db: Db,
            backend: ReplicateBackend,
            *,
            qualifier: ta.Sequence[str] = (),
            no_log: bool = False,
    ) -> None:
        super().__init__()

        self._name = check.non_empty_str(name)
        self._db = db
        self._backend = backend
        self._qualifier = tuple(qualifier)
        self._log = not no_log

        self._node_id: uuid.UUID | None = None

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._name!r})'

    @property
    def name(self) -> str:
        return self._name

    @property
    def db(self) -> Db:
        return self._db

    @property
    def backend(self) -> ReplicateBackend:
        return self._backend

    @property
    def qualifier(self) -> ta.Sequence[str]:
        return self._qualifier

    @property
    def log(self) -> bool:
        """Whether this node keeps a change log for links to tail; the sweep works either way."""

        return self._log

    #

    def qualify(self, last: str) -> QualifiedName:
        return QualifiedName((*self._qualifier, last))

    def table_name(self, td: TableDef) -> QualifiedName:
        return self.qualify(td.name.last)

    def shadow_name(self, td: TableDef) -> QualifiedName:
        return shadow_name(self.table_name(td))

    @property
    def node_table(self) -> QualifiedName:
        return node_table_name(self._qualifier)

    @property
    def cursor_table(self) -> QualifiedName:
        return cursor_table_name(self._qualifier)

    @property
    def log_table(self) -> QualifiedName:
        return log_table_name(self._qualifier)

    #

    @property
    def node_id(self) -> uuid.UUID:
        if (nid := self._node_id) is None:
            with self._db.connect() as conn:
                nid = self._backend.read_node_id(conn, self.node_table)
            if nid is None:
                raise ReplicationInstallError(f'{self!r} is not installed')
            self._node_id = nid
        return nid

    def _set_node_id(self, nid: uuid.UUID) -> None:
        self._node_id = nid
