import abc
import datetime
import enum
import typing as ta

from .... import check
from .... import dataclasses as dc
from .... import lang
from ...api import querierfuncs as qf
from ...api.queriers import Querier
from ...dtypes import DATETIME
from ...dtypes import STRING
from ...qualifiedname import QualifiedName
from ...qualifiedname import qn
from ...queries import Q
from ...tabledefs.elements import Column
from ...tabledefs.elements import Elements
from ...tabledefs.elements import Index
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.tabledefs import TableDef
from .config import SandboxesConfig


##


class SandboxKind(enum.Enum):
    SCHEMA = 'schema'
    DATABASE = 'database'


@dc.dataclass(frozen=True, kw_only=True)
class SandboxRecord(lang.Final):
    name: str
    kind: SandboxKind
    run_id: str
    owner: str
    created_at: datetime.datetime
    expires_at: datetime.datetime


##


class TimestampCodec(lang.Abstract):
    """
    How a lease timestamp crosses the driver boundary. The registry compares timestamps in python against the server's
    own clock, so all that matters is that what comes back equals (or sorts consistently with) what went in.
    """

    @abc.abstractmethod
    def encode(self, dt: datetime.datetime) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, v: ta.Any) -> datetime.datetime:
        raise NotImplementedError


class IdentityTimestampCodec(TimestampCodec, lang.Final):
    def encode(self, dt: datetime.datetime) -> ta.Any:
        return dt

    def decode(self, v: ta.Any) -> datetime.datetime:
        return check.isinstance(v, datetime.datetime)


class IsoTimestampCodec(TimestampCodec, lang.Final):
    """For backends that store timestamps as text (sqlite)."""

    def encode(self, dt: datetime.datetime) -> ta.Any:
        return dt.isoformat()

    def decode(self, v: ta.Any) -> datetime.datetime:
        return datetime.datetime.fromisoformat(check.isinstance(v, str))


class WholeSecondsTimestampCodec(TimestampCodec, lang.Final):
    """
    For backends whose default timestamp column has no fractional seconds (mysql). Truncating rather than letting the
    server round keeps a stored lease at or before the instant it was computed from, so a zero ttl still means expired.
    """

    def encode(self, dt: datetime.datetime) -> ta.Any:
        return dt.replace(microsecond=0)

    def decode(self, v: ta.Any) -> datetime.datetime:
        return check.isinstance(v, datetime.datetime)


##


class SandboxRegistry(lang.Final):
    """
    The one shared table every run reads and writes: a row per sandbox carrying its lease. A row is inserted before (or
    in the same transaction as) the creation of the sandbox, so anything that exists is registered, and a registered
    name whose object is gone is harmless to reap again. Timestamps are the server's, never the client's, so leases
    compare consistently across machines.
    """

    TABLE_NAME: ta.ClassVar[str] = 'sandboxes'

    def __init__(
            self,
            cfg: SandboxesConfig,
            *,
            table_name: QualifiedName | None = None,
            timestamp_codec: TimestampCodec | None = None,
    ) -> None:
        super().__init__()

        self._cfg = cfg
        self._table_name = table_name if table_name is not None else qn(cfg.registry_schema, self.TABLE_NAME)
        self._ts = timestamp_codec if timestamp_codec is not None else IdentityTimestampCodec()

        self._t = Q.n(tuple(self._table_name))

    @property
    def table_name(self) -> QualifiedName:
        return self._table_name

    @property
    def table_def(self) -> TableDef:
        return TableDef(self._table_name, Elements(
            Column('name', STRING),
            PrimaryKey(['name']),
            Column('kind', STRING),
            Column('run_id', STRING),
            Column('owner', STRING),
            Column('created_at', DATETIME),
            Column('expires_at', DATETIME),
            Index(['run_id']),
            Index(['expires_at']),
        ))

    #

    _COLUMNS: ta.ClassVar[ta.Sequence[str]] = (
        'name',
        'kind',
        'run_id',
        'owner',
        'created_at',
        'expires_at',
    )

    def _select(self) -> ta.Any:
        return Q.select(
            [Q.i(c) for c in self._COLUMNS],
            self._t,
            order_by=[(Q.i.created_at, 'asc'), (Q.i.name, 'asc')],
        )

    def _record(self, d: ta.Mapping[str, ta.Any]) -> SandboxRecord:
        return SandboxRecord(
            name=d['name'],
            kind=SandboxKind(d['kind']),
            run_id=d['run_id'],
            owner=d['owner'],
            created_at=self._ts.decode(d['created_at']),
            expires_at=self._ts.decode(d['expires_at']),
        )

    def list_all(self, q: Querier) -> list[SandboxRecord]:
        return [self._record(r.to_dict()) for r in qf.query_all(q, self._select())]

    def list_run(self, q: Querier, run_id: str) -> list[SandboxRecord]:
        stmt = dc.replace(self._select(), where=Q.eq(Q.i.run_id, Q.p.run_id))
        return [self._record(r.to_dict()) for r in qf.query_all(q, stmt, {Q.p.run_id: run_id})]

    def insert(self, q: Querier, rec: SandboxRecord) -> None:
        qf.exec(
            q,
            Q.insert(
                [Q.i(c) for c in self._COLUMNS],
                self._t,
                [Q.p(c) for c in self._COLUMNS],
            ),
            {
                Q.p.name: rec.name,
                Q.p.kind: rec.kind.value,
                Q.p.run_id: rec.run_id,
                Q.p.owner: rec.owner,
                Q.p.created_at: self._ts.encode(rec.created_at),
                Q.p.expires_at: self._ts.encode(rec.expires_at),
            },
        )

    def delete(self, q: Querier, name: str) -> None:
        qf.exec(q, Q.delete(self._t, where=Q.eq(Q.i.name, Q.p.name)), {Q.p.name: name})

    def renew_run(self, q: Querier, run_id: str, expires_at: datetime.datetime) -> None:
        qf.exec(
            q,
            Q.update(self._t, [(Q.i.expires_at, Q.p.expires_at)], where=Q.eq(Q.i.run_id, Q.p.run_id)),
            {Q.p.expires_at: self._ts.encode(expires_at), Q.p.run_id: run_id},
        )
