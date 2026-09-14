from ...dtypes import INTEGER
from ...dtypes import STRING
from ...qualifiedname import qn
from ..elements import Column
from ..elements import Elements
from ..elements import Index
from ..elements import PrimaryKey
from ..elements import UpdatedAtTrigger
from ..lower import normalize_table
from ..tabledefs import TableDef


def test_normalize_is_order_insensitive_for_non_columns():
    a = TableDef(qn('t'), Elements(
        Column('id', INTEGER),
        PrimaryKey(['id']),
        Column('name', STRING),
        Index(['name'], name='by_name'),
        UpdatedAtTrigger('b'),
        Index(['id'], name='by_id'),
        UpdatedAtTrigger('a'),
    ))
    b = TableDef(qn('t'), Elements(
        Index(['id'], name='by_id'),
        UpdatedAtTrigger('a'),
        Column('id', INTEGER),
        Index(['name'], name='by_name'),
        Column('name', STRING),
        UpdatedAtTrigger('b'),
        PrimaryKey(['id']),
    ))

    assert normalize_table(a) == normalize_table(b)


def test_normalize_preserves_column_order():
    td = TableDef(qn('t'), Elements(
        Column('b', INTEGER),
        Column('a', INTEGER),
        Index(['a']),
    ))

    assert [c.name for c in normalize_table(td).elements[Column]] == ['b', 'a']
