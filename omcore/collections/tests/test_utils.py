import pytest

from ... import lang
from ..utils import PartitionResult
from ..utils import make_map
from ..utils import make_map_by
from ..utils import map_keys
from ..utils import map_values
from ..utils import multi_map
from ..utils import multi_map_by
from ..utils import partition
from ..utils import unique


class Equal:
    def __eq__(self, other):
        return isinstance(other, Equal)

    def __hash__(self):
        return 0


def test_partition():
    assert partition(range(5), lambda value: value % 2 == 0) == PartitionResult(
        [0, 2, 4],
        [1, 3],
    )


def test_unique():
    assert unique([1, 2, 1, 3, 2]) == [1, 2, 3]
    assert unique(['a', 'A', 'b'], key=str.lower) == ['a', 'b']

    a = Equal()
    b = Equal()
    assert unique([a, b]) == [a]
    assert unique([a, b], identity=True) == [a, b]

    with pytest.raises(lang.DuplicateKeyError):
        unique([1, 1], strict=True)
    with pytest.raises(TypeError):
        unique('abc')


def test_make_map():
    assert make_map([('a', 1), ('b', 2)]) == {'a': 1, 'b': 2}
    assert make_map_by(lambda value: value[0], ['a1', 'b2']) == {'a': 'a1', 'b': 'b2'}

    with pytest.raises(lang.DuplicateKeyError):
        make_map([('a', 1), ('a', 2)], strict=True)


def test_map_keys_and_values():
    assert map_keys(str.upper, {'a': 1, 'b': 2}) == {'A': 1, 'B': 2}
    assert map_values(str, [('a', 1), ('b', 2)]) == {'a': '1', 'b': '2'}

    with pytest.raises(lang.DuplicateKeyError):
        map_keys(str.lower, {'a': 1, 'A': 2}, strict=True)


def test_multi_map():
    assert multi_map([('a', 1), ('b', 2), ('a', 3)]) == {
        'a': [1, 3],
        'b': [2],
    }
    assert multi_map_by(lambda value: value % 2, range(5)) == {
        0: [0, 2, 4],
        1: [1, 3],
    }
