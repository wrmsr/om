import pytest

from ...api._runtime import make_runtime
from ...api.contexts import MarshalContext
from ...api.contexts import MarshalFactoryContext
from ...api.contexts import UnmarshalContext
from ...api.contexts import UnmarshalFactoryContext
from ...standard.factories import StandardMarshalerFactory
from ...standard.factories import StandardUnmarshalerFactory
from ..tuples import FixedTupleMarshaler
from ..tuples import FixedTupleUnmarshaler
from ..tuples import VariadicTupleMarshaler
from ..tuples import VariadicTupleUnmarshaler


def test_fixed_tuple_marshal_unmarshal():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )
    mfc = MarshalFactoryContext(runtime=rt)
    mc = MarshalContext(runtime=rt)
    ufc = UnmarshalFactoryContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)

    marshaler = mfc.make_marshaler(tuple[int, str])
    unmarshaler = ufc.make_unmarshaler(tuple[int, str])

    assert isinstance(marshaler, FixedTupleMarshaler)
    assert len(marshaler.es) == 2
    assert isinstance(unmarshaler, FixedTupleUnmarshaler)
    assert len(unmarshaler.es) == 2

    assert marshaler.marshal(mc, (1, 'two')) == [1, 'two']
    assert unmarshaler.unmarshal(uc, [1, 'two']) == (1, 'two')


def test_variadic_tuple_marshal_unmarshal():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )
    mfc = MarshalFactoryContext(runtime=rt)
    mc = MarshalContext(runtime=rt)
    ufc = UnmarshalFactoryContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)

    marshaler = mfc.make_marshaler(tuple[int, ...])
    unmarshaler = ufc.make_unmarshaler(tuple[int, ...])

    assert isinstance(marshaler, VariadicTupleMarshaler)
    assert isinstance(unmarshaler, VariadicTupleUnmarshaler)
    assert marshaler.marshal(mc, (1, 2, 3)) == [1, 2, 3]
    assert unmarshaler.unmarshal(uc, [1, 2, 3]) == (1, 2, 3)
    assert marshaler.marshal(mc, ()) == []
    assert unmarshaler.unmarshal(uc, []) == ()

    bare_marshaler = mfc.make_marshaler(tuple)
    bare_unmarshaler = ufc.make_unmarshaler(tuple)
    assert isinstance(bare_marshaler, VariadicTupleMarshaler)
    assert isinstance(bare_unmarshaler, VariadicTupleUnmarshaler)
    assert bare_marshaler.marshal(mc, ('any', 1)) == ['any', 1]
    assert bare_unmarshaler.unmarshal(uc, ['any', 1]) == ('any', 1)


def test_empty_fixed_tuple():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )
    mc = MarshalContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    mfc = MarshalFactoryContext(runtime=rt)
    ufc = UnmarshalFactoryContext(runtime=rt)

    assert mfc.make_marshaler(tuple[()]).marshal(mc, ()) == []
    assert ufc.make_unmarshaler(tuple[()]).unmarshal(uc, []) == ()


def test_fixed_tuple_length_mismatch():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )
    mc = MarshalContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    mfc = MarshalFactoryContext(runtime=rt)
    ufc = UnmarshalFactoryContext(runtime=rt)

    with pytest.raises(ValueError, match='Expected tuple of length'):
        mfc.make_marshaler(tuple[int, str]).marshal(mc, (1,))

    with pytest.raises(ValueError, match='Expected tuple of length'):
        ufc.make_unmarshaler(tuple[int, str]).unmarshal(uc, [1])

    with pytest.raises(ValueError, match='Expected tuple of length'):
        ufc.make_unmarshaler(tuple[int, str]).unmarshal(uc, [1, 'two', 3])


def test_tuple_input_validation():
    rt = make_runtime(
        marshaler_factory=StandardMarshalerFactory(),
        unmarshaler_factory=StandardUnmarshalerFactory(),
    )
    mc = MarshalContext(runtime=rt)
    uc = UnmarshalContext(runtime=rt)
    mfc = MarshalFactoryContext(runtime=rt)
    ufc = UnmarshalFactoryContext(runtime=rt)

    with pytest.raises(TypeError):
        mfc.make_marshaler(tuple[int, ...]).marshal(mc, [1, 2])

    with pytest.raises(TypeError):
        ufc.make_unmarshaler(tuple[int, ...]).unmarshal(uc, '12')
