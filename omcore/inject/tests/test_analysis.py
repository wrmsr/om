import typing as ta

from ... import inject as inj


FooStr = ta.NewType('FooStr', str)


def test_analyze():
    def foo(s: str, i: int) -> FooStr:
        return FooStr(f'foo: {s=} {i=}')

    els = inj.as_elements(
        inj.bind(str, to_const='hi!'),
        inj.bind(int, to_const=420),
        # inj.bind(int, to_const=421),
        inj.bind(FooStr, to_fn=foo, singleton=True),
    )

    i = inj.create_injector(els)
    assert i[str] == 'hi!'
    assert i[int] == 420
    assert i[FooStr] == FooStr("foo: s='hi!' i=420")

    ana = els.analyze()
    assert ana.known_dependencies_by_key() == {
        inj.as_key(int): None,
        inj.as_key(str): None,
        inj.as_key(FooStr): frozenset([inj.as_key(int), inj.as_key(str)]),
    }
