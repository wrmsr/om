"""
An executable tutorial for `omcore.inject`, in pytest form. Parts progress from the basics through the full feature
set, demonstrating idiomatic usage and known rough edges along the way - later parts assume familiarity with earlier
ones. Where a topic has deeper dedicated coverage (concurrency, overrides, multis, ...) the relevant test module is
called out.
"""
import abc
import contextlib
import functools
import threading
import typing as ta

import pytest

from ... import dataclasses as dc
from ... import inject as inj
from ... import lang


##
# Part 1: The basics.
#
# An injector is created from *elements* - most commonly bindings, produced by `inj.bind`. Values are then requested
# from it by *key* - most commonly just a type. Binding a plain instance binds it as a constant under its own type.


def test_the_basics():
    i = inj.create_injector(
        inj.bind(420),
        inj.bind('four twenty'),
    )

    assert i.provide(int) == 420
    assert i.provide(str) == 'four twenty'

    # `__getitem__` is sugar for `provide`:
    assert i[int] == 420


def test_unbound_keys():
    i = inj.create_injector(inj.bind(420))

    # `provide` raises on unbound keys - `try_provide` returns a `lang.Maybe` instead:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(str)
    assert not i.try_provide(str).present
    assert i.try_provide(int).must() == 420


##
# Part 2: Binding classes and functions.
#
# Binding a *type* binds it to its own constructor, with parameters provided by annotation. Binding a *function* binds
# its return annotation as the key. Anything callable-but-annotationless (lambdas) can be adapted via
# `lang.typed_lambda` or `inj.target`.


def test_class_binding():
    class Greeter:
        def __init__(self, greeting: str) -> None:
            self.greeting = greeting

        def greet(self, name):
            return f'{self.greeting}, {name}!'

    i = inj.create_injector(
        inj.bind('hello'),
        inj.bind(Greeter),
    )

    assert i[Greeter].greet('world') == 'hello, world!'

    # Bindings are *unscoped* by default: every provision constructs afresh. See Part 5 for scopes.
    assert i[Greeter] is not i[Greeter]


def test_function_binding():
    def render(n: int) -> str:
        return f'#{n}'

    i = inj.create_injector(
        inj.bind(420),
        inj.bind(render),
    )
    assert i[str] == '#420'


def test_lambda_binding():
    # Lambdas can't carry annotations - `lang.typed_lambda` wraps one in an annotated signature:
    i = inj.create_injector(
        inj.bind(420),
        inj.bind(lang.typed_lambda(str, n=int)(lambda n: f'#{n}')),
    )
    assert i[str] == '#420'


def test_partial_binding():
    # `functools.partial` is function-like, and its un-applied signature is what gets injected:
    def repeat(s: str, n: int) -> list:
        return [s] * n

    i = inj.create_injector(
        inj.bind(3),
        inj.bind(functools.partial(repeat, 'yo')),
    )
    assert i[list] == ['yo', 'yo', 'yo']


def test_defaulted_parameters():
    # A parameter with a default is attempted: injected when its key is bound, defaulted when not. Note that this
    # applies per-parameter - constructors remain fully usable by hand.
    @dc.dataclass(frozen=True)
    class ServerConfig:
        port: int
        host: str = 'localhost'

    assert inj.create_injector(inj.bind(8080), inj.bind(ServerConfig))[ServerConfig] == ServerConfig(8080)
    assert inj.create_injector(
        inj.bind(8080),
        inj.bind('example.com'),
        inj.bind(ServerConfig),
    )[ServerConfig] == ServerConfig(8080, 'example.com')


def test_optional_annotations():
    # `X | None` annotations are stripped to `X` for key purposes - pair with a `= None` default for the common
    # 'optional collaborator' pattern:
    def describe(n: int, f: float | None = None) -> str:
        return f'{n=} {f=}'

    es = inj.as_elements(
        inj.bind(420),
        inj.bind(describe),
    )
    assert inj.create_injector(es)[str] == 'n=420 f=None'
    assert inj.create_injector(inj.bind(4.2), es)[str] == 'n=420 f=4.2'


