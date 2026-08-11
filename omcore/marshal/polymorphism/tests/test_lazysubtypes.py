import typing as ta

import pytest

from .... import dataclasses as dc
from .... import lang
from ...api.marshaling import SimpleMarshaling
from ...standard.factories import new_standard_marshaler_factory
from ...standard.factories import new_standard_unmarshaler_factory
from ..api import ExplicitSubtypeSource
from ..api import LazySubtype
from ..api import Polymorphism
from ..api import PolymorphismSubtypeError
from ..api import SubclassesSubtypeSource
from ..api import SubtypeInfo
from ..api import SubtypeInfos
from ..marshal import PolymorphismMarshalerFactory
from ..specs import PolymorphismSpec
from ..unmarshal import PolymorphismUnmarshalerFactory


##


@dc.dataclass(frozen=True)
class LzRoot:
    pass


@dc.dataclass(frozen=True)
class OneLz(LzRoot):
    a: int = 1


@dc.dataclass(frozen=True)
class TwoLz(LzRoot):
    b: int = 2


class _Counts:
    def __init__(self) -> None:
        super().__init__()

        self.dct: dict[str, int] = {}

    def lazy(self, cls: type, tag: str) -> SubtypeInfo:
        def resolve() -> type:
            self.dct[tag] = self.dct.get(tag, 0) + 1
            return cls

        return SubtypeInfo(
            LazySubtype(lang.get_cls_fqcn(cls), resolve),
            tag,
        )


def _new_marshaling():
    return SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


def _lazy_spec(cts: _Counts) -> PolymorphismSpec:
    return PolymorphismSpec(
        root=LzRoot,
        sources=[ExplicitSubtypeSource(SubtypeInfos([
            cts.lazy(OneLz, 'one'),
            cts.lazy(TwoLz, 'two'),
        ]))],
    )


##


def test_unmarshal_resolves_only_the_hit_tag():
    cts = _Counts()
    m = _new_marshaling()
    spec = _lazy_spec(cts)

    # Handler construction resolves nothing.
    u = m.new_unmarshal_factory_context().make_unmarshaler(spec)
    assert cts.dct == {}

    # First hit of a tag resolves that subtype - and nothing else.
    uc = m.new_unmarshal_context()
    assert u.unmarshal(uc, {'one': {'a': 5}}) == OneLz(5)
    assert cts.dct.get('one', 0) >= 1
    assert cts.dct.get('two', 0) == 0

    assert u.unmarshal(uc, {'two': {'b': 6}}) == TwoLz(6)
    assert cts.dct.get('two', 0) >= 1


def test_marshal_fqcn_fallback():
    cts = _Counts()
    m = _new_marshaling()
    spec = _lazy_spec(cts)

    # Handler construction resolves nothing; the marshal map is empty of lazy entries.
    mh = m.new_marshal_factory_context().make_marshaler(spec)
    assert cts.dct == {}

    # An instance of a lazily-declared (but by-definition loaded) class routes through the fqcn fallback.
    mc = m.new_marshal_context()
    assert mh.marshal(mc, OneLz(7)) == {'one': {'a': 7}}
    assert cts.dct.get('two', 0) == 0


def test_lazy_unifies_with_concrete_without_resolving():
    cts = _Counts()
    m = _new_marshaling()

    # The same class arrives lazily from one source and concretely from another (the subclass scan) - they unify by
    # fqcn, the concrete side wins, and the thunk is never called.
    spec = PolymorphismSpec(
        root=LzRoot,
        sources=[
            ExplicitSubtypeSource(SubtypeInfos([
                cts.lazy(OneLz, 'one'),
                cts.lazy(TwoLz, 'two'),
            ])),
            SubclassesSubtypeSource(),
        ],
    )

    assert (mv := m.marshal(OneLz(3), spec)) == {'one': {'a': 3}}
    assert m.unmarshal(mv, spec) == OneLz(3)
    assert cts.dct == {}


