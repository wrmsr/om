import typing as ta

from ...funcs import guard as gfs
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.specs import Spec
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory


##


class MultiMarshalerFactory(MarshalerFactory):
    def __init__(
            self,
            *facs: MarshalerFactory,
            strict: bool = False,
    ) -> None:
        super().__init__()

        self._facs = facs
        self._mgf = gfs.multi(*[f.make_marshaler for f in self._facs], strict=strict)

    def make_marshaler(self, ctx: MarshalFactoryContext, spec: Spec) -> ta.Callable[[], Marshaler] | None:
        return self._mgf(ctx, spec)


class MultiUnmarshalerFactory(UnmarshalerFactory):
    def __init__(
            self,
            *facs: UnmarshalerFactory,
            strict: bool = False,
    ) -> None:
        super().__init__()

        self._facs = facs
        self._mgf = gfs.multi(*[f.make_unmarshaler for f in self._facs], strict=strict)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, spec: Spec) -> ta.Callable[[], Unmarshaler] | None:
        return self._mgf(ctx, spec)