##
# Part 3: Keys, tags, and NewTypes.
#
# A key is a reflected type plus an optional *tag*. Tags disambiguate multiple bindings of one type;
# `ta.NewType` gives a value a domain name of its own - often the better choice for singular values.


def test_tags():
    i = inj.create_injector(
        inj.bind(8080, tag='http'),
        inj.bind(8443, tag='https'),
    )

    assert i[inj.as_key(int, tag='http')] == 8080
    assert i[inj.as_key(int, tag='https')] == 8443

    # The untagged key is its own, distinct key:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(int)


def test_tagged_parameters():
    # Parameters pick up tags via `ta.Annotated` metadata...
    def connect(host: str, port: ta.Annotated[int, inj.Tag('http')]) -> tuple:
        return (host, port)

    i = inj.create_injector(
        inj.bind('localhost'),
        inj.bind(80, tag='http'),
        inj.bind(connect),
    )
    assert i[tuple] == ('localhost', 80)


def test_externally_tagged_parameters():
    # ...or externally via `inj.tag`, keeping the signature clean for by-hand use:
    def connect(host: str, port: int) -> tuple:
        return (host, port)

    inj.tag(connect, port='http')

    i = inj.create_injector(
        inj.bind('localhost'),
        inj.bind(80, tag='http'),
        inj.bind(connect),
    )
    assert i[tuple] == ('localhost', 80)


DbUrl = ta.NewType('DbUrl', str)


def test_newtype_keys():
    i = inj.create_injector(inj.bind(DbUrl, to_const=DbUrl('postgres://prod')))

    assert i[DbUrl] == 'postgres://prod'

    # The NewType key is fully distinct from its base type:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(str)


def test_generic_keys():
    # Keys can be any reflectable type, including generic aliases:
    i = inj.create_injector(inj.bind(ta.Sequence[int], to_const=[1, 2, 3]))
    assert i[ta.Sequence[int]] == [1, 2, 3]


##
# Part 4: Interfaces and implementations.
#
# The house pattern: bind the impl, then *link* the interface to it with `to_key`. Consumers depend on the interface
# key; tests and alternate assemblies rebind the link. Keys are nominal - subclassing alone binds nothing.


class Storage(lang.Abstract):
    @abc.abstractmethod
    def save(self, v) -> None:
        raise NotImplementedError


class MemoryStorage(Storage):
    def __init__(self) -> None:
        super().__init__()

        self.saved: list = []

    def save(self, v) -> None:
        self.saved.append(v)


def test_interface_impl_link():
    i = inj.create_injector(
        inj.bind(MemoryStorage, singleton=True),
        inj.bind(Storage, to_key=MemoryStorage),
    )

    s = i[Storage]
    assert isinstance(s, MemoryStorage)

    # The link points at the impl's binding, sharing its scope:
    assert s is i[MemoryStorage]


def test_nominal_keys():
    # Keys are nominal, not structural - bool does not satisfy int, despite being a subclass:
    i = inj.create_injector(
        inj.bind(420),
        inj.bind(True),  # noqa
    )
    assert i[int] == 420
    assert i[bool] is True


##
# Part 5: Scopes.
#
# Unscoped (the default) constructs per provision. `singleton=True` caches on first provision; `eager=True`
# additionally constructs it at injector creation (failing fast on broken graphs). See test_scopes.py and Part 14 for
# seeded scopes, and test_concurrency.py for concurrent scope semantics.


def test_singletons():
    class Service:
        pass

    i = inj.create_injector(inj.bind(Service, singleton=True))
    assert i[Service] is i[Service]


def test_eager_singletons():
    created = []

    class Warmup:
        def __init__(self) -> None:
            created.append(self)

    i = inj.create_injector(inj.bind(Warmup, singleton=True, eager=True))

    assert len(created) == 1  # constructed by creation itself
    assert i[Warmup] is created[0]


