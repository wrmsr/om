import contextlib

import pytest

from ... import inject as inj
from ... import lang
from ..impl.plans import compile_provision_plan


##


async def _interpret(injector, key, binding, provide):
    return await provide()


@pytest.mark.parametrize('interpreted', [False, True])
def test_static_cycle_path(interpreted):
    a, b, c = [inj.as_key(int, tag=t) for t in ('a', 'b', 'c')]
    elements = inj.collect_elements(inj.as_elements(
        inj.bind(a, to_key=b),
        inj.bind(b, to_key=c),
        inj.bind(c, to_key=a),
        *([inj.bind_provision_listener(_interpret)] if interpreted else []),
    ))

    with pytest.raises(inj.CyclicDependencyError) as ei:
        inj.create_injector(elements)[a]

    error = ei.value
    assert error.key == a
    assert error.chain == (a, b, c, a)
    assert error.wait_chain is None
    assert '\n  -> '.join(map(repr, error.chain)) in str(error)

    with pytest.raises(inj.CyclicDependencyError) as ei:
        compile_provision_plan(elements, a)
    assert ei.value.chain == (a, b, c, a)


@pytest.mark.parametrize('interpreted', [False, True])
@pytest.mark.parametrize('scoped', [False, True])
def test_reentrant_self_cycle_path(interpreted, scoped):
    def make(i: inj.Injector) -> int:
        return i[int]

    injector = inj.create_injector(
        inj.bind(make, singleton=scoped),
        *([inj.bind_provision_listener(_interpret)] if interpreted else []),
    )
    with pytest.raises(inj.CyclicDependencyError) as ei:
        injector[int]
    assert ei.value.chain == (inj.as_key(int), inj.as_key(int))


@pytest.mark.parametrize('interpreted', [False, True])
@pytest.mark.parametrize('delimited', [False, True])
def test_export_provider_cycle_path(interpreted, delimited):
    # A compiled export crosses an async provider into an app dependency chain that needs the export again.
    # Its intermediate nodes must appear even though they never pass through the interpreter's key guard.
    agent, exports, quit_signal, app, renderer, paths = [
        inj.as_key(object, tag=t)
        for t in ('Agent', 'Exports', 'QuitSignal', 'App', 'Renderer', 'Paths')
    ]
    scope = inj.DelimitedScope('errors') if delimited else inj.Singleton()

    async def make_exports(injector):
        await injector[quit_signal]
        return object()

    async def run():
        injector = await inj.create_asyncio_injector(
            *([inj.bind_scope(scope)] if delimited else []),
            inj.bind(agent, in_=scope, to_fn=inj.target(x=exports)(lambda x: x)),
            inj.bind(exports, singleton=True, to_async_fn=inj.target(injector=inj.AsyncInjector)(make_exports)),
            inj.bind(quit_signal, to_key=app),
            inj.bind(app, singleton=True, to_fn=inj.target(x=renderer)(lambda x: x)),
            inj.bind(renderer, to_fn=inj.target(x=paths)(lambda x: x)),
            inj.bind(paths, singleton=True, to_fn=inj.target(x=agent)(lambda x: x)),
            *([inj.bind_provision_listener(_interpret)] if interpreted else []),
        )

        if isinstance(scope, inj.DelimitedScope):
            async with inj.async_enter_scope(injector, scope):
                await injector[agent]
        else:
            await injector[agent]

    # This graph never suspends: it can be driven synchronously even with asyncio concurrency identities.
    with pytest.raises(inj.CyclicDependencyError) as ei:
        lang.sync_await(run())
    error = ei.value
    assert error.chain == (agent, exports, quit_signal, app, renderer, paths, agent)
    if not interpreted:
        assert error.wait_chain == (agent,)
        assert 'Waiting for own in-progress provision:' in str(error)


def test_cross_injector_cycle_path():
    # Exception enrichment follows the actual call path, even when a provider re-enters an older request frame.
    def outer(i: inj.Injector) -> int:
        return int(inj.create_injector(inj.bind(str, to_fn=lambda: str(i[int])))[str])

    with pytest.raises(inj.CyclicDependencyError) as ei:
        inj.create_injector(inj.bind(outer))[int]
    assert ei.value.chain == tuple(map(inj.as_key, (int, str, int)))


def test_cycle_message_without_path():
    key = inj.as_key(int)
    assert str(inj.CyclicDependencyError(key)) == f'Cyclic dependency: {key!r}'


##


