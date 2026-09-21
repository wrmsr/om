import abc
import typing as ta

from ... import collections as col
from ... import dataclasses as dc
from ... import lang
from ... import marshal as msh
from ... import typedvalues as tv
from ..dtypes import Dtype
from ..qualifiedname import QualifiedName
from .options import ColumnOptions
from .options import IndexOptions
from .predicates import Predicate
from .predicates import as_opt_predicate
from .values import SimpleValue


##


class Element(tv.TypedValue, lang.Abstract, lang.Sealed):
    pass


##


@dc.dataclass(frozen=True)
class Column(Element, lang.Final):
    name: str
    type: Dtype

    _: dc.KW_ONLY

    nullable: bool = False
    default: lang.Maybe[SimpleValue] = lang.nothing()

    # TODO: marshal once concrete (backend) option types exist - open families have no poly impls yet.
    options: ColumnOptions = (
        dc.xfield(default_factory=tv.TypedValues, coerce=tv.as_collection) |
        msh.dc_field_options(no_marshal=True, no_unmarshal=True)
    )


@dc.dataclass(frozen=True)
class PrimaryKey(Element, tv.UniqueTypedValue, lang.Final):
    columns: ta.Sequence[str] = dc.xfield(coerce=col.seq)  # noqa


@dc.dataclass(frozen=True)
class Index(Element, lang.Final):
    columns: ta.Sequence[str] = dc.xfield(coerce=col.seq)  # noqa

    _: dc.KW_ONLY

    name: str | None = None

    unique: bool = False
    where: Predicate | None = (
        dc.xfield(None, coerce=as_opt_predicate) |
        msh.dc_field_options(no_marshal=True, no_unmarshal=True)
    )

    options: IndexOptions = (
        dc.xfield(default_factory=tv.TypedValues, coerce=tv.as_collection) |
        msh.dc_field_options(no_marshal=True, no_unmarshal=True)
    )


def index_name(table_name: QualifiedName, e: Index) -> str:
    """
    The effective name an index is created under: its explicit `name`, or the deterministic auto-name derived from the
    table and columns. Shared by the DDL renderer and the differ so an unnamed in-code index matches its reflected,
    db-named counterpart (otherwise diffing would drop-and-recreate it on every run). Only the table's own (last) name
    part participates - an index always lives in its table's schema, so the qualification adds nothing.
    """

    return e.name if e.name is not None else '__'.join([table_name.last, 'index', *e.columns])


##


@dc.dataclass(frozen=True)
class Trigger(Element, lang.Abstract):
    """
    A trigger tabledefs knows by name only. Trigger bodies are deliberately never modeled - there is no cross-dialect
    trigger language - so a concrete trigger type is pure data, and a per-backend `TriggerRenderer` plugin supplies its
    SQL. The family is open: `UpdatedAtTrigger` is built in, but any package may define its own trigger type (and
    register renderers for it with the backend renderer) without tabledefs knowing of it.

    Names carry ownership. Every type derives its trigger names from a per-table prefix and claims exactly the names
    under that prefix: the differ only ever drops a reflected trigger whose name is claimed by a type present in the
    in-code definition, so one use case's triggers are never clobbered by another's. A change to a trigger's body is
    surfaced by versioning its name, which the differ then sees as a drop and an add. Since trigger names are
    database-global on sqlite and mysql (not per-table as on postgres), a prefix must incorporate the table name.
    """

    @classmethod
    @abc.abstractmethod
    def trigger_name_prefix(cls, table_name: QualifiedName) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def trigger_name_suffix(self) -> str:
        raise NotImplementedError

    def trigger_name(self, table_name: QualifiedName) -> str:
        return self.trigger_name_prefix(table_name) + self.trigger_name_suffix()

    @classmethod
    def owns_trigger_name(cls, table_name: QualifiedName, name: str) -> bool:
        return name.startswith(cls.trigger_name_prefix(table_name))


@dc.dataclass(frozen=True)
class OpaqueTrigger(Trigger, lang.Final):
    """A trigger known only by name, as reflected from a live database. It can be diffed against but never created."""

    name: str

    @classmethod
    def trigger_name_prefix(cls, table_name: QualifiedName) -> str:  # noqa: ARG003
        return ''

    def trigger_name_suffix(self) -> str:
        return self.name

    @classmethod
    def owns_trigger_name(cls, table_name: QualifiedName, name: str) -> bool:  # noqa: ARG003
        return False


##


@dc.dataclass(frozen=True)
class IdIntegerPrimaryKey(Element, lang.Final):
    pass


#


@dc.dataclass(frozen=True)
class CreatedAt(Element, lang.Final):
    pass


@dc.dataclass(frozen=True)
class UpdatedAt(Element, lang.Final):
    pass


@dc.dataclass(frozen=True)
class UpdatedAtTrigger(Trigger, lang.Final):
    """
    Keeps a column as the time its row was last updated, by whoever it was that updated it, on every dialect alike:

     - An update which changes the column is taken at its word. It is from someone who knows when the row was really
       updated - a copy of it being brought up to date with its owner's, say - and the column is theirs to set.
     - One which does not is stamped - with the time, or with the least the dialect can tell apart past what the column
       already held should the time be no later than that. So the column only ever goes up as its row is updated, no
       two versions of a row carry the same time, and - which is the point of that - a version of a row arriving
       wherever an older one is kept always changes the column, and so is taken at its word.
    """

    column: str

    @classmethod
    def trigger_name_prefix(cls, table_name: QualifiedName) -> str:
        return f'{table_name.last}__trigger__updated_at__'

    def trigger_name_suffix(self) -> str:
        return self.column


@dc.dataclass(frozen=True)
class CreatedAtUpdatedAt(Element, lang.Final):
    pass


##


Elements: ta.TypeAlias = tv.TypedValues[Element]
