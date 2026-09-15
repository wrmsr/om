"""The tabledefs replication adds to a node, derived from the schema so each dialect renders its own correct types."""
import typing as ta

from ..dtypes import BOOLEAN
from ..dtypes import DATETIME
from ..dtypes import STRING
from ..dtypes import UUID
from ..dtypes import Integer
from ..qualifiedname import QualifiedName
from ..tabledefs.elements import Column
from ..tabledefs.elements import Elements
from ..tabledefs.elements import PrimaryKey
from ..tabledefs.tabledefs import TableDef


##


SHADOW_KEY: ta.Final[str] = 'id'
SHADOW_VERSION: ta.Final[str] = 'version'
SHADOW_ORIGIN: ta.Final[str] = 'origin'
SHADOW_DELETED: ta.Final[str] = 'deleted'
SHADOW_CHANGED_AT: ta.Final[str] = 'changed_at'


def shadow_table_def(name: QualifiedName) -> TableDef:
    """
    A table's shadow: one row per key ever seen, carrying the writer-owned version, the authoring node, and whether the
    base row is gone (a tombstone). Only the primary key is indexed; the sweep needs nothing else.
    """

    return TableDef(name, Elements(
        Column(SHADOW_KEY, UUID),
        PrimaryKey([SHADOW_KEY]),
        Column(SHADOW_VERSION, Integer(bits=64)),
        Column(SHADOW_ORIGIN, UUID),
        Column(SHADOW_DELETED, BOOLEAN),
        Column(SHADOW_CHANGED_AT, DATETIME),
    ))


##


NODE_ID: ta.Final[str] = 'id'
NODE_CREATED_AT: ta.Final[str] = 'created_at'


def node_table_def(name: QualifiedName) -> TableDef:
    """A single row: this database's identity, stamped as the origin of everything it writes."""

    return TableDef(name, Elements(
        Column(NODE_ID, UUID),
        PrimaryKey([NODE_ID]),
        Column(NODE_CREATED_AT, DATETIME),
    ))


##


CURSOR_LINK: ta.Final[str] = 'link'
CURSOR_TABLE: ta.Final[str] = 'table_name'
CURSOR_POSITION: ta.Final[str] = 'position'
CURSOR_SWEEPS: ta.Final[str] = 'sweeps'
CURSOR_UPDATED_AT: ta.Final[str] = 'updated_at'


def cursor_table_def(name: QualifiedName) -> TableDef:
    """Where a link's sweep of each table currently stands: the last key seen, or nothing between sweeps."""

    return TableDef(name, Elements(
        Column(CURSOR_LINK, STRING),
        Column(CURSOR_TABLE, STRING),
        PrimaryKey([CURSOR_LINK, CURSOR_TABLE]),
        Column(CURSOR_POSITION, STRING, nullable=True),
        Column(CURSOR_SWEEPS, Integer(bits=64)),
        Column(CURSOR_UPDATED_AT, DATETIME),
    ))
