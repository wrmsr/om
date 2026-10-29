import re
import typing as ta

from ... import check
from ...re import regex_to_string
from ..api.contexts import MarshalContext
from ..api.contexts import UnmarshalContext
from ..api.types import DuplexHandler
from ..api.values import Value
from ..factories.typemap import TypeMapDuplexFactory


##


class PatternMarshalerUnmarshaler(DuplexHandler):
    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        return check.isinstance(regex_to_string(check.isinstance(o, re.Pattern)), str)

    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        return re.compile(check.isinstance(v, str))


PATTERN_MARSHALER_FACTORY = PATTERN_UNMARSHALER_FACTORY = TypeMapDuplexFactory({  # noqa
    re.Pattern: PatternMarshalerUnmarshaler(),
})
