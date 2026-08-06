"""
These factories are deliberately stateless: the configured factory list is read through the construction context on
every make call, which both keeps them shareable and lets the Runtime's footprint-keyed handler caching notice
`install_standard_factories` updates - a changed StandardMarshalerFactories config invalidates exactly the handlers
whose construction consulted it. Construction is the cached cold path, so the per-call list assembly is irrelevant.
"""
import typing as ta

from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory
from .api import StandardMarshalerFactories
from .api import StandardUnmarshalerFactories
from .defaults import DEFAULT_STANDARD_FACTORIES


##


class StandardMarshalerFactory(MarshalerFactory):
    def __init__(
            self,
            *,
            first: ta.Iterable[MarshalerFactory] | None = None,
            last: ta.Iterable[MarshalerFactory] | None = None,
    ) -> None:
        super().__init__()

        self._first = tuple(first or ())
        self._last = tuple(last or ())

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        cfg = ctx.get_configs().get(StandardMarshalerFactories)
        facs: ta.Sequence[MarshalerFactory] = cfg.lst if cfg is not None else DEFAULT_STANDARD_FACTORIES.marshaler_factories  # noqa

        for f in (*self._first, *facs, *self._last):
            if (m := f.make_marshaler(ctx, spec)) is not None:
                return m

        return None


class StandardUnmarshalerFactory(UnmarshalerFactory):
    def __init__(
            self,
            *,
            first: ta.Iterable[UnmarshalerFactory] | None = None,
            last: ta.Iterable[UnmarshalerFactory] | None = None,
    ) -> None:
        super().__init__()

        self._first = tuple(first or ())
        self._last = tuple(last or ())

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        cfg = ctx.get_configs().get(StandardUnmarshalerFactories)
        facs: ta.Sequence[UnmarshalerFactory] = cfg.lst if cfg is not None else DEFAULT_STANDARD_FACTORIES.unmarshaler_factories  # noqa

        for f in (*self._first, *facs, *self._last):
            if (u := f.make_unmarshaler(ctx, spec)) is not None:
                return u

        return None


##


def new_standard_marshaler_factory(
        *,
        first: ta.Iterable[MarshalerFactory] | None = None,
        last: ta.Iterable[MarshalerFactory] | None = None,
) -> MarshalerFactory:
    return StandardMarshalerFactory(
        first=first,
        last=last,
    )


def new_standard_unmarshaler_factory(
        *,
        first: ta.Iterable[UnmarshalerFactory] | None = None,
        last: ta.Iterable[UnmarshalerFactory] | None = None,
) -> UnmarshalerFactory:
    return StandardUnmarshalerFactory(
        first=first,
        last=last,
    )
