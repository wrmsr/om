import typing as ta
import uuid

from ... import dataclasses as dc
from ... import lang
from .config import OriginFilter


##


@dc.dataclass(frozen=True, kw_only=True)
class ShadowState(lang.Final):
    version: int
    origin: uuid.UUID
    deleted: bool


@dc.dataclass(frozen=True, kw_only=True)
class SourceRow(lang.Final):
    """One swept row: its shadow state plus, unless it is a tombstone, the base row's canonical values by column."""

    key: uuid.UUID
    version: int
    origin: uuid.UUID
    deleted: bool
    values: ta.Mapping[str, ta.Any] | None

    @property
    def state(self) -> ShadowState:
        return ShadowState(version=self.version, origin=self.origin, deleted=self.deleted)


@dc.dataclass(frozen=True, kw_only=True)
class OriginPredicate(lang.Final):
    """A link's origin filter, resolved against live node ids."""

    filter: OriginFilter
    node_id: uuid.UUID | None = None  # the source's own id, or the excluded target's, as the filter demands
