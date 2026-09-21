from ... import check
from ... import dataclasses as dc
from ... import lang
from ..dtypes import Datetime
from ..dtypes import Dtype
from ..dtypes import Integer
from ..dtypes import String
from ..qualifiedname import QualifiedName
from .elements import Column
from .elements import Index
from .elements import OpaqueTrigger
from .elements import PrimaryKey
from .elements import Trigger
from .elements import index_name
from .lower import normalize_table
from .tabledefs import TableDef


##


class MigrationOp(lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class AddColumn(MigrationOp, lang.Final):
    table: QualifiedName
    column: Column


@dc.dataclass(frozen=True)
class DropColumn(MigrationOp, lang.Final):
    table: QualifiedName
    name: str


@dc.dataclass(frozen=True)
class AlterColumn(MigrationOp, lang.Final):
    table: QualifiedName
    column: Column  # the desired end state; the backend renders the alter to reach it (type and/or nullability)


@dc.dataclass(frozen=True)
class AddIndex(MigrationOp, lang.Final):
    table: QualifiedName
    index: Index


@dc.dataclass(frozen=True)
class DropIndex(MigrationOp, lang.Final):
    table: QualifiedName
    name: str


@dc.dataclass(frozen=True)
class AddTrigger(MigrationOp, lang.Final):
    table: QualifiedName
    trigger: Trigger
    table_def: TableDef  # a trigger plugin may need the rest of the table (its primary key, say) to render


@dc.dataclass(frozen=True)
class DropTrigger(MigrationOp, lang.Final):
    table: QualifiedName
    name: str
    trigger_cls: type[Trigger]  # the type whose namespace claimed the name; its plugin knows how to drop it


##


class UnsupportedDiffError(Exception):
    pass


# The dtypes every backend reflects faithfully and unambiguously, so a change between two of them is a real, confident
# change worth acting on. Lossier types (Uuid/Boolean/Float/Bytes, which some backends' reflection collapses to
# String/Integer) are deliberately not compared, to avoid spurious churn.
_DIFFABLE_DTYPES = (Integer, String, Datetime)


def dtypes_confidently_differ(cur: Dtype, ex: Dtype) -> bool:
    """
    Whether two dtypes differ in a way every backend reflects faithfully. Only the diffable kinds are compared at all;
    within a kind, a detail (width, length) left unspecified on either side matches anything, so an in-code default
    never churns against whatever concrete type the db reports for it.
    """

    if not (isinstance(cur, _DIFFABLE_DTYPES) and isinstance(ex, _DIFFABLE_DTYPES)):
        return False

    if type(cur) is not type(ex):
        return True

    if isinstance(cur, Integer) and isinstance(ex, Integer):
        return cur.bits is not None and ex.bits is not None and cur.bits != ex.bits

    elif isinstance(cur, String) and isinstance(ex, String):
        return cur.length is not None and ex.length is not None and cur.length != ex.length

    else:
        return False


def diff_table(
        current: TableDef,
        existing: TableDef,
        *,
        trigger_table: TableDef | None = None,
) -> list[MigrationOp]:
    """
    Produce the migration ops that bring `existing` (e.g. a table reflected from a live db) up to `current` (the
    in-code definition): column add/drop/alter, named-index add/drop, and trigger add/drop. A column's nullability
    change, or a confident type change (see `dtypes_confidently_differ`), becomes an in-place `AlterColumn`; lossier
    type differences are left untouched (reflection can't tell them apart). Primary-key changes are refused outright
    (`UnsupportedDiffError`); options are left untouched. Triggers are compared by name only: a current trigger whose
    name is absent is added, and a reflected trigger not in the current definition is dropped only if its name is
    claimed by a trigger type present in `current` - anything else on the table is somebody else's and is left alone.
    Whether an `AlterColumn` can actually be applied is the backend's call - sqlite, lacking ALTER COLUMN, refuses it at
    render time. Operates on the order-normal-form, so element order is insignificant.

    What is diffed is a table as the db holds it, which is not always the table as it was defined: reflection may have
    lost what a column really is, and a backend may hold a table in another shape than its definition's altogether (see
    `cluster_on_primary_key`). A trigger however is rendered against the table it is on, and means that table as
    defined - so when the two differ `trigger_table` is that definition, and is what an added trigger is given.
    """

    if current.name != existing.name:
        raise UnsupportedDiffError(f'table name differs: {current.name!r} != {existing.name!r}')

    current = normalize_table(current)
    existing = normalize_table(existing)

    cur_pk = current.elements.get(PrimaryKey)
    ex_pk = existing.elements.get(PrimaryKey)
    # In order: it is the order of a key's columns which the table is kept in, and looked up by.
    if list(cur_pk.columns if cur_pk is not None else ()) != list(ex_pk.columns if ex_pk is not None else ()):
        raise UnsupportedDiffError(f'primary-key change is not supported: {ex_pk!r} -> {cur_pk!r}')

    cur_pk_cols = frozenset(cur_pk.columns if cur_pk is not None else ())

    ops: list[MigrationOp] = []

    #

    cur_cols = {c.name: c for c in current.elements.get(Column, ())}
    ex_cols = {c.name: c for c in existing.elements.get(Column, ())}

    for name, c in cur_cols.items():
        ex_col = ex_cols.get(name)
        if ex_col is None:
            ops.append(AddColumn(current.name, c))
            continue

        # A column on both sides: emit an in-place AlterColumn for the changes we can see faithfully - a nullability
        # change (reflected accurately everywhere except on pk columns, which are implicitly not-null however declared)
        # or a confident type change.
        nullability_changed = name not in cur_pk_cols and c.nullable != ex_col.nullable
        if nullability_changed or dtypes_confidently_differ(c.type, ex_col.type):
            ops.append(AlterColumn(current.name, c))

    for name in ex_cols:
        if name not in cur_cols:
            ops.append(DropColumn(current.name, name))

    #

    cur_idx = {index_name(current.name, i): i for i in current.elements.get(Index, ())}
    ex_idx = {index_name(existing.name, i): i for i in existing.elements.get(Index, ())}

    for nm, i in cur_idx.items():
        ex = ex_idx.get(nm)
        if ex is None:
            ops.append(AddIndex(current.name, i))
        elif (list(i.columns), i.unique) != (list(ex.columns), ex.unique):
            # Same name, changed definition - drop and recreate. The where-clause is intentionally not compared:
            # partial-index reflection is lossy, so doing so would diff forever.
            ops.append(DropIndex(current.name, nm))
            ops.append(AddIndex(current.name, i))
    for nm in ex_idx:
        if nm not in cur_idx:
            ops.append(DropIndex(current.name, nm))

    #

    cur_trg: dict[str, Trigger] = {}
    for t in current.elements.get_any(Trigger):
        nm = t.trigger_name(current.name)
        check.not_in(nm, cur_trg)
        cur_trg[nm] = t
    ex_trg_names = sorted({t.trigger_name(existing.name) for t in existing.elements.get_any(Trigger)})
    cur_trg_types = sorted({type(t) for t in cur_trg.values()}, key=lambda tc: tc.__qualname__)

    for nm, t in cur_trg.items():
        if nm in ex_trg_names:
            continue
        if isinstance(t, OpaqueTrigger):
            raise UnsupportedDiffError(f'opaque trigger {nm!r} is absent from the db and cannot be created')
        ops.append(AddTrigger(current.name, t, trigger_table if trigger_table is not None else current))

    for nm in ex_trg_names:
        if nm in cur_trg:
            continue
        owners = [tc for tc in cur_trg_types if tc.owns_trigger_name(current.name, nm)]
        if not owners:
            continue  # not ours to touch
        ops.append(DropTrigger(current.name, nm, check.single(owners)))

    return ops
