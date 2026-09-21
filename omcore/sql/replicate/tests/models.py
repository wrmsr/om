"""
The yelp-like demo schema, keyed by uuids as replicated tables must be, plus a table exercising every dtype, one kept
clustered, and one with timestamps kept by triggers.
"""
from .... import typedvalues as tv
from ...dtypes import BOOLEAN
from ...dtypes import BYTES
from ...dtypes import DATETIME
from ...dtypes import FLOAT
from ...dtypes import STRING
from ...dtypes import UUID
from ...dtypes import Integer
from ...tabledefs.elements import Column
from ...tabledefs.elements import CreatedAtUpdatedAt
from ...tabledefs.elements import Index
from ...tabledefs.elements import PrimaryKey
from ...tabledefs.options import Clustered
from ...tabledefs.tabledefs import table_def
from ..config import ReplicationSchema


##


def build_schema() -> ReplicationSchema:
    return ReplicationSchema([

        table_def(
            'businesses',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('name', STRING),
            Index(['name']),
        ),

        # Clustered on other than its key, which on some dialects makes that key no longer its primary key where it
        # counts - while it is still by that key that it is captured, and applied.
        table_def(
            'business_categories',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('business_id', UUID),
            Column('tag', STRING),
            Index(['business_id', 'tag'], unique=True, options=tv.TypedValues(Clustered())),
        ),

        table_def(
            'users',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('name', STRING),
            Column('favorite_business_id', UUID, nullable=True),
            Index(['name']),
        ),

        table_def(
            'user_relations',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('src_id', UUID),
            Column('dst_id', UUID),
            Index(['src_id']),
            Index(['dst_id']),
        ),

        table_def(
            'reviews',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('business_id', UUID),
            Column('user_id', UUID),
            Column('text', STRING),
            Index(['business_id']),
            Index(['user_id']),
        ),

        # Its timestamps kept by triggers of its own, alongside the ones which capture it.
        table_def(
            'notes',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('text', STRING),
            CreatedAtUpdatedAt(),
        ),
        table_def(
            'kitchen_sink',
            Column('id', UUID),
            PrimaryKey(['id']),
            Column('i', Integer(bits=64), nullable=True),
            Column('s', STRING, nullable=True),
            Column('d', DATETIME, nullable=True),
            Column('u', UUID, nullable=True),
            Column('b', BOOLEAN, nullable=True),
            Column('f', FLOAT, nullable=True),
            Column('y', BYTES, nullable=True),
        ),

    ])
