import pytest

from ..ranked import RankedSeq
from ..ranked import RankedSetSeq


class Equal:
    def __eq__(self, other):
        return isinstance(other, Equal)

    def __hash__(self):
        return 0


def test_ranked_seq():
    ranked = RankedSeq(['b', 'a', 'c'])

    assert list(ranked) == ['b', 'a', 'c']
    assert ranked[1] == 'a'
    assert ranked.rank('c') == 2
    assert ranked.ranks == {'b': 0, 'a': 1, 'c': 2}
    assert 'a' in ranked

    with pytest.raises(ValueError, match='1 != 2'):
        RankedSeq(['a', 'a'])


def test_ranked_seq_identity():
    a = Equal()
    b = Equal()

    ranked = RankedSeq([a, b], identity=True)
    assert ranked.rank(a) == 0
    assert ranked.rank(b) == 1


def test_ranked_set_seq():
    ranked = RankedSetSeq([
        ['a', 'b'],
        ['c'],
    ])

    assert list(map(set, ranked)) == [{'a', 'b'}, {'c'}]
    assert ranked.rank('b') == 0
    assert ranked.rank('c') == 1

    with pytest.raises(ValueError, match='1 != 2'):
        RankedSetSeq([['a'], ['a']])


def test_ranked_set_seq_identity():
    a = Equal()
    b = Equal()

    ranked = RankedSetSeq([[a], [b]], identity=True)
    assert ranked.rank(a) == 0
    assert ranked.rank(b) == 1
