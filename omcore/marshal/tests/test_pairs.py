import pytest

from ..api.types import FactoryPair
from ..api.types import HandlerPair
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory


def test_handler_pair_enforced():
    with pytest.raises(TypeError):
        class Bad(Marshaler, Unmarshaler):  # noqa
            def marshal(self, ctx, o):
                return o

            def unmarshal(self, ctx, v):
                return v

    class Good(HandlerPair):
        def marshal(self, ctx, o):
            return o

        def unmarshal(self, ctx, v):
            return v

    g = Good()
    assert isinstance(g, Marshaler)
    assert isinstance(g, Unmarshaler)
    assert isinstance(g, HandlerPair)


def test_handler_pair_fixes_mro():
    # The pair base fixes the mro order (Marshaler then Unmarshaler) - conflicting base orders are rejected by python
    # itself.
    with pytest.raises(TypeError):
        class Bad(Unmarshaler, HandlerPair):  # type: ignore[misc]  # noqa
            pass


def test_factory_pair_enforced():
    with pytest.raises(TypeError):
        class Bad(MarshalerFactory, UnmarshalerFactory):  # noqa
            def make_marshaler(self, ctx, rty):
                return None

            def make_unmarshaler(self, ctx, rty):
                return None

    class Good(FactoryPair):
        def make_marshaler(self, ctx, rty):
            return None

        def make_unmarshaler(self, ctx, rty):
            return None

    g = Good()
    assert isinstance(g, MarshalerFactory)
    assert isinstance(g, UnmarshalerFactory)
    assert isinstance(g, FactoryPair)


def test_single_role_unaffected():
    class M(Marshaler):
        def marshal(self, ctx, o):
            return o

    class U(Unmarshaler):
        def unmarshal(self, ctx, v):
            return v

    assert not isinstance(M(), HandlerPair)
    assert not isinstance(U(), HandlerPair)
