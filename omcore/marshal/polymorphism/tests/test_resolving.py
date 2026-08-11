import pytest

from .... import dataclasses as dc
from .... import lang
from ...api.marshaling import SimpleMarshaling
from ...api.naming import CasingNaming
from ...standard.factories import new_standard_marshaler_factory
from ...standard.factories import new_standard_unmarshaler_factory
from ..api import ConfigsSubtypeSource
from ..api import ExplicitSubtypeSource
from ..api import LazySubtype
from ..api import PolymorphismSubtypeError
from ..api import SubclassesSubtypeSource
from ..api import SubtypeConfig
from ..api import SubtypeInfo
from ..api import SubtypeInfos
from ..api import SuffixStripping
from ..api import set_polymorphic
from ..manifests import SubtypeManifest
from ..resolving import match_subtype_manifests
from ..specs import PolymorphismSpec


##


@set_polymorphic(
    naming='snake',
    suffix_stripping='required',
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
    with pytest.raises(PolymorphismSubtypeError):
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
        sources=[ExplicitSubtypeSource(SubtypeInfos([
            SubtypeInfo(MessageSentEvent, 'ms', frozenset(['msg_sent'])),
            SubtypeInfo(UserClickedEvent, 'uc'),
        ]))],
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
            SubclassesSubtypeSource(),
            ExplicitSubtypeSource(SubtypeInfos([SubtypeInfo(MessageSentEvent, 'ms')])),
        ],
        naming=CasingNaming(lang.SNAKE_CASE),
        suffix_stripping=SuffixStripping(mode='required'),
    )

    assert m.marshal(MessageSentEvent('hi'), spec) == {'ms': {'msg': 'hi'}}
    assert m.marshal(UserClickedEvent(1), spec) == {'user_clicked': {'x': 1}}

    # Conflicting explicit tags for the same impl are an error.
    conflict_spec = PolymorphismSpec(
        root=Event,
        sources=[
            ExplicitSubtypeSource(SubtypeInfos([SubtypeInfo(MessageSentEvent, 'a')])),
            ExplicitSubtypeSource(SubtypeInfos([SubtypeInfo(MessageSentEvent, 'b')])),
        ],
    )
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(MessageSentEvent('x'), conflict_spec)

    # Conflicting tags across different impls are an error.
    tag_clash_spec = PolymorphismSpec(
        root=Event,
        sources=[
            ExplicitSubtypeSource(SubtypeInfos([
                SubtypeInfo(MessageSentEvent, 'same'),
                SubtypeInfo(UserClickedEvent, 'same'),
            ])),
        ],
    )
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(MessageSentEvent('x'), tag_clash_spec)


def test_config_tag_conflict():
    m = _new_marshaling()

    # Two configs claiming the same impl with different explicit tags conflict at resolution.
    m.config_registry.update(Event, SubtypeConfig(MessageSentEvent, tag='a'))
    m.config_registry.update(Event, SubtypeConfig(MessageSentEvent, tag='b'))

    spec = PolymorphismSpec(
        root=Event,
        sources=[ConfigsSubtypeSource()],
    )
    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(MessageSentEvent('x'), spec)


##


def test_impl_for_manifest_matching():
    vs = [
        SubtypeManifest(
            module='omfoo.agent.events',
            attr='MessageSentEvent',
            base='$.agent.types.Event',
        ),
        SubtypeManifest(
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

    assert match_subtype_manifests(FakeEvent, vs) == [vs[0]]

    class OtherRoot:
        pass

    OtherRoot.__module__ = 'omfoo.nope'
    OtherRoot.__qualname__ = 'Event'

    assert match_subtype_manifests(OtherRoot, vs) == []


def test_manifest_lazy_construction():
    # Mirrors the resolver's _manifest_raw_subtype: a manifest entry becomes a LazySubtype from static data alone -
    # the fqcn is assembled without any import.
    v = SubtypeManifest(
        module='omfoo.agent.events',
        attr='MessageSentEvent',
        base='$.agent.types.Event',
    )

    lz = LazySubtype(f'{v.module}.{v.attr}', v.resolve)
    assert lz.fqcn == 'omfoo.agent.events.MessageSentEvent'
