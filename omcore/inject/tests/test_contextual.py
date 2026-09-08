import pytest

from ... import contextual as cxl
from ... import inject as inj


def test_contextual():
    @cxl.wrap()
    def foo(i: int, f: float = cxl.param()) -> str:
        return f'{i=} {f=}'

    with pytest.raises(cxl.UnboundError):
        _ = inj.create_injector(
            inj.bind(foo),
            inj.bind(420),
        )[str]

    s = inj.create_injector(
        inj.bind(foo),
        inj.bind(420),
        inj.bind(4.2),
    )[str]
    assert s == 'i=420 f=4.2'

    with cxl.bind({float: 2.1}):
        s = inj.create_injector(
            inj.bind(foo),
            inj.bind(420),
        )[str]
    assert s == 'i=420 f=2.1'
