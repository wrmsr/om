import abc
import dataclasses as dc
import typing as ta

from .... import lang
from ..processing.base import ProcessingContext
from .ops import Op
from .ops import OpRefMap
from .values import Bindings


##


@dc.dataclass(frozen=True)
class Generation:
    ops: ta.Sequence[Op]
    ref_map: OpRefMap | None = None
    bindings: Bindings | None = dc.field(default=None, kw_only=True)


class Generator(lang.Abstract):
    # Opt in locally after accounting for non-spec inputs in cache_key(). Bump for semantic changes not reflected in
    # spec/cache schemas. An unopted-in extension keeps the entire installation on the generation path.
    cache_version: ta.ClassVar[int | None] = None
    cache_schema: ta.ClassVar[tuple[type, ...]] = ()

    def cache_key(self, ctx: ProcessingContext) -> ta.Any:
        return ()

    @abc.abstractmethod
    def generate(self, ctx: ProcessingContext) -> Generation | None:
        raise NotImplementedError
