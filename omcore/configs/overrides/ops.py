import typing as ta

from ... import dataclasses as dc
from ... import lang
from .paths import OverridePath


##


class OpValue(lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class RawOpValue(OpValue, lang.Final):
    """Unparsed value literal text - parsed and typed only once applied, when the shape of its target is known."""

    text: str


@dc.dataclass(frozen=True)
class FileOpValue(OpValue, lang.Final):
    """`@path` - the contents of a file, loaded once applied."""

    path: str


@dc.dataclass(frozen=True)
class ConstOpValue(OpValue, lang.Final):
    """An already concrete value, used as is."""

    value: ta.Any


##


class OverrideOp(lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class SetOp(OverrideOp, lang.Final):
    """`path=value` - replaces whatever is at the path, creating it (and anything leading to it) if necessary."""

    path: OverridePath = dc.xfield(coerce=tuple)
    value: OpValue = dc.xfield()


@dc.dataclass(frozen=True)
class MergeOp(OverrideOp, lang.Final):
    """
    `path+=value` - deep-merges a map into a map, or extends a list with a list. Lists nested within a merged map
    replace rather than extend.
    """

    path: OverridePath = dc.xfield(coerce=tuple)
    value: OpValue = dc.xfield()


@dc.dataclass(frozen=True)
class RemoveOp(OverrideOp, lang.Final):
    """`/path` - removes a map entry (resetting it to its default, if it has one) or a list element."""

    path: OverridePath = dc.xfield(coerce=tuple)


@dc.dataclass(frozen=True)
class JqOp(OverrideOp, lang.Final):
    """Replaces the entire tree with the single output of a jq filter applied to it."""

    filter: str
