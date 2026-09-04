import pytest

from ..building import D


def test_remove_strict():
    first = D.span('first')
    target = D.span('target')
    root = D.div(first, target)

    assert root.remove(target, strict=True) is root
    assert root.body == [first]

    with pytest.raises(ValueError, match='not in body'):
        root.remove(target, strict=True)

    empty = D.div()
    with pytest.raises(ValueError, match='not in body'):
        empty.remove(target, strict=True)