@pytest.mark.parametrize('interpreted', [False, True])
@pytest.mark.parametrize('scope', [inj.Unscoped(), inj.Singleton(), inj.ThreadScope(), inj.DelimitedScope('unbound')])
@pytest.mark.parametrize('entrypoint', ['provide', 'try_provide', 'plan'])
def test_unbound_dependency_path(interpreted, scope, entrypoint):
    missing = inj.as_key(float, tag='missing')
    elements = inj.collect_elements(inj.as_elements(
        *([inj.bind_scope(scope)] if isinstance(scope, inj.DelimitedScope) else []),
        inj.bind(420),
        inj.bind(tuple, to_fn=inj.target(first=int, second=str)(lambda first, second: (first, second))),
        inj.bind(str, to_key=missing, in_=scope),
        *([inj.bind_provision_listener(_interpret)] if interpreted else []),
    ))
    injector = inj.create_injector(elements)

    def provide():
        if entrypoint == 'plan':
            return lang.sync_await(compile_provision_plan(elements, tuple).provide(injector))
        return getattr(injector, entrypoint)(tuple)

    with inj.enter_scope(injector, scope) if isinstance(scope, inj.DelimitedScope) else contextlib.nullcontext():
        with pytest.raises(inj.UnboundKeyError) as ei:
            provide()

    error = ei.value
    assert error.key == missing
    assert error.chain == (inj.as_key(tuple), inj.as_key(str), missing)
    assert '\n  -> '.join(map(repr, error.chain)) in str(error)


@pytest.mark.parametrize('use_async', [False, True])
def test_unbound_root_path(use_async):
    injector = inj.create_injector(inj.as_elements())
    if use_async:
        ai = injector[inj.AsyncInjector]
        assert not lang.sync_await(ai.try_provide(int)).present
        with pytest.raises(inj.UnboundKeyError) as ei:
            lang.sync_await(ai.provide(int))
    else:
        assert not injector.try_provide(int).present
        with pytest.raises(inj.UnboundKeyError) as ei:
            injector[int]

    assert ei.value.key == inj.as_key(int)
    assert ei.value.chain == (inj.as_key(int),)


@pytest.mark.parametrize('interpreted', [False, True])
def test_unbound_async_provider_path(interpreted):
    async def make(f: float) -> str:
        return str(f)

    async def run():
        injector = await inj.create_asyncio_injector(
            inj.bind(tuple, to_fn=inj.target(x=str)(lambda x: (x,)), singleton=True),
            inj.bind(make),
            *([inj.bind_provision_listener(_interpret)] if interpreted else []),
        )
        await injector[tuple]

    with pytest.raises(inj.UnboundKeyError) as ei:
        lang.sync_await(run())
    assert ei.value.chain == tuple(map(inj.as_key, (tuple, str, float)))


@pytest.mark.parametrize('interpreted', [False, True])
def test_unbound_optional_dependency_path(interpreted):
    def make(s: str = 'default') -> tuple:
        return (s,)

    listeners = [inj.bind_provision_listener(_interpret)] if interpreted else []
    assert inj.create_injector(inj.bind(make), *listeners)[tuple] == ('default',)

    # A bound optional dependency that itself lacks a dependency must fail, rather than using the default.
    parent = inj.create_injector(inj.bind(str, to_key=float), *listeners)
    child = inj.create_injector(inj.bind(make), parent=parent)
    with pytest.raises(inj.UnboundKeyError) as ei:
        child[tuple]
    # str appears once for the child lookup and once for its provision in the parent.
    assert ei.value.chain == tuple(map(inj.as_key, (tuple, str, str, float)))


@pytest.mark.parametrize('interpreted', [False, True])
def test_unbound_inject_path(interpreted):
    def make(s: str) -> tuple:
        return (s,)

    injector = inj.create_injector(
        inj.bind(str, to_key=float),
        *([inj.bind_provision_listener(_interpret)] if interpreted else []),
    )
    with pytest.raises(inj.UnboundKeyError) as ei:
        injector.inject(make)
    # An injected callable need not have a binding; only its provisioned arguments have keys.
    assert ei.value.chain == tuple(map(inj.as_key, (str, float)))


def test_unbound_cross_injector_path():
    def make() -> int:
        return int(inj.create_injector(inj.bind(str, to_key=float))[str])

    with pytest.raises(inj.UnboundKeyError) as ei:
        inj.create_injector(inj.bind(make))[int]
    assert ei.value.chain == tuple(map(inj.as_key, (int, str, float)))


def test_unbound_eager_key_path():
    with pytest.raises(inj.UnboundKeyError) as ei:
        inj.create_injector(inj.Eager(inj.as_key(int)))
    assert ei.value.chain == (inj.as_key(int),)


def test_unbound_message_without_path():
    key = inj.as_key(int)
    assert str(inj.UnboundKeyError(key)) == f'Unbound key: {key!r}'
