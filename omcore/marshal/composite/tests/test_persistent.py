from .... import collections as col
from ...api.types import SimpleMarshaling
from ...factories.multi import MultiMarshalerFactory
from ...factories.multi import MultiUnmarshalerFactory
from ...singular.primitives import PRIMITIVE_MARSHALER_FACTORY
from ...singular.primitives import PRIMITIVE_UNMARSHALER_FACTORY
from ..persistent import PersistentMappingMarshalerFactory
from ..persistent import PersistentMappingUnmarshalerFactory
from ..persistent import PersistentSequenceMarshalerFactory
from ..persistent import PersistentSequenceUnmarshalerFactory


def test_persistent():
    msh = SimpleMarshaling(
        marshaler_factory=MultiMarshalerFactory(
            PersistentSequenceMarshalerFactory(),
            PersistentMappingMarshalerFactory(),
            PRIMITIVE_MARSHALER_FACTORY,
        ),
        unmarshaler_factory=MultiUnmarshalerFactory(
            PersistentSequenceUnmarshalerFactory(),
            PersistentMappingUnmarshalerFactory(),
            PRIMITIVE_UNMARSHALER_FACTORY,
        ),
    )

    seq = col.new_persistent_seq([1, 2, 10])
    seq_v = msh.marshal(seq, col.PersistentSequence[int])
    assert seq_v == [1, 2, 10]
    seq2 = msh.unmarshal(seq_v, col.PersistentSequence[int])
    assert list(seq2) == list(seq)

    dct = col.new_persistent_map({1: 10, 2: 20, 10: 100}.items())
    dct_v = msh.marshal(dct, col.PersistentMapping[int, int])
    assert dct_v == {1: 10, 2: 20, 10: 100}
    dct2 = msh.unmarshal(dct_v, col.PersistentMapping[int, int])
    assert dict(dct2) == dict(dct)
