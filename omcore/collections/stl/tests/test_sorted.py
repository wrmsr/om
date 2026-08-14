import pytest

from .... import collections as col
from .. import _stl as fc  # type: ignore


def test_skiplistdict():
    dct: col.SortedMutableMapping[float, str] = fc.Map('float64', 'object')
    dct[4] = 'd'
    dct[2] = 'b'
    dct[5] = 'e'

    assert dct[2] == 'b'
    assert list(dct) == [2, 4, 5]
    assert list(dct.items()) == [(2, 'b'), (4, 'd'), (5, 'e')]
    assert list(dct.values()) == ['b', 'd', 'e']
    assert list(dct.items_desc()) == [(5, 'e'), (4, 'd'), (2, 'b')]

    assert list(dct.items_from(3.9)) == [(4, 'd'), (5, 'e')]
    assert list(dct.items_from(4)) == [(4, 'd'), (5, 'e')]
    assert list(dct.items_from(4.1)) == [(5, 'e')]

    assert list(dct.items_from_desc(4.1)) == [(4, 'd'), (2, 'b')]
    assert list(dct.items_from_desc(4)) == [(4, 'd'), (2, 'b')]
    assert list(dct.items_from_desc(3.9)) == [(2, 'b')]
    assert list(dct.items_from_desc(6)) == [(5, 'e'), (4, 'd'), (2, 'b')]

    del dct[4]
    assert list(dct.items()) == [(2, 'b'), (5, 'e')]
    with pytest.raises(KeyError):
        del dct[4]


def test_sorted_list_dict():
    assert dict(fc.Map('int64', 'int64')) == {}
    assert dict(fc.Map('int64', 'int64', {3: 4, 1: 2})) == {1: 2, 3: 4}
