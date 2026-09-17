"""Runtime bindings, kept separate from the opaque values they retrieve."""
import abc
import dataclasses as dc
import enum
import typing as ta

from .... import lang
from ..processing.base import ProcessingContext
from ..processing.registry import processing_context_item_name
from .idents import CTX_IDENT
from .idents import SPEC_IDENT
from .ops import OpRef


##


class ValOp(enum.Enum):
    MUST = enum.auto()


@dc.dataclass(frozen=True)
class Item:
    key: str | int


ValStep: ta.TypeAlias = str | int | ValOp | Item
ValPath: ta.TypeAlias = tuple[ValStep, ...]


def _resolve_path(value: ta.Any, path: ValPath) -> ta.Any:
    for step in path:
        if isinstance(step, str):
            value = getattr(value, step)
        elif isinstance(step, (int, Item)):
            value = value[step.key if isinstance(step, Item) else step]
        elif step is ValOp.MUST:
            value = value.must()
        else:
            raise TypeError(step)
    return value


def _path_src(src: str, path: ValPath) -> str:
    for step in path:
        if isinstance(step, str):
            if not step.isidentifier():
                raise ValueError(step)
            src += f'.{step}'
        elif isinstance(step, (int, Item)):
            src += f'[{step.key if isinstance(step, Item) else step!r}]'
        elif step is ValOp.MUST:
            src += '.must()'
        else:
            raise TypeError(step)
    return src


class Val(lang.Abstract):
    @abc.abstractmethod
    def resolve(self, ctx: ProcessingContext) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def src(self) -> str:
        raise NotImplementedError


@dc.dataclass(frozen=True)
class SpecVal(Val):
    path: ValPath

    def resolve(self, ctx: ProcessingContext) -> ta.Any:
        return _resolve_path(ctx.cs, self.path)

    def src(self) -> str:
        return _path_src(SPEC_IDENT, self.path)


@dc.dataclass(frozen=True)
class ContextVal(Val):
    item: str
    path: ValPath = ()

    @classmethod
    def of(cls, item: ta.Any, path: ValPath = ()) -> ContextVal:
        return cls(processing_context_item_name(item), path)

    def resolve(self, ctx: ProcessingContext) -> ta.Any:
        return _resolve_path(ctx[self.item], self.path)

    def src(self) -> str:
        return _path_src(f'{CTX_IDENT}[{self.item!r}]', self.path)


Bindings: ta.TypeAlias = ta.Mapping[OpRef, Val]
