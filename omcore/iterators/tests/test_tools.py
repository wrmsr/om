from ..tools import expand_indexed_pairs
from ..tools import merge_on
from ..tools import take
from ..tools import unzip


def test_unzip():
    c0, c1, c2 = unzip(iter([
        (1, 2, 3),
        (4, 5, 6),
    ]))

    assert list(c1) == [2, 5]
    assert list(c0) == [1, 4]
    assert list(c2) == [3, 6]
    assert unzip(iter(())) == []


def test_take():
    it = iter(range(5))
    assert take(2, it) == [0, 1]
    assert list(it) == [2, 3, 4]


def test_merge_on():
    assert list(merge_on(
        lambda item: item[0],
        [('a', 1), ('c', 3)],
        [('a', 2), ('b', 4), ('c', 5)],
    )) == [
        ('a', [(0, ('a', 1)), (1, ('a', 2))]),
        ('b', [(1, ('b', 4))]),
        ('c', [(0, ('c', 3)), (1, ('c', 5))]),
    ]


def test_expand_indexed_pairs():
    assert expand_indexed_pairs([(1, 'b'), (3, 'd')], '-') == ['-', 'b', '-', 'd']
    assert expand_indexed_pairs(iter([(1, 'b'), (3, 'd')]), '-') == ['-', 'b', '-', 'd']
    assert expand_indexed_pairs(iter(()), '-') == []
    assert expand_indexed_pairs(iter([(1, 'b'), (3, 'd')]), '-', width=3) == ['-', 'b', '-']
