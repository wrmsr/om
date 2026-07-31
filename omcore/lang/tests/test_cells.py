import pytest

from ..cells import cell
from ..cells import cell_cell


def test_cell():
    c = cell('first')

    assert c() == 'first'
    c.set('second')
    assert c() == 'second'
    assert repr(c) == "_Cell('second')"

    with pytest.raises(TypeError):
        bool(c)
    with pytest.raises(TypeError):
        hash(c)
    with pytest.raises(TypeError):
        c == c  # noqa


def test_closure_cell():
    value = 'first'

    def get():
        return value

    assert get.__closure__ is not None
    closure_cell = get.__closure__[0]
    c = cell_cell(closure_cell)

    assert c() == 'first'
    c.set('second')
    assert c() == 'second'
    assert get() == 'second'