def test_thread_scope():
    class Conn:
        pass

    i = inj.create_injector(inj.bind(Conn, in_=inj.ThreadScope()))

    c = i[Conn]
    assert i[Conn] is c

    other: list = []
    t = threading.Thread(target=lambda: other.append(i[Conn]))
    t.start()
    t.join()
    assert other[0] is not c


def test_eager_needs_an_instantiation_point():
    # Rough edge, by design: eagerness requires a scope with a defined instantiation point (injector init for
    # unscoped/singleton, scope open for seeded scopes). ThreadScope has none - there is no 'when' - so it is rejected
    # loudly at creation:
    class Conn:
        pass

    with pytest.raises(inj.ScopeEagerUnsupportedError):
        inj.create_injector(inj.bind(Conn, in_=inj.ThreadScope(), eager=True))


##
# Part 6: The injector in the graph.
#
# Provisions are memoized per *request* (one top-level `provide` call): a diamond dependency sees a single shared
# instance even unscoped. The injector itself is injectable - useful for adapters, though domain code should almost
# never touch it.


class DiamondLeaf:
    pass


class DiamondLeft:
    def __init__(self, leaf: DiamondLeaf) -> None:
        self.leaf = leaf


class DiamondRight:
    def __init__(self, leaf: DiamondLeaf) -> None:
        self.leaf = leaf


class DiamondRoot:
    def __init__(self, left: DiamondLeft, right: DiamondRight) -> None:
        self.left = left
        self.right = right


def test_request_memoization():
    i = inj.create_injector(
        inj.bind(DiamondLeaf),
        inj.bind(DiamondLeft),
        inj.bind(DiamondRight),
        inj.bind(DiamondRoot),
    )

    root = i[DiamondRoot]
    assert root.left.leaf is root.right.leaf

    # ...but a new request starts fresh:
    assert i[DiamondRoot].left.leaf is not root.left.leaf


def test_injector_injectable():
    class Locator:
        def __init__(self, i: inj.Injector) -> None:
            self.i = i

    i = inj.create_injector(inj.bind(420), inj.bind(Locator))
    assert i[Locator].i is i
    assert i[Locator].i[int] == 420


def test_injecting_a_call():
    # `inject` calls an arbitrary annotated callable with provided kwargs; `provide_kwargs` returns them:
    def fn(n: int, s: str) -> tuple:
        return (n, s)

    i = inj.create_injector(inj.bind(420), inj.bind('yo'))
    assert i.inject(fn) == (420, 'yo')
    assert i.provide_kwargs(inj.build_kwargs_target(fn)) == {'n': 420, 's': 'yo'}


def test_jit_injection():
    # `inject` also constructs classes that were never bound at all - keyword-only parameters included:
    class Server:
        def __init__(self, *, port: int) -> None:
            self.port = port

    i = inj.create_injector(inj.bind(8080))
    assert i.inject(Server).port == 8080


def test_non_strict_kwargs():
    # `build_kwargs_target(fn, non_strict=True)` reflects only what it can - unannotated parameters are skipped
    # rather than rejected. With `provide_kwargs` this gives partial-fill: inject what the graph knows, hand-complete
    # the rest.
    def fn(n: int, mystery=None, s: str = 'd') -> tuple:
        return (n, mystery, s)

    i = inj.create_injector(inj.bind(420))
    kw = i.provide_kwargs(inj.build_kwargs_target(fn, non_strict=True))
    assert kw == {'n': 420}
    assert fn(**kw, mystery='!') == (420, '!', 'd')


##
# Part 7: Composition.
#
# `as_elements` composes element sets - the house idiom is per-package `bind_*()` functions returning `inj.Elements`,
# with parents composing children. Exactly-duplicate bindings squash; genuinely conflicting ones are a hard error -
# there is deliberately no silent last-wins (that's what overrides are for).


