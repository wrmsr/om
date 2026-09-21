import abc
import io
import typing as ta

from ... import check
from ... import collections as col
from ... import dataclasses as dc
from ... import lang
from ..dtypes import Integer
from ..qualifiedname import QualifiedName
from ..syntax import QuoteStyle
from ..syntax import QuoteStyles
from .diffing import AddColumn
from .diffing import AddIndex
from .diffing import AddTrigger
from .diffing import AlterColumn
from .diffing import DropColumn
from .diffing import DropIndex
from .diffing import DropTrigger
from .diffing import MigrationOp
from .elements import Column
from .elements import Index
from .elements import PrimaryKey
from .elements import Trigger
from .elements import index_name
from .lower import clustered_index
from .predicates import And
from .predicates import Compare
from .predicates import IsNull
from .predicates import Not
from .predicates import Or
from .predicates import Predicate
from .predicates import RawPredicate
from .predicates import SimplePredicateValue
from .tabledefs import TableDef
from .triggers import TriggerRenderer
from .values import Now
from .values import SimpleValue


##


class UnsupportedMigrationError(Exception):
    pass


class IdentifierTooLongError(Exception):
    def __init__(self, name: str, max_length: int) -> None:
        super().__init__(f'identifier {name!r} exceeds the backend limit of {max_length} bytes')

        self.name = name
        self.max_length = max_length


class UnknownTriggerTypeError(Exception):
    def __init__(self, cls: type[Trigger]) -> None:
        super().__init__(f'no TriggerRenderer is registered for trigger type {cls.__qualname__}')

        self.cls = cls


@dc.dataclass()
class RenderColumn:
    name: str
    type: str

    _: dc.KW_ONLY

    not_null: bool = False
    default: str | None = None
    identity: str = ''
    extra: ta.Sequence[str] = ()


