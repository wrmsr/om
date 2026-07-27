from ... import inject as inj
from ... import lang


def test_override():
    i = inj.create_injector(
        inj.override(
            inj.bind(420),
            inj.bind(421),
        ),
        inj.bind(5.2),
        inj.bind(lang.typed_lambda(str, i=int, f=float)(lambda i, f: f'{i}, {f}')),
    )
    assert i.provide(int) == 421
    assert i.provide(str) == '421, 5.2'


def test_override_new_keys():
    i = inj.create_injector(
        inj.override(
            inj.as_elements(
                inj.bind(420),
                inj.bind(lang.typed_lambda(str, i=int, f=float)(lambda i, f: f'{i}, {f}')),
            ),
            inj.bind(421),
            inj.bind(5.2),
        ),
    )
    assert i.provide(int) == 421
    assert i.provide(float) == 5.2
    assert i.provide(str) == '421, 5.2'
