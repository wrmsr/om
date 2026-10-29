import re
import uuid

from ... import check
from ..api.contexts import MarshalContext
from ..api.contexts import UnmarshalContext
from ..api.types import DuplexHandler
from ..api.values import Value
from ..factories.typemap import TypeMapDuplexFactory


##


PATTERN = re.compile(r'([0-9A-Fa-f]{8}-([0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12})|([0-9A-Fa-f]{32})')


class UuidMarshalerUnmarshaler(DuplexHandler):
    def marshal(self, ctx: MarshalContext, o: uuid.UUID) -> Value:
        return str(o)

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> uuid.UUID:
        return uuid.UUID(check.isinstance(v, str).replace('-', ''))


UUID_MARSHALER_UNMARSHALER = UuidMarshalerUnmarshaler()

UUID_MARSHALER_FACTORY = UUID_UNMARSHALER_FACTORY = TypeMapDuplexFactory({
    uuid.UUID: UUID_MARSHALER_UNMARSHALER,
})
