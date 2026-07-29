import pytest

from ... import inject as inj
from ..impl.injector import AsyncInjectorImpl
from ..impl.scopes import SeededScopeImpl


def test_dupe_scope_bindings():
    ss = inj.SeededScope('hi')
    i = inj.create_injector(
        inj.as_elements(
            inj.bind_scope(ss),
            inj.bind(420, in_=ss),
        ),
        inj.as_elements(
            inj.bind_scope(ss),
            inj.bind('four twenty', in_=ss),
        ),
    )
    with inj.enter_seeded_scope(i, ss, {}):
        assert i[int] == 420
        assert i[str] == 'four twenty'


def test_scopes():
    ss = inj.SeededScope('hi')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind(420, in_=ss),
        inj.bind_scope_seed(float, ss),
    )
    with inj.enter_seeded_scope(i, ss, {
        inj.as_key(float): 4.2,
    }):
        assert i[int] == 420
        assert i[float] == 4.2


def _freeze_scope(i, ss):
    # Freezing is (currently, deliberately) impl-level api:
    ai = i[inj.AsyncInjector]
    assert isinstance(ai, AsyncInjectorImpl)
    ssi = ai.get_scope_impl(ss)
    assert isinstance(ssi, SeededScopeImpl)
    ssi.freeze()


def test_seeded_scope_freeze():
    ss = inj.SeededScope('freezer')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(420, tag='a', in_=ss),
        inj.bind(421, tag='b', in_=ss),
    )

    with inj.enter_seeded_scope(i, ss, {inj.as_key(float): 4.2}):
        assert i[inj.as_key(int, tag='a')] == 420

        _freeze_scope(i, ss)

        # Provisions made before the freeze keep serving, as do seeds - but new construction is rejected:
        assert i[inj.as_key(int, tag='a')] == 420
        assert i[float] == 4.2
        with pytest.raises(inj.ScopeFrozenError):
            i.provide(inj.as_key(int, tag='b'))

    # The next opening starts fresh and unfrozen:
    with inj.enter_seeded_scope(i, ss, {inj.as_key(float): 5.3}):
        assert i[inj.as_key(int, tag='b')] == 421

    # Freezing requires an open scope:
    with pytest.raises(inj.ScopeNotOpenError):
        _freeze_scope(i, ss)


def test_seeded_eager():
    c = 0

    def foo(i: int) -> str:
        nonlocal c
        c += 1
        return f'foo: {c} {i}'

    ss = inj.SeededScope('hi')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind(420, in_=ss),
        inj.bind(foo, in_=ss, eager=True),
        inj.bind_scope_seed(float, ss),
    )
    assert c == 0
    with inj.enter_seeded_scope(i, ss, {
        inj.as_key(float): 4.2,
    }):
        assert c == 1
        assert i[int] == 420
        assert i[float] == 4.2
        assert i[str] == 'foo: 1 420'