class Renderer(lang.Abstract):
    """
    Standard CREATE-TABLE assembly shared by all backends. Dialects override only the small set of hooks below; the
    column/constraint/index layout and the identity-column detection are shared so backends do not duplicate them.

    Every identifier is quoted, always, through the dialect's quote style, and a table name is rendered exactly as
    qualified in its definition. Trigger SQL is never assembled here: it is dispatched by trigger type to the registered
    `TriggerRenderer` plugins - the backend's built-ins plus whatever the caller passes in.
    """

    @dc.dataclass(frozen=True, kw_only=True)
    class CreateOptions:
        drop_if_exists: bool = False
        if_not_exists: bool = False

    def __init__(
            self,
            *,
            trigger_renderers: ta.Sequence[TriggerRenderer] = (),
    ) -> None:
        super().__init__()

        by_cls: dict[type[Trigger], TriggerRenderer] = {}
        for tr in [*self.builtin_trigger_renderers(), *trigger_renderers]:
            check.not_in(tr.trigger_cls, by_cls)
            by_cls[tr.trigger_cls] = tr
        self._trigger_renderers_by_cls = by_cls

    def builtin_trigger_renderers(self) -> ta.Sequence[TriggerRenderer]:
        return ()

    def trigger_renderer(self, cls: type[Trigger]) -> TriggerRenderer:
        try:
            return self._trigger_renderers_by_cls[cls]
        except KeyError:
            raise UnknownTriggerTypeError(cls) from None

    ##
    # identifiers

    ident_quote_style: QuoteStyle = QuoteStyles.DOUBLE

    # Some backends (postgres) silently truncate an over-long identifier, which can fold two names into one; refusing
    # up front is far safer.
    max_ident_length: int | None = None

    def quote_ident(self, s: str) -> str:
        check.non_empty_str(s)
        if (ml := self.max_ident_length) is not None and len(s.encode('utf-8')) > ml:
            raise IdentifierTooLongError(s, ml)
        return self.ident_quote_style.quote(s)

    def qname(self, qn: QualifiedName) -> str:
        return '.'.join(self.quote_ident(p) for p in qn)

    ##
    # hooks

    @abc.abstractmethod
    def column_type(self, c: Column, *, is_identity: bool, indexed: bool = False) -> str:
        raise NotImplementedError

    # An integer of unspecified width gets the backend's default, except an identity column, which should never run out
    # of ids.
    default_integer_bits: int = 32
    identity_integer_bits: int = 64

    def integer_bits(self, t: Integer, *, is_identity: bool) -> int:
        if t.bits is not None:
            return t.bits
        return self.identity_integer_bits if is_identity else self.default_integer_bits

    def column_identity_sql(self, c: Column) -> str:
        return ''

    def column_option_sql(self, c: Column) -> list[str]:
        # Base supports no column options; any present trips the fail-closed consumer.
        with c.options.consume():
            pass
        return []

    def consume_table_options(self, tbl: TableDef) -> None:
        # Base supports no table options.
        with tbl.options.consume():
            pass

    def render_default(self, v: SimpleValue) -> str:
        if isinstance(v, Now):
            return 'current_timestamp'
        else:
            raise TypeError(v)

    def table_suffixes(self, tbl: TableDef, identity_column: str | None) -> list[str]:
        return []

    def physical_table(self, tbl: TableDef) -> TableDef:
        """
        The table as this backend holds it, where that is not as it is defined - a clustered one, on a backend which can
        only cluster on the primary key. It is the physical table which is created, and which reflection will see, so it
        is the one a definition is diffed as; its triggers though are rendered against the definition.
        """

        clustered_index(tbl)
        return tbl

    def drop_statement(self, tbl: TableDef) -> str:
        return f'drop table if exists {self.qname(tbl.name)}'

    def index_statement(self, table_name: QualifiedName, e: Index, opts: CreateOptions) -> str:
        idx_name = index_name(table_name, e)

        with e.options.consume():
            pass  # base supports no index options

        out = io.StringIO()
        out.write('create ')
        if e.unique:
            out.write('unique ')
        out.write('index ')
        if opts.if_not_exists:
            out.write('if not exists ')
        out.write(
            f'{self.quote_ident(idx_name)} on '
            f'{self.qname(table_name)} '
            f'({", ".join(self.quote_ident(c) for c in e.columns)})',
        )
        if e.where is not None:
            out.write(f' where {self.render_predicate(e.where)}')
        out.write('\n')
        return out.getvalue()

    def index_statements(self, table_name: QualifiedName, e: Index, opts: CreateOptions) -> list[str]:
        # All it takes to have the index, which for some is more than creating it.
        return [self.index_statement(table_name, e, opts)]

    def drop_index_statement(self, table_name: QualifiedName, name: str) -> str:
        # An index lives in its table's schema, so a drop must qualify it the same way.
        return f'drop index {self.qname(table_name.sibling(name))}'

    def render_predicate(self, p: Predicate) -> str:
        if isinstance(p, RawPredicate):
            return p.s
        elif isinstance(p, Compare):
            return f'{self.quote_ident(p.column)} {p.op.value} {self.render_predicate_value(p.value)}'
        elif isinstance(p, IsNull):
            return f'{self.quote_ident(p.column)} is not null' if p.negated else f'{self.quote_ident(p.column)} is null'
        elif isinstance(p, Not):
            return f'not ({self.render_predicate(p.predicate)})'
        elif isinstance(p, And):
            return ' and '.join(f'({self.render_predicate(c)})' for c in p.predicates)
        elif isinstance(p, Or):
            return ' or '.join(f'({self.render_predicate(c)})' for c in p.predicates)
        else:
            raise TypeError(p)  # fail-closed: backend predicate nodes are handled by the backend's override

    def render_predicate_value(self, v: SimplePredicateValue) -> str:
        if v is None:
            return 'null'
        elif isinstance(v, bool):
            return 'true' if v else 'false'
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        else:
            raise TypeError(v)

    ##
    # triggers

    def trigger_create_statements(self, tbl: TableDef, t: Trigger, opts: CreateOptions) -> list[str]:
        # The differ relies on a trigger type owning every name it renders, so refuse to create one that does not (an
        # OpaqueTrigger, say, which exists only to be diffed against).
        name = t.trigger_name(tbl.name)
        if not type(t).owns_trigger_name(tbl.name, name):
            raise TypeError(f'trigger type {type(t).__qualname__} does not own its own name {name!r}')

        return self.trigger_renderer(type(t)).create_statements(self, tbl, t, opts)

    def trigger_drop_statements(self, table_name: QualifiedName, name: str, cls: type[Trigger]) -> list[str]:
        return self.trigger_renderer(cls).drop_statements(self, table_name, name)

    ##
    # shared assembly

    def _identity_column(self, cols: ta.Mapping[str, Column], pk: PrimaryKey | None) -> str | None:
        if pk is not None and len(pk.columns) == 1 and isinstance(cols[pk.columns[0]].type, Integer):
            return pk.columns[0]
        return None

    def _build_render_column(self, c: Column, *, is_identity: bool, indexed: bool = False) -> RenderColumn:
        dfl: str | None = None
        if c.default.present:
            if is_identity:
                raise TypeError(c)
            dfl = self.render_default(c.default.must())

        return RenderColumn(
            c.name,
            self.column_type(c, is_identity=is_identity, indexed=indexed),
            not_null=not c.nullable,
            default=dfl,
            identity=self.column_identity_sql(c) if is_identity else '',
            extra=self.column_option_sql(c),
        )

    def _render_column(self, rc: RenderColumn) -> str:
        out = io.StringIO()
        out.write(f'{self.quote_ident(rc.name)} {rc.type}')
        if rc.identity:
            out.write(f' {rc.identity}')
        if rc.not_null:
            out.write(' not null')
        if rc.default is not None:
            out.write(f' default {rc.default}')
        for x in rc.extra:
            out.write(f' {x}')
        return out.getvalue()

    def render_create_statements(
            self,
            tbl: TableDef,
            opts: CreateOptions | None = None,
    ) -> list[str]:
        if opts is None:
            opts = self.CreateOptions()

        self.consume_table_options(tbl)

        # Everything from here on is of the physical table, but for the triggers, which get the one that was given.
        ptbl = self.physical_table(tbl)

        cols: ta.Mapping[str, Column] = col.make_map_by(
            lambda c: c.name,
            ptbl.elements[Column],
            strict=True,
        )

        pk = ptbl.elements.get(PrimaryKey)
        identity_column = self._identity_column(cols, pk)

        # Columns participating in an index or the primary key - some backends (mysql) must give an indexed string a
        # bounded varchar length rather than an un-indexable text type.
        indexed_cols = {cn for i in ptbl.elements.get(Index, ()) for cn in i.columns}
        if pk is not None:
            indexed_cols.update(pk.columns)

        r_cols: dict[str, RenderColumn] = {
            c.name: self._build_render_column(
                c,
                is_identity=(c.name == identity_column),
                indexed=(c.name in indexed_cols),
            )
            for c in cols.values()
        }

        constraints: list[str] = []
        indexes: list[str] = []
        triggers: list[str] = []

        for e in ptbl.elements:
            if isinstance(e, Column):
                pass  # Already handled

            elif isinstance(e, PrimaryKey):
                check.not_empty(e.columns)
                constraints.append(f'primary key ({", ".join(self.quote_ident(c) for c in e.columns)})')

            elif isinstance(e, Trigger):
                triggers.extend(self.trigger_create_statements(tbl, e, opts))

            elif isinstance(e, Index):
                indexes.extend(self.index_statements(tbl.name, e, opts))

            else:
                raise TypeError(e)

        cts = io.StringIO()

        cts.write('create table')
        if opts.if_not_exists:
            cts.write(' if not exists')
        cts.write(f' {self.qname(tbl.name)} (\n')

        for i, rc in enumerate(r_cols.values()):
            cts.write(f'  {self._render_column(rc)}')

            if constraints or i < len(r_cols) - 1:
                cts.write(',')

            cts.write('\n')

        for i, cs in enumerate(constraints):
            cts.write(f'  {cs}')

            if i < len(constraints) - 1:
                cts.write(',')

            cts.write('\n')

        cts.write(')')

        for sfx in self.table_suffixes(ptbl, identity_column):
            cts.write('\n')
            cts.write(sfx)

        stmts: list[str] = []

        if opts.drop_if_exists:
            stmts.append(self.drop_statement(tbl))

        stmts.append(cts.getvalue())

        stmts.extend(indexes)
        stmts.extend(triggers)

        return stmts

    ##
    # migrations

    def alter_column_statements(self, op: AlterColumn) -> list[str]:
        # In-place column alteration is backend-specific (and impossible on sqlite without a table rebuild); backends
        # that can do it override this.
        raise UnsupportedMigrationError(
            f'{type(self).__name__} cannot alter column {op.column.name!r} of table {op.table!r} in place',
        )

    def render_migration(self, op: MigrationOp, opts: CreateOptions | None = None) -> list[str]:
        if opts is None:
            opts = self.CreateOptions()

        if isinstance(op, AddColumn):
            rc = self._render_column(self._build_render_column(op.column, is_identity=False))
            return [f'alter table {self.qname(op.table)} add column {rc}']
        elif isinstance(op, DropColumn):
            return [f'alter table {self.qname(op.table)} drop column {self.quote_ident(op.name)}']
        elif isinstance(op, AlterColumn):
            return self.alter_column_statements(op)
        elif isinstance(op, AddIndex):
            return self.index_statements(op.table, op.index, opts)
        elif isinstance(op, DropIndex):
            return [self.drop_index_statement(op.table, op.name)]
        elif isinstance(op, AddTrigger):
            return self.trigger_create_statements(op.table_def, op.trigger, opts)
        elif isinstance(op, DropTrigger):
            return self.trigger_drop_statements(op.table, op.name, op.trigger_cls)
        else:
            raise TypeError(op)
