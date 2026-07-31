from ..proxy import ProxyMapping
from ..proxy import ProxySequence
from ..proxy import ProxySet


def test_proxy_sequence():
    seq = ProxySequence([1, 2, 3])

    assert repr(seq) == 'ProxySequence([1, 2, 3])'
    assert list(reversed(seq)) == [3, 2, 1]
    assert seq[1:] == [2, 3]
    assert seq.index(2) == 1


def test_proxy_set():
    st = ProxySet({2, 3})

    assert st < {1, 2, 3}
    assert st > {2}
    assert ({1, 2} & st) == {2}
    assert ({1, 2} | st) == {1, 2, 3}
    assert ({1, 2} - st) == {1}
    assert ({1, 2} ^ st) == {1, 3}


def test_proxy_mapping():
    mapping = ProxyMapping({'a': 1, 'b': 2})

    assert dict(mapping) == {'a': 1, 'b': 2}
    assert mapping.get('c', 3) == 3
    assert list(mapping.items()) == [('a', 1), ('b', 2)]
