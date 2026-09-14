import pytest

from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import UUID
from ...dtypes import Integer
from ...dtypes import String
from ...qualifiedname import qn
from ..diffing import AddColumn
from ..diffing import AddIndex
from ..diffing import AddTrigger
from ..diffing import AlterColumn
from ..diffing import DropColumn
from ..diffing import DropIndex
from ..diffing import DropTrigger
from ..diffing import UnsupportedDiffError
from ..diffing import diff_table
from ..elements import Column
from ..elements import Elements
from ..elements import Index
from ..elements import OpaqueTrigger
from ..elements import PrimaryKey
from ..elements import UpdatedAtTrigger
from ..tabledefs import TableDef


def _td(*els):
    return TableDef(qn('t'), Elements(*els))


def test_add_and_drop_columns():
    existing = _td(Column('id', INTEGER), PrimaryKey(['id']), Column('old', STRING))
    current = _td(Column('id', INTEGER), PrimaryKey(['id']), Column('new', STRING))

    ops = diff_table(current, existing)

    assert {o.column.name for o in ops if isinstance(o, AddColumn)} == {'new'}
    assert {o.name for o in ops if isinstance(o, DropColumn)} == {'old'}


def test_add_and_drop_indexes():
    existing = _td(Column('id', INTEGER), Index(['id'], name='old_ix'))
    current = _td(Column('id', INTEGER), Index(['id'], name='new_ix'))

    assert {type(o) for o in diff_table(current, existing)} == {AddIndex, DropIndex}


def test_order_insensitive_no_change():
    a = _td(Column('a', INTEGER), Column('b', INTEGER), Index(['a'], name='x'))
    b = _td(Index(['a'], name='x'), Column('b', INTEGER), Column('a', INTEGER))

    assert diff_table(a, b) == []


def test_pk_change_raises():
    a = _td(Column('id', INTEGER), Column('k', INTEGER), PrimaryKey(['id']))
    b = _td(Column('id', INTEGER), Column('k', INTEGER), PrimaryKey(['k']))
    with pytest.raises(UnsupportedDiffError):
        diff_table(a, b)


def test_name_mismatch_raises():
    with pytest.raises(UnsupportedDiffError):
        diff_table(
            TableDef(qn('a'), Elements(Column('x', INTEGER))),
            TableDef(qn('b'), Elements(Column('x', INTEGER))),
        )
    with pytest.raises(UnsupportedDiffError):
        diff_table(
            TableDef(qn('s', 'a'), Elements(Column('x', INTEGER))),
            TableDef(qn('a'), Elements(Column('x', INTEGER))),
        )


def test_unnamed_index_idempotent():
    # an unnamed in-code index vs its reflected, auto-named counterpart -> no diff
    code = _td(Column('id', INTEGER), Column('email', STRING), Index(['email']))
    reflected = _td(Column('id', INTEGER), Column('email', STRING), Index(['email'], name='t__index__email'))
    assert diff_table(code, reflected) == []


def test_changed_named_index_recreates():
    a = _td(Column('id', INTEGER), Column('x', INTEGER), Index(['id'], name='ix'))
    b = _td(Column('id', INTEGER), Column('x', INTEGER), Index(['x'], name='ix'))
    assert [type(o) for o in diff_table(a, b)] == [DropIndex, AddIndex]


def test_type_change_alters():
    a = _td(Column('id', INTEGER), Column('v', STRING), PrimaryKey(['id']))
    b = _td(Column('id', INTEGER), Column('v', INTEGER), PrimaryKey(['id']))
    assert [type(o) for o in diff_table(a, b)] == [AlterColumn]


def test_nullability_change_alters():
    a = _td(Column('id', INTEGER), Column('v', STRING, nullable=True), PrimaryKey(['id']))
    b = _td(Column('id', INTEGER), Column('v', STRING), PrimaryKey(['id']))
    assert [type(o) for o in diff_table(a, b)] == [AlterColumn]


def test_lossy_type_change_ignored():
    # Uuid is not faithfully reflected on every backend, so a Uuid-vs-String difference is left alone (no false alter)
    a = _td(Column('id', INTEGER), Column('v', UUID), PrimaryKey(['id']))
    b = _td(Column('id', INTEGER), Column('v', STRING), PrimaryKey(['id']))
    assert diff_table(a, b) == []


def test_dtype_details():
    def ops(cur, ex):
        return [type(o) for o in diff_table(
            _td(Column('id', INTEGER), Column('v', cur), PrimaryKey(['id'])),
            _td(Column('id', INTEGER), Column('v', ex), PrimaryKey(['id'])),
        )]

    # an unspecified detail matches whatever concrete detail the db reports, in either direction
    assert ops(INTEGER, Integer(bits=64)) == []
    assert ops(Integer(bits=64), INTEGER) == []
    assert ops(STRING, String(length=40)) == []

    # two specified details that differ are a confident change
    assert ops(Integer(bits=64), Integer(bits=32)) == [AlterColumn]
    assert ops(String(length=40), String(length=80)) == [AlterColumn]
    assert ops(Integer(bits=64), Integer(bits=64)) == []


##


def test_trigger_add():
    cur = _td(Column('id', INTEGER), Column('updated_at', STRING), PrimaryKey(['id']), UpdatedAtTrigger('updated_at'))
    ex = _td(Column('id', INTEGER), Column('updated_at', STRING), PrimaryKey(['id']))

    [op] = diff_table(cur, ex)
    assert isinstance(op, AddTrigger)
    assert op.trigger == UpdatedAtTrigger('updated_at')
    assert op.table_def.name == qn('t')


def test_trigger_reflected_matches_by_name():
    cur = _td(Column('id', INTEGER), PrimaryKey(['id']), UpdatedAtTrigger('updated_at'))
    ex = _td(Column('id', INTEGER), PrimaryKey(['id']), OpaqueTrigger('t__trigger__updated_at__updated_at'))

    assert diff_table(cur, ex) == []


def test_trigger_drop_only_within_owned_namespace():
    # a stale trigger under a namespace claimed by a current trigger type is dropped; a foreign one is left alone
    cur = _td(Column('id', INTEGER), PrimaryKey(['id']), UpdatedAtTrigger('updated_at'))
    ex = _td(
        Column('id', INTEGER),
        PrimaryKey(['id']),
        OpaqueTrigger('t__trigger__updated_at__updated_at'),
        OpaqueTrigger('t__trigger__updated_at__modified_at'),
        OpaqueTrigger('somebody_elses_trigger'),
    )

    [op] = diff_table(cur, ex)
    assert op == DropTrigger(qn('t'), 't__trigger__updated_at__modified_at', UpdatedAtTrigger)


def test_trigger_nothing_claimed_nothing_dropped():
    # with no trigger type present in the current definition, no namespace is claimed and nothing is dropped
    cur = _td(Column('id', INTEGER), PrimaryKey(['id']))
    ex = _td(Column('id', INTEGER), PrimaryKey(['id']), OpaqueTrigger('t__trigger__updated_at__updated_at'))

    assert diff_table(cur, ex) == []


def test_trigger_opaque_in_current_refused():
    cur = _td(Column('id', INTEGER), PrimaryKey(['id']), OpaqueTrigger('whatever'))
    ex = _td(Column('id', INTEGER), PrimaryKey(['id']))

    with pytest.raises(UnsupportedDiffError):
        diff_table(cur, ex)
