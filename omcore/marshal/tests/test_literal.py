import typing as ta

from ..api._runtime import make_runtime
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..standard.factories import StandardMarshalerFactory
from ..standard.factories import StandardUnmarshalerFactory


Foo: ta.TypeAlias = ta.Literal['a', 'b', 'c']


def test_literal():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )

    mfc = MarshalFactoryContext(runtime=rt)
    mc = MarshalContext(runtime=rt)
    assert mfc.make_marshaler(Foo).marshal(mc, 'a') == 'a'

    ufc = UnmarshalFactoryContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    assert ufc.make_unmarshaler(Foo).unmarshal(uc, 'a') == 'a'
