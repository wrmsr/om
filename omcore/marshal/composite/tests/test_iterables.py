import typing as ta

import pytest

from ...api._runtime import make_runtime
from ...api.contexts import UnmarshalContext
from ...api.contexts import UnmarshalFactoryContext
from ...api.options import Options
from ...standard.factories import StandardUnmarshalerFactory
from ..api import DefaultIterableConstructors


def test_ctor_option():
    ufc = UnmarshalFactoryContext(runtime=(rt := make_runtime(unmarshaler_factory=StandardUnmarshalerFactory())))

    uc = UnmarshalContext(runtime=rt)
    u = ufc.make_unmarshaler(ta.Sequence[int]).unmarshal(uc, [1, 2, 3])
    assert u == (1, 2, 3)

    uc = UnmarshalContext(runtime=rt, options=Options(
        DefaultIterableConstructors(sequence=list),
    ))
    u = ufc.make_unmarshaler(ta.Sequence[int]).unmarshal(uc, [1, 2, 3])
    assert u == [1, 2, 3]


def test_str_not_iterable_input():
    # A str is iterable but must not be silently exploded into characters.
    ufc = UnmarshalFactoryContext(runtime=(rt := make_runtime(unmarshaler_factory=StandardUnmarshalerFactory())))
    uc = UnmarshalContext(runtime=rt)

    with pytest.raises(TypeError):
        ufc.make_unmarshaler(ta.Sequence[str]).unmarshal(uc, 'abc')

    with pytest.raises(TypeError):
        ufc.make_unmarshaler(list[str]).unmarshal(uc, 'abc')
