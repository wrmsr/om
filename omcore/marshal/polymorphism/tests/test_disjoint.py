import typing as ta

import pytest

from .... import dataclasses as dc
from ...api.marshaling import SimpleMarshaling
from ...api.naming import as_naming
from ...standard.factories import new_standard_marshaler_factory
from ...standard.factories import new_standard_unmarshaler_factory
from ..api import DisjointPolymorphism
from ..api import FieldTypeTagging
from ..api import PolymorphismSubtypeError
from ..api import PolymorphismTaggingError
from ..api import SubclassesSubtypeSource
from ..api import polymorphism_from_subclasses
from ..api import set_polymorphic
from ..marshal import PolymorphismMarshalerFactory
from ..specs import DisjointPolymorphismSpec
from ..specs import PolymorphismSpec
from ..unmarshal import PolymorphismUnmarshalerFactory


##


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake')
class Fruit:
    pass


@dc.dataclass(frozen=True)
class Apple(Fruit):
    crisp: bool = True


@dc.dataclass(frozen=True)
class Banana(Fruit):
    ripe: bool = True


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake')
class Tool:
    pass


@dc.dataclass(frozen=True)
class Hammer(Tool):
    heads: int = 1


@dc.dataclass(frozen=True)
class Saw(Tool):
    teeth: int = 24


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


##


def test_multi_root_union_roundtrip():
    m = _new_marshaling()

    u = Fruit | Tool

    assert (mv := m.marshal(Apple(), u)) == {'apple': {'crisp': True}}
    assert m.unmarshal(mv, u) == Apple()

    assert (mv := m.marshal(Hammer(), u)) == {'hammer': {'heads': 1}}
    assert m.unmarshal(mv, u) == Hammer()


def test_tag_stability_across_entry_paths():
    # A subtype's wire form must be identical via its own root, the full disjoint union, and a narrowed union.
    m = _new_marshaling()

    via_root = m.marshal(Banana(), Fruit)
    via_union = m.marshal(Banana(), Fruit | Tool)
    via_narrow = m.marshal(Banana(), Banana | Hammer)

    assert via_root == via_union == via_narrow == {'banana': {'ripe': True}}


def test_narrowed_cross_root_union():
    m = _new_marshaling()

    u = Apple | Hammer

    assert (mv := m.marshal(Apple(), u)) == {'apple': {'crisp': True}}
    assert m.unmarshal(mv, u) == Apple()
    assert m.unmarshal({'hammer': {'heads': 2}}, u) == Hammer(2)

    # The restriction is real: subtypes outside the union's members are rejected.
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(Saw(), u)


def test_member_order_converges():
    m = _new_marshaling()
    mfc = m.new_marshal_factory_context()

    # Differently-ordered union annotations converge on one canonical spec - and thus one handler.
    assert mfc.make_marshaler(Fruit | Tool) is mfc.make_marshaler(Tool | Fruit)


##


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake', suffix_stripping='required')
class Cat:
    pass


@dc.dataclass(frozen=True)
class NoisyCat(Cat):
    pass


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake', suffix_stripping='required')
class Dog:
    pass


@dc.dataclass(frozen=True)
class NoisyDog(Dog):
    pass


def test_cross_root_tag_collision():
    # Both roots derive the tag 'noisy' for their subtype - a real conflict, loudly rejected.
    m = _new_marshaling()

    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(NoisyDog(), Cat | Dog)


##


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake')
class Wrapped:
    pass


@dc.dataclass(frozen=True)
class AWrapped(Wrapped):
    pass


@dc.dataclass(frozen=True)
@set_polymorphic(naming='snake', type_tagging=FieldTypeTagging('$kind'))
class Fielded:
    pass


@dc.dataclass(frozen=True)
class BFielded(Fielded):
    pass


def test_tagging_mismatch_raises():
    m = _new_marshaling()

    with pytest.raises(PolymorphismTaggingError):
        m.marshal(AWrapped(), Wrapped | Fielded)


def test_disjoint_spec_tagging_mismatch_raises():
    with pytest.raises(PolymorphismTaggingError):
        DisjointPolymorphismSpec([
            PolymorphismSpec(root=Wrapped, sources=[SubclassesSubtypeSource()]),
            PolymorphismSpec(root=Fielded, sources=[SubclassesSubtypeSource()], tagging=FieldTypeTagging('$kind')),
        ])


##


def test_explicit_disjoint_polymorphism():
    dp = DisjointPolymorphism([
        polymorphism_from_subclasses(Fruit, naming='snake'),
        polymorphism_from_subclasses(Tool, naming='snake'),
    ])

    m = SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(first=[PolymorphismMarshalerFactory(dp)]),
        unmarshaler_factory=new_standard_unmarshaler_factory(first=[PolymorphismUnmarshalerFactory(dp)]),
    )

    # Matches each constituent root...
    assert (mv := m.marshal(Apple(), Fruit)) == {'apple': {'crisp': True}}
    assert m.unmarshal(mv, Fruit) == Apple()

    # ...and unions spanning constituents (member-is-root and concrete members alike).
    u = ta.Union[Fruit, Hammer]  # noqa
    assert (mv := m.marshal(Hammer(), u)) == {'hammer': {'heads': 1}}
    assert m.unmarshal(mv, u) == Hammer()
    assert m.unmarshal({'banana': {}}, u) == Banana()


def test_disjoint_spec_as_direct_target():
    m = _new_marshaling()

    spec = DisjointPolymorphismSpec([
        PolymorphismSpec(root=Fruit, sources=[SubclassesSubtypeSource()], naming=as_naming('snake')),
        PolymorphismSpec(root=Tool, sources=[SubclassesSubtypeSource()], naming=as_naming('snake')),
    ])

    assert (mv := m.marshal(Saw(), spec)) == {'saw': {'teeth': 24}}
    assert m.unmarshal(mv, spec) == Saw()
