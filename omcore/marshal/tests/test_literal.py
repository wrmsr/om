import typing as ta

from ... import check
from ... import reflect as rfl
from ..api.contexts import MarshalContext
from ..api.contexts import MarshalFactoryContext
from ..api.contexts import UnmarshalContext
from ..api.contexts import UnmarshalFactoryContext
from ..api.runtime import Runtime
from ..standard.factories import StandardMarshalerFactory
from ..standard.factories import StandardUnmarshalerFactory


Foo: ta.TypeAlias = ta.Literal['a', 'b', 'c']


def test_literal():
    mf = StandardMarshalerFactory()
    uf = StandardUnmarshalerFactory()

    rt = Runtime(
        marshaler_factory=mf,
        unmarshaler_factory=uf,
    )

    mfc = MarshalFactoryContext(runtime=rt)
    mc = MarshalContext(runtime=rt)
    assert check.not_none(mf.make_marshaler(mfc, rfl.reflect_type(Foo)))().marshal(mc, 'a') == 'a'

    ufc = UnmarshalFactoryContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    assert check.not_none(uf.make_unmarshaler(ufc, rfl.reflect_type(Foo)))().unmarshal(uc, 'a') == 'a'