def test_binder_function_composition():
    @dc.dataclass(frozen=True)
    class AppConfig:
        greeting: str = 'hello'
        shout: bool = False

    def bind_app(cfg: AppConfig = AppConfig()) -> inj.Elements:
        els: list[inj.Elemental] = [
            inj.bind(cfg.greeting, tag='greeting'),
        ]

        # Note `inj.target`, not `lang.typed_lambda`: typed_lambda annotates with *types*, while target takes full
        # keys - needed here since the dependency is tagged.
        if cfg.shout:
            els.append(inj.bind(
                str,
                to_fn=inj.target(g=inj.as_key(str, tag='greeting'))(lambda g: g.upper() + '!'),
            ))
        else:
            els.append(inj.bind(str, to_key=inj.as_key(str, tag='greeting')))

        return inj.as_elements(*els)

    assert inj.create_injector(bind_app())[str] == 'hello'
    assert inj.create_injector(bind_app(AppConfig(shout=True)))[str] == 'HELLO!'


def test_duplicates_squash_conflicts_raise():
    es = inj.as_elements(inj.bind(420))

    # The same binding appearing twice (eg. via two modules composing a shared third) is fine:
    assert inj.create_injector(es, es)[int] == 420

    # Two *different* bindings for one key are not:
    with pytest.raises(inj.ConflictingKeyError):
        inj.create_injector(es, inj.bind(421))


##
# Part 8: Overrides.
#
# `inj.override(src, *ovr)` rebinds matching keys within an element set - the canonical use being a test (or a
# specializing frontend) substituting a real-but-simple implementation. Overrides operate on *keys*: the override's
# elements for a key replace the source's wholesale, while additive intent is expressed by composing *outside* the
# override. See test_overrides.py for the full semantics (multis, eagers, non-keyed elements).


class Database:
    def __init__(self, url: DbUrl) -> None:
        self.url = url


def test_override_for_testing():
    def bind_app() -> inj.Elements:
        return inj.as_elements(
            inj.bind(DbUrl, to_const=DbUrl('postgres://prod')),
            inj.bind(Database, singleton=True),
        )

    assert inj.create_injector(bind_app())[Database].url == 'postgres://prod'

    i = inj.create_injector(inj.override(
        bind_app(),
        inj.bind(DbUrl, to_const=DbUrl('sqlite://:memory:')),
    ))
    assert i[Database].url == 'sqlite://:memory:'


##
# Part 9: Multibindings.
#
# Set and map binders let many element sets contribute entries to one shared collection - the backbone of registry
# and plugin patterns. See test_multis.py, and the items-binder helper in test_helpers.py / helpers/multis.py for the
# higher-level 'contributed items' pattern.


class Command(lang.Abstract):
    @abc.abstractmethod
    def run(self) -> str:
        raise NotImplementedError


class HelloCommand(Command):
    def run(self) -> str:
        return 'hi!'


class VersionCommand(Command):
    def run(self) -> str:
        return '4.20'


def test_map_multibinding_registry():
    def bind_command(name, cmd_cls) -> inj.Elements:
        return inj.as_elements(
            inj.bind(Command, tag=name, to_ctor=cmd_cls),
            inj.map_binder[str, Command]().bind(name, inj.as_key(Command, tag=name)),
        )

    i = inj.create_injector(
        bind_command('hello', HelloCommand),
        bind_command('version', VersionCommand),
    )

    commands = i[ta.Mapping[str, Command]]
    assert commands['hello'].run() == 'hi!'
    assert commands['version'].run() == '4.20'


##
# Part 10: Private element sets.
#
# `inj.private` wires its elements in an isolated child injector, `expose=True` selectively publishing keys back to
# the owner. Internal keys - even ones identical across two privates - never collide or leak.


def test_private_wiring():
    i = inj.create_injector(
        inj.private(
            inj.bind(DbUrl, to_const=DbUrl('postgres://main')),
            inj.bind(Database, tag='main', expose=True),
        ),
        inj.private(
            inj.bind(DbUrl, to_const=DbUrl('postgres://replica')),
            inj.bind(Database, tag='replica', expose=True),
        ),
    )

    assert i[inj.as_key(Database, tag='main')].url == 'postgres://main'
    assert i[inj.as_key(Database, tag='replica')].url == 'postgres://replica'

    # Each private's DbUrl stays private:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(DbUrl)


