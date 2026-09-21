import pytest

from .... import typedvalues as tv
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import UUID
from ..diffing import AddTrigger
from ..diffing import UnsupportedDiffError
from ..diffing import diff_table
from ..elements import Column
from ..elements import Index
from ..elements import PrimaryKey
from ..elements import UpdatedAtTrigger
from ..lower import ClusteredIndexError
from ..lower import cluster_on_primary_key
from ..lower import clustered_index
from ..options import Clustered
from ..options import IndexOptions
from ..predicates import RawPredicate
from ..tabledefs import table_def


##


_CLUSTERED: IndexOptions = tv.TypedValues(Clustered())
_NOT_CLUSTERED: IndexOptions = tv.TypedValues()


def _entries(*extra, clustered=True):
    return table_def(
        'entries',
        Column('id', UUID),
        PrimaryKey(['id']),
        Column('seq', INTEGER),
        Column('session_id', UUID),
        Column('entry', STRING),
        Index(['session_id', 'seq'], unique=True, options=_CLUSTERED if clustered else _NOT_CLUSTERED),
        *extra,
    )


def test_clustered_index():
    assert clustered_index(_entries(clustered=False)) is None
    assert clustered_index(_entries()) == Index(['session_id', 'seq'], unique=True, options=_CLUSTERED)


def test_clustered_index_has_to_be_something_a_table_can_be_kept_by():
    def td(*els):
        return table_def('t', Column('id', UUID), PrimaryKey(['id']), Column('a', INTEGER), *els)

    for bad in [
        td(Index(['a'], options=_CLUSTERED)),  # not unique
        td(Index(['a'], unique=True, where=RawPredicate('a > 0'), options=_CLUSTERED)),  # partial
        td(Column('n', INTEGER, nullable=True), Index(['n'], unique=True, options=_CLUSTERED)),  # nullable
        td(Index(['nope'], unique=True, options=_CLUSTERED)),  # not there
        td(
            Column('b', INTEGER),
            Index(['a'], unique=True, options=_CLUSTERED),
            Index(['b'], unique=True, options=_CLUSTERED),
        ),  # more than one
    ]:
        with pytest.raises(ClusteredIndexError):
            clustered_index(bad)


def test_cluster_on_primary_key():
    # nothing to do, nothing done
    td = _entries(clustered=False)
    assert cluster_on_primary_key(td) is td

    # the index takes the key's place, in its own order, and the key becomes the unique index it still is
    assert cluster_on_primary_key(_entries()) == table_def(
        'entries',
        Column('id', UUID),
        Index(['id'], unique=True),
        Column('seq', INTEGER),
        Column('session_id', UUID),
        Column('entry', STRING),
        PrimaryKey(['session_id', 'seq']),
    )

    # a table with no key to displace just gains one
    assert cluster_on_primary_key(table_def(
        't',
        Column('a', INTEGER),
        Index(['a'], unique=True, options=_CLUSTERED),
    )) == table_def('t', Column('a', INTEGER), PrimaryKey(['a']))

    # an identity key is the backend's own row id, which the table is kept by no matter what
    with pytest.raises(ClusteredIndexError):
        cluster_on_primary_key(table_def(
            't',
            Column('id', INTEGER),
            PrimaryKey(['id']),
            Column('a', INTEGER),
            Index(['a'], unique=True, options=_CLUSTERED),
        ))


def test_diff_is_of_the_physical_table_and_triggers_of_the_definition():
    td = _entries()
    existing = cluster_on_primary_key(td)

    # defined against physical is a change of primary key, which is refused - as is a reordering of one
    with pytest.raises(UnsupportedDiffError):
        diff_table(td, existing)
    with pytest.raises(UnsupportedDiffError):
        diff_table(
            table_def('t', Column('a', INTEGER), Column('b', INTEGER), PrimaryKey(['a', 'b'])),
            table_def('t', Column('a', INTEGER), Column('b', INTEGER), PrimaryKey(['b', 'a'])),
        )

    # physical against physical is no change at all
    assert diff_table(cluster_on_primary_key(td), existing) == []

    # and a trigger added along the way is handed the definition, whose key is still the one it was defined with
    with_trigger = _entries(Column('updated_at', STRING), UpdatedAtTrigger('updated_at'))
    [op] = diff_table(
        cluster_on_primary_key(with_trigger),
        cluster_on_primary_key(_entries(Column('updated_at', STRING))),
        trigger_table=with_trigger,
    )
    assert isinstance(op, AddTrigger)
    assert op.table_def is with_trigger
    assert list(op.table_def.elements[PrimaryKey].columns) == ['id']