def test_only_restriction_matches_lazy_by_fqcn():
    cts = _Counts()
    m = _new_marshaling()

    spec = PolymorphismSpec(
        root=LzRoot,
        sources=[ExplicitSubtypeSource(SubtypeInfos([
            cts.lazy(OneLz, 'one'),
            cts.lazy(TwoLz, 'two'),
        ]))],
        only=[OneLz],
    )

    assert cts.dct == {}
    assert m.unmarshal({'one': {'a': 9}}, spec) == OneLz(9)
    assert cts.dct.get('two', 0) == 0

    with pytest.raises(Exception):  # noqa
        m.unmarshal({'two': {'b': 1}}, spec)


def test_explicit_union_matches_lazy_member():
    cts = _Counts()

    p = Polymorphism(
        LzRoot,
        SubtypeInfos([
            cts.lazy(OneLz, 'one'),
            SubtypeInfo(TwoLz, 'two'),
        ]),
    )

    m = SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(first=[PolymorphismMarshalerFactory(p)]),
        unmarshaler_factory=new_standard_unmarshaler_factory(first=[PolymorphismUnmarshalerFactory(p)]),
    )

    # The union member class is loaded but resolved as a lazy declaration - matched by fqcn.
    u = ta.Union[OneLz, TwoLz]  # noqa
    assert cts.dct == {}
    assert m.unmarshal({'one': {'a': 2}}, u) == OneLz(2)
    assert m.unmarshal({'two': {'b': 3}}, u) == TwoLz(3)


##


def test_imposter_class_conflicts():
    @dc.dataclass(frozen=True)
    class ImposterLz(LzRoot):
        pass

    # Simulate module-reload-style artifacts: a distinct class claiming OneLz's fqcn. Derived fqcns are round-trip
    # verified (lang.get_cls_fqcn), so the imposter cannot actually produce a colliding fqcn - it degrades to
    # identity keying and the collision surfaces as a tag conflict instead. Fail loudly either way.
    ImposterLz.__module__ = OneLz.__module__
    ImposterLz.__qualname__ = OneLz.__qualname__

    assert lang.get_cls_fqcn(ImposterLz, optional=True) is None
    assert lang.get_cls_fqcn(OneLz, optional=True) is not None

    m = _new_marshaling()

    spec = PolymorphismSpec(
        root=LzRoot,
        sources=[
            ExplicitSubtypeSource(SubtypeInfos([SubtypeInfo(OneLz, 'one')])),
            ExplicitSubtypeSource(SubtypeInfos([SubtypeInfo(ImposterLz, 'one')])),
        ],
    )

    with pytest.raises(PolymorphismSubtypeError):
        m.marshal(OneLz(1), spec)


def test_optional_union_through_explicit_factory():
    # An `X | None` union probed by an explicit polymorphism factory (member set including NoneType) must pass
    # cleanly to the Optional machinery regardless of member iteration order.
    p = Polymorphism(
        LzRoot,
        SubtypeInfos([SubtypeInfo(OneLz, 'one')]),
    )

    m = SimpleMarshaling(
        marshaler_factory=new_standard_marshaler_factory(first=[PolymorphismMarshalerFactory(p)]),
        unmarshaler_factory=new_standard_unmarshaler_factory(first=[PolymorphismUnmarshalerFactory(p)]),
    )

    u = ta.Optional[OneLz]  # noqa
    assert m.marshal(None, u) is None
    assert (mv := m.marshal(OneLz(4), u)) == {'a': 4}
    assert m.unmarshal(mv, u) == OneLz(4)
    assert m.unmarshal(None, u) is None


def _make_dynamic_subtype() -> type:
    @dc.dataclass(frozen=True)
    class DynLz(LzRoot):
        d: int = 4

    return DynLz


def test_dynamic_class_participates_without_fqcn():
    dyn = _make_dynamic_subtype()
    assert lang.get_cls_fqcn(dyn, optional=True) is None

    m = _new_marshaling()

    spec = PolymorphismSpec(
        root=LzRoot,
        sources=[ExplicitSubtypeSource(SubtypeInfos([
            SubtypeInfo(dyn, 'dyn'),
            SubtypeInfo(OneLz, 'one'),
        ]))],
    )

    assert (mv := m.marshal(dyn(8), spec)) == {'dyn': {'d': 8}}
    assert m.unmarshal(mv, spec) == dyn(8)
