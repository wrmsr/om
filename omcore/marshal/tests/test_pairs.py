import pytest

from ..api.types import DuplexFactory
from ..api.types import DuplexHandler
from ..api.types import Marshaler
from ..api.types import MarshalerFactory
from ..api.types import Unmarshaler
from ..api.types import UnmarshalerFactory


def test_duplex_handler_enforced():
    with pytest.raises(TypeError):
        class Bad(Marshaler, Unmarshaler):  # noqa
            def marshal(self, ctx, o):
                return o

            def unmarshal(self, ctx, v):
                return v

    class Good(DuplexHandler):
        def marshal(self, ctx, o):
            return o

        def unmarshal(self, ctx, v):
            return v

    g = Good()
    assert isinstance(g, Marshaler)
    assert isinstance(g, Unmarshaler)
    assert isinstance(g, DuplexHandler)


def test_duplex_handler_fixes_mro():
    # The duplex base fixes the mro order (Marshaler then Unmarshaler) - conflicting base orders are rejected by python
    # itself.
    with pytest.raises(TypeError):
        class Bad(Unmarshaler, DuplexHandler):  # type: ignore[misc]  # noqa
            pass


def test_duplex_factory_enforced():
    with pytest.raises(TypeError):
        class Bad(MarshalerFactory, UnmarshalerFactory):  # noqa
            def make_marshaler(self, ctx, rty):
                return None

            def make_unmarshaler(self, ctx, rty):
                return None

    class Good(DuplexFactory):
        def make_marshaler(self, ctx, rty):
            return None

        def make_unmarshaler(self, ctx, rty):
            return None

    g = Good()
    assert isinstance(g, MarshalerFactory)
    assert isinstance(g, UnmarshalerFactory)
    assert isinstance(g, DuplexFactory)


def test_single_role_unaffected():
    class M(Marshaler):
        def marshal(self, ctx, o):
            return o

    class U(Unmarshaler):
        def unmarshal(self, ctx, v):
            return v

    assert not isinstance(M(), DuplexHandler)
    assert not isinstance(U(), DuplexHandler)
