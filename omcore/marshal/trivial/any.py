import typing as ta

from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.types import DuplexHandler
from ..api.values import Value
from ..factories.typemap import TypeMapDuplexFactory


##


class AnyMarshalerUnmarshaler(DuplexHandler):
    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        # FIXME: naughty
        mfc = MarshalFactoryContext(runtime=(rt := ctx.runtime))
        return rt.make_marshaler(mfc, type(o)).marshal(ctx, o)

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        return v


ANY_MARSHALER_UNMARSHALER = AnyMarshalerUnmarshaler()

ANY_MARSHALER_FACTORY = ANY_UNMARSHALER_FACTORY = TypeMapDuplexFactory({
    ta.Any: ANY_MARSHALER_UNMARSHALER,
})
