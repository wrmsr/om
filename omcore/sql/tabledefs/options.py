import typing as ta

from ... import dataclasses as dc
from ... import lang
from ... import typedvalues as tv


##


class ColumnOption(tv.TypedValue, lang.Abstract):
    pass


class IndexOption(tv.TypedValue, lang.Abstract):
    pass


class TableOption(tv.TypedValue, lang.Abstract):
    pass


ColumnOptions: ta.TypeAlias = tv.TypedValues[ColumnOption]
IndexOptions: ta.TypeAlias = tv.TypedValues[IndexOption]
TableOptions: ta.TypeAlias = tv.TypedValues[TableOption]


##


class BackendOption(tv.TypedValue, lang.Abstract):
    """
    Marker for any backend-specific option, of any element kind. A backend defines its own marker subclass (e.g.
    PostgresOption) under backends/<name>, mixed into concrete options alongside the relevant ColumnOption /
    IndexOption / TableOption. Core code references only this base, never a concrete backend.
    """


##


@dc.dataclass(frozen=True)
class Clustered(IndexOption, tv.UniqueTypedValue, lang.Final):
    """
    The table is to be kept in the order of this index - which has to be a unique one, of columns which cannot be null -
    rather than that of its primary key. This is the table as it is defined, and how much comes of it is the backend's:
    where the primary key is the one order a table can be kept in, the index takes its place and the key becomes the
    unique index it logically still is; where nothing keeps a table in any order, the intent is at least recorded.
    """