##
# Part 11: Wrapper stacks.
#
# For decorator-composed implementations, build the stack in the binder - bottom-to-top, optionally conditionally -
# and bind the interface to the top. Each layer's class simply takes the interface as a constructor arg; the helper
# privately rebinds it per-level. See test_wrappers.py.


class Renderer(lang.Abstract):
    @abc.abstractmethod
    def render(self) -> str:
        raise NotImplementedError


class TextRenderer(Renderer):
    def render(self) -> str:
        return 'hi'


class BoldRenderer(Renderer):
    def __init__(self, wrapped: Renderer) -> None:
        super().__init__()

        self.wrapped = wrapped

    def render(self) -> str:
        return f'<b>{self.wrapped.render()}</b>'


class HeaderRenderer(Renderer):
    def __init__(self, wrapped: Renderer) -> None:
        super().__init__()

        self.wrapped = wrapped

    def render(self) -> str:
        return f'<h1>{self.wrapped.render()}</h1>'


def test_wrapper_stack():
    def build(*, bold):
        stack = inj.wrapper_binder_helper(Renderer)

        els: list[inj.Elemental] = [stack.push_bind(to_ctor=TextRenderer)]
        if bold:
            els.append(stack.push_bind(to_ctor=BoldRenderer))
        els.append(stack.push_bind(to_ctor=HeaderRenderer))
        els.append(inj.bind(Renderer, to_key=stack.top))

        return inj.create_injector(*els)

    assert build(bold=True)[Renderer].render() == '<h1><b>hi</b></h1>'
    assert build(bold=False)[Renderer].render() == '<h1>hi</h1>'


##
# Part 12: Cycles, and breaking them with Late.
#
# Construction cycles are detected and rejected. The sanctioned fix is `Late[T]` - a no-arg callable resolving T from
# the injector on first call - bound via `inj.bind_late` (or `bind_async_late`), keeping laziness at the *dependency*
# level rather than contorting constructors. See test_late.py for named-getter variants.


class Chicken:
    def __init__(self, egg: Egg) -> None:
        self.egg = egg


class Egg:
    def __init__(self, chicken: Chicken) -> None:
        self.chicken = chicken


def test_cycles_are_rejected():
    i = inj.create_injector(
        inj.bind(Chicken, singleton=True),
        inj.bind(Egg, singleton=True),
    )
    with pytest.raises(inj.CyclicDependencyError):
        i.provide(Chicken)


class LateEgg:
    def __init__(self, chicken: inj.Late[LateChicken]) -> None:
        self._chicken = chicken

    @property
    def chicken(self) -> LateChicken:
        return self._chicken()


class LateChicken:
    def __init__(self, egg: LateEgg) -> None:
        self.egg = egg


def test_late_breaks_cycles():
    i = inj.create_injector(
        inj.bind(LateChicken, singleton=True),
        inj.bind(LateEgg, singleton=True),
        inj.bind_late(LateChicken),
    )

    chicken = i[LateChicken]
    assert chicken.egg.chicken is chicken


##
# Part 13: Managed lifecycles.
#
# `create_managed_injector` scopes the injector to a context manager, binding an `ExitStack` for provider functions
# to register cleanup on. `make_managed_provider` adapts a context-managed (or closeable) class into such a provider.
# See test_managed.py, including the async variants.


class Connection:
    def __init__(self, url: DbUrl) -> None:
        self.url = url
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_managed_lifecycle():
    with inj.create_managed_injector(
        inj.bind(DbUrl, to_const=DbUrl('postgres://prod')),
        inj.bind(Connection, singleton=True, to_fn=inj.make_managed_provider(Connection, contextlib.closing)),
    ) as i:
        conn = i[Connection]
        assert conn.url == 'postgres://prod'
        assert not conn.closed

    assert conn.closed


