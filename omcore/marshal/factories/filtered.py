"""This module is considered part of the api."""
import typing as ta

from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory


FactoryT = ta.TypeVar('FactoryT', bound=MarshalerFactory | UnmarshalerFactory)
FactoryContextT = ta.TypeVar('FactoryContextT', bound=MarshalFactoryContext | UnmarshalFactoryContext)


##


class _FilteredFactory(ta.Generic[FactoryContextT, FactoryT]):
    def __init__(
            self,
            fn: ta.Callable[[FactoryContextT, Spec], bool],
            fac: FactoryT,
    ) -> None:
        super().__init__()

        self._fn = fn
        self._fac = fac

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._fn}, {self._fac})'


class FilteredMarshalerFactory(_FilteredFactory[MarshalFactoryContext, MarshalerFactory], MarshalerFactory):
    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        if not self._fn(ctx, spec):
            return None
        return self._fac.make_marshaler(ctx, spec)


class FilteredUnmarshalerFactory(_FilteredFactory[UnmarshalFactoryContext, UnmarshalerFactory], UnmarshalerFactory):
    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        if not self._fn(ctx, spec):
            return None
        return self._fac.make_unmarshaler(ctx, spec)
