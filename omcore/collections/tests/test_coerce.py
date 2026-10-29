import typing as ta

import pytest

from .. import coerce
from ..frozen import Frozen


def test_coerce():
    r = coerce.seq_of(str)([1, 2])
    assert r == ['1', '2']
    assert isinstance(r, Frozen)  # type: ignore[unreachable]
    assert isinstance(r, ta.Sequence)  # type: ignore[unreachable]

    c = coerce.seq_of((int,))
    assert c([1, 2]) == [1, 2]
    with pytest.raises(TypeError):
        c([1, '2'])

    c = coerce.seq_of((int, None))
    assert c([1, 2, None]) == [1, 2, None]


def test_coerce_tuple():
    ft = (420, 'hi')
    tt = coerce.tuple_of(lambda i: str(i + 1), lambda s: len(s))(ft)

    assert tt == ('421', 2)