##
# Part 14: Seeded scopes.
#
# A `SeededScope` is opened per unit-of-work (request, session, job), *seeded* with the values that define that unit.
# Bindings `in_` the scope construct at most once per opening; seed keys are declared with `bind_scope_seed` and
# provided at entry. See test_scopes.py for scope-open eagers, and test_concurrency.py for concurrent semantics.


REQUEST_SCOPE = inj.SeededScope('web-request')


@dc.dataclass(frozen=True)
class WebRequest:
    path: str


class WebHandler:
    def __init__(self, request: WebRequest, db: Database) -> None:
        self.request = request
        self.db = db

    def handle(self) -> str:
        return f'{self.request.path} @ {self.db.url}'


def test_request_scope():
    i = inj.create_injector(
        inj.bind(DbUrl, to_const=DbUrl('postgres://prod')),
        inj.bind(Database, singleton=True),

        inj.bind_scope(REQUEST_SCOPE),
        inj.bind_scope_seed(WebRequest, REQUEST_SCOPE),
        inj.bind(WebHandler, in_=REQUEST_SCOPE),
    )

    # Scoped bindings are only available while the scope is open:
    with pytest.raises(inj.ScopeNotOpenError):
        i.provide(WebHandler)

    with inj.enter_seeded_scope(i, REQUEST_SCOPE, {inj.as_key(WebRequest): WebRequest('/a')}):
        h = i[WebHandler]
        assert h.handle() == '/a @ postgres://prod'
        assert i[WebHandler] is h  # one per scope opening

    with inj.enter_seeded_scope(i, REQUEST_SCOPE, {inj.as_key(WebRequest): WebRequest('/b')}):
        h2 = i[WebHandler]
        assert h2 is not h  # each opening starts fresh
        assert h2.handle() == '/b @ postgres://prod'
        assert h2.db is h.db  # while singletons span openings


##
# Part 15: Async.
#
# The real injector is async-native - the sync one is a facade over it. `create_async_injector` awaits provisions,
# async provider functions bind just like sync ones, and everything above translates directly. See test_managed.py
# and test_concurrency.py for deeper async coverage.


def test_async_injector():
    async def render(n: int) -> str:
        return f'#{n}'

    i = lang.sync_await(inj.create_async_injector(
        inj.bind(420),
        inj.bind(render),
    ))

    assert lang.sync_await(i.provide(str)) == '#420'


##
# Part 16: Assorted rough edges.
#
# Honest gotchas, codified so they stay known.


def test_gotcha_newtype_erasure():
    # NewTypes erase at runtime: binding an *instance* of one binds the base type, silently. Bind NewType keys
    # explicitly (`inj.bind(DbUrl, to_const=...)`, per Part 3).
    i = inj.create_injector(inj.bind(DbUrl('oops')))

    assert i[str] == 'oops'
    with pytest.raises(inj.UnboundKeyError):
        i.provide(DbUrl)


def test_gotcha_instances_bind_their_concrete_type():
    # Similarly, binding an impl instance binds the *impl* key, not the interface - link or bind explicitly:
    i = inj.create_injector(inj.bind(MemoryStorage()))
    with pytest.raises(inj.UnboundKeyError):
        i.provide(Storage)

    i = inj.create_injector(inj.bind(Storage, to_const=MemoryStorage()))
    assert isinstance(i[Storage], MemoryStorage)


def test_gotcha_provision_listeners_transform():
    # Provision listeners wrap every provision - including scope-cached ones - and their return value *replaces* the
    # provided value. Powerful for instrumentation; easy to abuse. See test_listeners.py.
    async def exclaim(injector, key, binding, fn):
        v = await fn()
        return v + '!' if isinstance(v, str) else v

    i = inj.create_injector(
        inj.bind('hi'),
        inj.bind_provision_listener(exclaim),
    )
    assert i[str] == 'hi!'
