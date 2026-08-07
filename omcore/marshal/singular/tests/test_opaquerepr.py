from .... import dataclasses as dc
from .... import lang
from ...api.marshaling import SimpleMarshaling
from ...api.vias import MarshalVia
from ...api.vias import UnmarshalVia
from ...composite.optionals import OptionalMarshalerFactory
from ...composite.optionals import OptionalUnmarshalerFactory
from ...factories.multi import MultiMarshalerFactory
from ...factories.multi import MultiUnmarshalerFactory
from ...objects.dataclasses import DataclassFactory
from ...objects.helpers import update_field_options
from ...objects.marshal import ObjectMarshalerFactory
from ...objects.unmarshal import ObjectUnmarshalerFactory
from ..opaquerepr import OPAQUE_REPR_MARSHALER_FACTORY
from ..opaquerepr import OPAQUE_REPR_UNMARSHALER_FACTORY
from ..primitives import PRIMITIVE_MARSHALER_FACTORY
from ..primitives import PRIMITIVE_UNMARSHALER_FACTORY


class Baz:
    def __repr__(self) -> str:
        return 'baz!'


@dc.dataclass()
@update_field_options(
    'o',
    marshal_via=MarshalVia(lang.OpaqueRepr | None),
    unmarshal_via=UnmarshalVia(lang.OpaqueRepr | None),
)
class C:
    s: str
    o: Baz | lang.OpaqueRepr | None


def test_opaque_repr():
    msh = SimpleMarshaling(
        marshaler_factory=MultiMarshalerFactory(
            DataclassFactory(),
            ObjectMarshalerFactory(),
            OptionalMarshalerFactory(),
            OPAQUE_REPR_MARSHALER_FACTORY,
            PRIMITIVE_MARSHALER_FACTORY,
        ),
        unmarshaler_factory=MultiUnmarshalerFactory(
            DataclassFactory(),
            ObjectUnmarshalerFactory(),
            OptionalUnmarshalerFactory(),
            OPAQUE_REPR_UNMARSHALER_FACTORY,
            PRIMITIVE_UNMARSHALER_FACTORY,
        ),
    )

    assert msh.marshal('foo') == 'foo'
    assert (mv := msh.marshal(C('bar', None))) == {'s': 'bar', 'o': None}
    assert msh.unmarshal(mv, C) == C('bar', None)
    assert (mv := msh.marshal(C('bar', Baz()))) == {'s': 'bar', 'o': 'baz!'}
    assert msh.unmarshal(mv, C) == C('bar', lang.OpaqueRepr('baz!'))
