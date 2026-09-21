"""
Pure IR describing what was reflected from a live database. This layer does no IO and knows no dialect - it is just a
neutral, lossy snapshot. Reflection deliberately fails *open*: a real table may carry things we don't model (extension
artifacts, exotic constraints), and an inspector should record what it understands and ignore the rest rather than
refuse.
"""
import typing as ta

from ... import dataclasses as dc
from ... import lang
from ..qualifiedname import QualifiedName


##


@dc.dataclass(frozen=True)
class ReflectedColumn(lang.Final):
    name: str
    type: str  # the raw dialect type string, verbatim from the db

    _: dc.KW_ONLY

    nullable: bool = True
    length: int | None = None  # a bounded character length, when the db reports one


@dc.dataclass(frozen=True)
class ReflectedIndex(lang.Final):
    name: str
    columns: ta.Sequence[str]

    _: dc.KW_ONLY

    unique: bool = False


@dc.dataclass(frozen=True)
class ReflectedTrigger(lang.Final):
    name: str  # a trigger is reflected by name alone - its body is never modeled


@dc.dataclass(frozen=True)
class ReflectedTable(lang.Final):
    name: QualifiedName  # exactly as it was asked for, so it diffs cleanly against the in-code definition
    columns: ta.Sequence[ReflectedColumn]

    _: dc.KW_ONLY

    primary_key: ta.Sequence[str] = ()  # in the key's own order, which need not be the columns'
    indexes: ta.Sequence[ReflectedIndex] = ()
    triggers: ta.Sequence[ReflectedTrigger] = ()
