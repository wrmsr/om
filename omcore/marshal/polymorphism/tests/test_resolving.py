import pytest

from .... import dataclasses as dc
from ...api.marshaling import SimpleMarshaling
from ...api.naming import Naming
from ...standard.factories import new_standard_marshaler_factory
from ...standard.factories import new_standard_unmarshaler_factory
from ..api import Impl
from ..api import PolymorphismImpl
from ..api import PolymorphismImplError
from ..api import set_polymorphic_from_subclasses
from ..manifests import ImplForManifest
from ..resolving import match_impl_for_manifests
from ..specs import ConfigImplSource
from ..specs import ExplicitImplSource
from ..specs import PolymorphismSpec
from ..specs import SubclassesImplSource


##


@set_polymorphic_from_subclasses(
    naming=Naming.SNAKE,
    strip_suffix=True,
)
class Event:
    pass


@dc.dataclass(frozen=True)
class MessageSentEvent(Event):
    msg: str


@dc.dataclass(frozen=True)
class UserClickedEvent(Event):
    x: int


@dc.dataclass(frozen=True)
class WorkerStartedEvent(Event):
    n: int


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


##


def test_metadata_polymorphism():
    m = _new_marshaling()

    assert (mv := m.marshal(MessageSentEvent('hi'), Event)) == {'message_sent': {'msg': 'hi'}}
    assert m.unmarshal(mv, Event) == MessageSentEvent('hi')


def test_union_of_impls():
    # The marquee: a union of impl subtypes of a polymorphic root resolves to the restricted polymorphism.
    m = _new_marshaling()

    u = MessageSentEvent | UserClickedEvent

    assert (mv := m.marshal(UserClickedEvent(3), u)) == {'user_clicked': {'x': 3}}
    assert m.unmarshal(mv, u) == UserClickedEvent(3)
    assert m.unmarshal({'message_sent': {'msg': 'yo'}}, u) == MessageSentEvent('yo')

    # The restriction is real: an impl outside the union's members is rejected.
    with pytest.raises(PolymorphismImplError):
        m.marshal(WorkerStartedEvent(1), u)


def test_union_including_root_lifts_restriction():
    m = _new_marshaling()

    u = Event | MessageSentEvent

    assert (mv := m.marshal(WorkerStartedEvent(1), u)) == {'worker_started': {'n': 1}}
    assert m.unmarshal(mv, u) == WorkerStartedEvent(1)


def test_explicit_source_spec():
    m = _new_marshaling()

    spec = PolymorphismSpec(
        root=Event,
        sources=[ExplicitImplSource([
            Impl(MessageSentEvent, 'ms', frozenset(['msg_sent'])),
            Impl(UserClickedEvent, 'uc'),
        ])],
    )

    assert (mv := m.marshal(MessageSentEvent('hi'), spec)) == {'ms': {'msg': 'hi'}}
    assert m.unmarshal(mv, spec) == MessageSentEvent('hi')
    assert m.unmarshal({'msg_sent': {'msg': 'yo'}}, spec) == MessageSentEvent('yo')
    assert m.unmarshal({'uc': {'x': 1}}, spec) == UserClickedEvent(1)


def test_source_merge_and_conflicts():
    m = _new_marshaling()

    # Same impl from two sources merges (explicit tag wins) - here subclass scan + explicit.
    spec = PolymorphismSpec(
        root=Event,
        sources=[
            SubclassesImplSource(),
            ExplicitImplSource([Impl(MessageSentEvent, 'ms')]),
        ],
        naming=Naming.SNAKE,
        strip_suffix=True,
    )

    assert m.marshal(MessageSentEvent('hi'), spec) == {'ms': {'msg': 'hi'}}
    assert m.marshal(UserClickedEvent(1), spec) == {'user_clicked': {'x': 1}}

    # Conflicting explicit tags for the same impl are an error.
    conflict_spec = PolymorphismSpec(
        root=Event,
        sources=[
            ExplicitImplSource([Impl(MessageSentEvent, 'a')]),
            ExplicitImplSource([Impl(MessageSentEvent, 'b')]),
        ],
    )
    with pytest.raises(PolymorphismImplError):
        m.marshal(MessageSentEvent('x'), conflict_spec)

    # Conflicting tags across different impls are an error.
    tag_clash_spec = PolymorphismSpec(
        root=Event,
        sources=[
            ExplicitImplSource([
                Impl(MessageSentEvent, 'same'),
                Impl(UserClickedEvent, 'same'),
            ]),
        ],
    )
    with pytest.raises(PolymorphismImplError):
        m.marshal(MessageSentEvent('x'), tag_clash_spec)


def test_config_tag_conflict():
    m = _new_marshaling()

    # Two configs claiming the same impl with different explicit tags conflict at resolution.
    m.config_registry.update(Event, PolymorphismImpl(MessageSentEvent, tag='a'))
    m.config_registry.update(Event, PolymorphismImpl(MessageSentEvent, tag='b'))

    spec = PolymorphismSpec(
        root=Event,
        sources=[ConfigImplSource()],
    )
    with pytest.raises(PolymorphismImplError):
        m.marshal(MessageSentEvent('x'), spec)


##


def test_impl_for_manifest_matching():
    vs = [
        ImplForManifest(
            module='omfoo.agent.events',
            attr='MessageSentEvent',
            base='$.agent.types.Event',
        ),
        ImplForManifest(
            module='omfoo.agent.events',
            attr='UserClickedEvent',
            base='ombar.other.Thing',
        ),
    ]

    assert vs[0].resolve_base_path() == 'omfoo.agent.types.Event'
    assert vs[1].resolve_base_path() == 'ombar.other.Thing'

    class FakeEvent:
        pass

    FakeEvent.__module__ = 'omfoo.agent.types'
    FakeEvent.__qualname__ = 'Event'

    assert match_impl_for_manifests(FakeEvent, vs) == [vs[0]]

    class OtherRoot:
        pass

    OtherRoot.__module__ = 'omfoo.nope'
    OtherRoot.__qualname__ = 'Event'

    assert match_impl_for_manifests(OtherRoot, vs) == []
