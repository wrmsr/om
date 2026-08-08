"""The successor to the 'open polymorphism' tests: config-registered impls as a resolver source."""
import pytest

from .... import dataclasses as dc
from .... import lang
from ...api.marshaling import SimpleMarshaling
from ...api.naming import CasingNaming
from ...standard.factories import new_standard_marshaler_factory
from ...standard.factories import new_standard_unmarshaler_factory
from ..api import ConfigsSubtypeSource
from ..api import PolymorphismSubtypeError
from ..api import SubtypeConfig
from ..api import SuffixStripping
from ..api import set_polymorphic
from ..specs import PolymorphismSpec


@set_polymorphic(
    sources=['subclasses', 'configs'],
    naming='snake',
    suffix_stripping='required',
)
class Foo:
    pass


@dc.dataclass(frozen=True)
class IntFoo(Foo):
    i: int


@dc.dataclass(frozen=True)
class StrFoo(Foo):
    s: str


@dc.dataclass(frozen=True)
class BoolFoo(Foo):
    b: bool


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


def test_registered_tag_override_invalidates():
    m = _new_marshaling()

    # Baseline: subclass source finds the impls, tags derived per the root's config.
    assert (mv := m.marshal(IntFoo(420), Foo)) == {'int': {'i': 420}}
    assert m.unmarshal(mv, Foo) == IntFoo(420)

    # A late config registration must invalidate the cached handler (through its config footprint) and its explicit
    # tag must win over the derived one.
    m.config_registry.update(Foo, SubtypeConfig(IntFoo, tag='eye', alts=['aye']))

    assert (mv := m.marshal(IntFoo(420), Foo)) == {'eye': {'i': 420}}
    assert m.unmarshal(mv, Foo) == IntFoo(420)
    assert m.unmarshal({'aye': {'i': 420}}, Foo) == IntFoo(420)

    # Untouched impls keep their derived tags.
    assert (mv := m.marshal(StrFoo('x'), Foo)) == {'str': {'s': 'x'}}
    assert m.unmarshal(mv, Foo) == StrFoo('x')


def test_config_only_spec():
    m = _new_marshaling()

    spec = PolymorphismSpec(
        root=Foo,
        sources=[ConfigsSubtypeSource()],
        naming=CasingNaming(lang.SNAKE_CASE),
        suffix_stripping=SuffixStripping(mode='required'),
    )

    # No impls registered yet - resolution fails loudly at construction.
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(IntFoo(1), spec)

    m.config_registry.update(Foo, SubtypeConfig(IntFoo))
    m.config_registry.update(Foo, SubtypeConfig(StrFoo))

    assert (mv := m.marshal(IntFoo(1), spec)) == {'int': {'i': 1}}
    assert m.unmarshal(mv, spec) == IntFoo(1)

    # BoolFoo was never registered under this spec.
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(BoolFoo(True), spec)

    # Late registration is observed - the config read is in the spec handler's footprint.
    m.config_registry.update(Foo, SubtypeConfig(BoolFoo))
    assert (mv := m.marshal(BoolFoo(True), spec)) == {'bool': {'b': True}}
    assert m.unmarshal(mv, spec) == BoolFoo(True)
