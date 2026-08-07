import typing as ta

from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.types import DuplexHandler
from ..api.values import Value
from ..factories.typemap import TypeMapMarshalerFactory
from ..factories.typemap import TypeMapUnmarshalerFactory


##


class AnyMarshalerUnmarshaler(DuplexHandler):
    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        # FIXME: naughty
        mfc = MarshalFactoryContext(runtime=(rt := ctx.runtime))
        return rt.make_marshaler(mfc, type(o)).marshal(ctx, o)

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        return v


ANY_MARSHALER_UNMARSHALER = AnyMarshalerUnmarshaler()

ANY_MARSHALER_FACTORY = TypeMapMarshalerFactory({ta.Any: ANY_MARSHALER_UNMARSHALER})
ANY_UNMARSHALER_FACTORY = TypeMapUnmarshalerFactory({ta.Any: ANY_MARSHALER_UNMARSHALER})
