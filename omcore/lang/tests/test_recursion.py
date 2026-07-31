import pytest

from ..recursion import LimitedRecursionError
from ..recursion import recursion_limiting
from ..recursion import recursion_limiting_context


def test_recursion():
    @recursion_limiting(5)
    def foo(x):
        return x + foo(x - 1) if x > 0 else 0

    assert foo(4) == 4 + 3 + 2 + 1

    with pytest.raises(LimitedRecursionError):
        foo(5)


def test_zero_recursion_limit_rejects_first_entry():
    with pytest.raises(LimitedRecursionError) as exc_info:
        with recursion_limiting_context('key', 0):
            pass

    assert exc_info.value.key == 'key'
    assert exc_info.value.depth == 0
