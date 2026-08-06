import typing as ta

import pytest

from ... import dataclasses as dc
from ..api.configs import ConfigRegistry
from ..api.configs import LazyInit
from ..api.errors import UnhandledTypeError
from ..api.funcs import FuncMarshaler
from ..api.marshaling import SimpleMarshaling
from ..api.naming import Naming
from ..api.options import update_default_options
from ..api.vias import MarshalVia
from ..composite.api import DefaultIterableConstructors
from ..factories.typemap import TypeMapMarshalerFactory
from ..standard.factories import new_standard_marshaler_factory
from ..standard.factories import new_standard_unmarshaler_factory
from ..standard.install import install_standard_factories


@dc.dataclass(frozen=True)
class Point:
    x_val: int
    y_val: int


@dc.dataclass(frozen=True)
class Other:
    s: str


@dc.dataclass(frozen=True)
class Node:
    name: str
    children: ta.Sequence['Node'] = ()  # noqa


class Weird:
    pass


def _new_marshaling(cfgs=None):
    return SimpleMarshaling(
        **(dict(config_registry=cfgs) if cfgs is not None else {}),
        marshaler_factory=new_standard_marshaler_factory(),
        unmarshaler_factory=new_standard_unmarshaler_factory(),
    )


def test_footprint_invalidation_is_precise():
    m = _new_marshaling()

    assert m.marshal(Point(1, 2)) == {'x_val': 1, 'y_val': 2}

    mfc = m.new_marshal_factory_context()
    other_h = mfc.make_marshaler(Other)
    point_h = mfc.make_marshaler(Point)

    # Registering config for Point invalidates Point's cached handler - its construction read Point's config key...
    m.config_registry.update(Point, Naming.LOW_CAMEL)
    assert m.marshal(Point(1, 2)) == {'xVal': 1, 'yVal': 2}
    assert mfc.make_marshaler(Point) is not point_h

    # ...but Other's handler survives, revalidated in place.
    assert mfc.make_marshaler(Other) is other_h


def test_negative_entry_invalidation():
    m = _new_marshaling()

    with pytest.raises(UnhandledTypeError):
        m.marshal(Weird(), Weird)
    with pytest.raises(UnhandledTypeError):
        m.marshal(Weird(), Weird)

    # The failed construction observed the absence of a via for Weird - registering one must invalidate the cached
    # negative entry.
    m.config_registry.update(Weird, MarshalVia(FuncMarshaler(lambda ctx, o: 'weird!')))

    assert m.marshal(Weird(), Weird) == 'weird!'


def test_lazy_init_default_options_apply_to_first_op():
    cfgs = ConfigRegistry()

    def init(cr: ConfigRegistry) -> None:
        update_default_options(cr, DefaultIterableConstructors(sequence=list))

    cfgs.update(None, LazyInit(init))

    m = _new_marshaling(cfgs)

    # The very first operation must already see the lazily-registered default options.
    assert m.unmarshal([1, 2, 3], ta.Sequence[int]) == [1, 2, 3]
    assert isinstance(m.unmarshal([1, 2, 3], ta.Sequence[int]), list)


def test_late_lazy_init_runs_once():
    m = _new_marshaling()

    assert m.marshal(5) == 5

    ran: list = []

    def init(cr: ConfigRegistry) -> None:
        ran.append(1)
        cr.update(Point, Naming.LOW_CAMEL)

    m.config_registry.update(None, LazyInit(init))

    assert m.marshal(Point(1, 2)) == {'xVal': 1, 'yVal': 2}
    assert ran == [1]

    assert m.marshal(Point(1, 2)) == {'xVal': 1, 'yVal': 2}
    assert ran == [1]


def test_sealed_registry_usable():
    # First use must not mutate the registry (there is no auto-installed default factory config anymore).
    cfgs = ConfigRegistry().seal()

    m = _new_marshaling(cfgs)

    assert m.marshal(420) == 420
    assert m.unmarshal(420, int) == 420


def test_install_standard_factories_after_first_use():
    m = _new_marshaling()

    assert m.marshal(Other('a')) == {'s': 'a'}

    install_standard_factories(
        m.config_registry,
        TypeMapMarshalerFactory({Other: FuncMarshaler(lambda ctx, o: 'other!')}),
    )

    assert m.marshal(Other('a')) == 'other!'

    # Unrelated types are unaffected.
    assert m.marshal(Point(1, 2)) == {'x_val': 1, 'y_val': 2}


def test_flush():
    m = _new_marshaling()
    mfc = m.new_marshal_factory_context()

    h1 = mfc.make_marshaler(Other)
    assert mfc.make_marshaler(Other) is h1

    m.get_runtime().flush()

    h2 = mfc.make_marshaler(Other)
    assert h2 is not h1

    assert m.marshal(Other('a')) == {'s': 'a'}


def test_recursive_construction():
    m = _new_marshaling()

    v = Node('r', (Node('a', (Node('b'),)), Node('c')))
    mv = m.marshal(v)
    assert mv == {
        'name': 'r',
        'children': [
            {'name': 'a', 'children': [{'name': 'b', 'children': []}]},
            {'name': 'c', 'children': []},
        ],
    }
    assert m.unmarshal(mv, Node) == v
