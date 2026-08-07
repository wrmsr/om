import pytest

from ... import dataclasses as dc
from ..api.errors import UnhandledTypeError
from ..api.marshaling import SimpleMarshaling
from ..api.specs import InternalSpec
from ..api.vias import MarshalVia
from ..api.vias import UnmarshalVia
from ..factories.multi import MultiMarshalerFactory
from ..factories.multi import MultiUnmarshalerFactory
from ..objects.helpers import update_field_options
from ..objects.infos import FieldInfo
from ..objects.infos import FieldInfos
from ..objects.marshal import ObjectMarshalerFactory
from ..objects.marshal import SimpleObjectMarshalerFactory
from ..objects.specs import ObjectSpec
from ..objects.unmarshal import ObjectUnmarshalerFactory
from ..objects.unmarshal import SimpleObjectUnmarshalerFactory
from ..singular.primitives import PRIMITIVE_MARSHALER_FACTORY
from ..singular.primitives import PRIMITIVE_UNMARSHALER_FACTORY
from ..standard.factories import new_standard_marshaler_factory
from ..standard.factories import new_standard_unmarshaler_factory


@dc.dataclass(frozen=True)
class Point:
    x: int
    y: int


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


def _point_spec() -> ObjectSpec:
    return ObjectSpec(
        ty=Point,
        fields=FieldInfos([
            FieldInfo(name='x', type=int, marshal_name='ex', unmarshal_names=['ex']),
            FieldInfo(name='y', type=int, marshal_name='why', unmarshal_names=['why', 'y2']),
        ]),
    )


def test_spec_as_direct_target():
    m = _new_marshaling()

    spec = _point_spec()
    assert m.marshal(Point(1, 2), spec) == {'ex': 1, 'why': 2}
    assert m.unmarshal({'ex': 1, 'why': 2}, spec) == Point(1, 2)
    assert m.unmarshal({'ex': 1, 'y2': 2}, spec) == Point(1, 2)

    # The derived default shape is unaffected by the spec-keyed entries.
    assert m.marshal(Point(1, 2)) == {'x': 1, 'y': 2}


def test_specs_are_value_keyed():
    m = _new_marshaling()
    mfc = m.new_marshal_factory_context()

    h1 = mfc.make_marshaler(_point_spec())
    h2 = mfc.make_marshaler(_point_spec())
    assert h1 is h2


def test_spec_in_via():
    @dc.dataclass(frozen=True)
    @update_field_options('p', marshal_via=MarshalVia(_point_spec()), unmarshal_via=UnmarshalVia(_point_spec()))
    class Holder:
        p: Point

    m = _new_marshaling()

    mv = m.marshal(Holder(Point(1, 2)))
    assert mv == {'p': {'ex': 1, 'why': 2}}
    assert m.unmarshal(mv, Holder) == Holder(Point(1, 2))


def test_unknown_internal_spec_is_unhandled():
    class WeirdSpec(InternalSpec):
        pass

    m = _new_marshaling()

    with pytest.raises(UnhandledTypeError):
        m.marshal(5, WeirdSpec())


class KwThing:
    def __init__(self, *, a: int) -> None:
        super().__init__()

        self.a = a

    def __eq__(self, other):
        return type(other) is KwThing and other.a == self.a

    def __hash__(self):
        return hash((KwThing, self.a))


def test_simple_object_factories_rederive_through_specs():
    fis = [FieldInfo(name='a', type=int, marshal_name='a', unmarshal_names=['a'])]

    m = SimpleMarshaling(
        marshaler_factory=MultiMarshalerFactory(
            SimpleObjectMarshalerFactory({KwThing: fis}),
            ObjectMarshalerFactory(),
            PRIMITIVE_MARSHALER_FACTORY,
        ),
        unmarshaler_factory=MultiUnmarshalerFactory(
            SimpleObjectUnmarshalerFactory({KwThing: fis}),
            ObjectUnmarshalerFactory(),
            PRIMITIVE_UNMARSHALER_FACTORY,
        ),
    )

    mv = m.marshal(KwThing(a=420), KwThing)
    assert mv == {'a': 420}
    assert m.unmarshal(mv, KwThing) == KwThing(a=420)
