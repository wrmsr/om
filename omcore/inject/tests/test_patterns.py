"""
Integration tests codifying real-world composition patterns from the injector's heavier users (the minichain driver,
the app/server experiments, and the iceworm engine's phased-scope architecture, translated to the current injector).
Each test is a miniature of a pattern that has seen production-ish use - if one of these breaks, an idiom broke.
"""
import abc
import contextlib
import contextvars
import typing as ta

import pytest

from ... import dataclasses as dc
from ... import inject as inj
from ... import lang


##
# Pattern: per-package binder functions - config in, elements out.
#
# Applications are assembled from `bind_*()` functions taking (defaulted) frozen config dataclasses, branching on
# them, and composing their children's binders. Impl selection is expressed as different bindings, not branches in
# domain logic; internals of a subsystem hide in a private, exposing only its public interface.


UserName = ta.NewType('UserName', str)


class UserStore(lang.Abstract):
    @abc.abstractmethod
    def get(self, name) -> str:
        raise NotImplementedError


class MemoryUserStore(UserStore):
    def get(self, name) -> str:
        return f'mem:{name}'


class SignerSecret(str):  # noqa
    pass


class Signer:
    def __init__(self, secret: SignerSecret) -> None:
        self.secret = secret


class SignedUserStore(UserStore):
    def __init__(self, signer: Signer) -> None:
        self.signer = signer

    def get(self, name) -> str:
        return f'signed[{self.signer.secret}]:{name}'


@dc.dataclass(frozen=True)
class AppConfig:
    signed: bool = False
    signer_key: str = 'hunter2'


def bind_memory_user_store() -> inj.Elemental:
    return inj.as_elements(
        inj.bind(MemoryUserStore, singleton=True),
        inj.bind(UserStore, to_key=MemoryUserStore),
    )


def bind_signed_user_store(cfg: AppConfig) -> inj.Elemental:
    # The signing machinery is an implementation detail - private, with only the store exposed:
    return inj.private(
        inj.bind(SignerSecret, to_const=SignerSecret(cfg.signer_key)),
        inj.bind(Signer, singleton=True),

        inj.bind(SignedUserStore, singleton=True),
        inj.bind(UserStore, to_key=SignedUserStore, expose=True),
    )


def bind_app(cfg: AppConfig = AppConfig()) -> inj.Elements:
    els: list[inj.Elemental] = []

    if cfg.signed:
        els.append(bind_signed_user_store(cfg))
    else:
        els.append(bind_memory_user_store())

    return inj.as_elements(*els)


def test_config_driven_assembly():
    assert inj.create_injector(bind_app())[UserStore].get('u') == 'mem:u'

    i = inj.create_injector(bind_app(AppConfig(signed=True, signer_key='s3cr3t')))
    assert i[UserStore].get('u') == 'signed[s3cr3t]:u'

    # The private's internals did not leak:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(Signer)


def test_override_specializes_a_stack():
    # A frontend (or test) takes a whole assembled binder and re-points single keys - never editing the source binder:
    i = inj.create_injector(inj.override(
        bind_app(),
        inj.bind(UserStore, to_const=MemoryUserStore()),
    ))
    assert isinstance(i[UserStore], MemoryUserStore)


##
# Pattern: contributed item collections.
#
# The items-binder helper is how packages contribute into an extensible collection (event callbacks, tool catalogs,
# ...): a NewType'd Sequence as the collection's key, one owner binding the provider, any number of contributors
# binding items. Consumers just take the collection type; ordering is registration order; empty is fine.


@dc.dataclass(frozen=True)
class Tool:
    name: str


Tools = ta.NewType('Tools', ta.Sequence[Tool])


@lang.cached_function
def tools() -> inj.ItemsBinderHelper[Tool]:
    return inj.items_binder_helper[Tool](Tools)


class ToolBox:
    def __init__(self, ts: Tools) -> None:
        self.ts = ts


def test_contributed_items():
    i = inj.create_injector(
        tools().bind_items_provider(singleton=True),

        # One 'package' contributes consts, another contributes an injected item:
        tools().bind_item_consts(Tool('read'), Tool('write')),
        tools().bind_item(to_fn=inj.target(s=str)(lambda s: Tool(s)), singleton=True),

        inj.bind('search'),
        inj.bind(ToolBox, singleton=True),
    )

    ts = [t.name for t in i[ToolBox].ts]

    # NOTE - real finding, deliberately pinned loosely: INJECT.md promises 'order is registration order', but the
    # helper collects contribution boxes through a *set* whose iteration order follows id()-based hashes, so
    # cross-contribution order is nondeterministic in practice. Order within one bind_item_consts call does hold.
    assert set(ts) == {'read', 'write', 'search'}
    assert ts.index('read') < ts.index('write')


def test_contributed_items_empty():
    i = inj.create_injector(tools().bind_items_provider(singleton=True))
    assert list(i[Tools]) == []


##
# Pattern: the event-bus cycle, broken with Late.
#
# A bus needs its callbacks at construction; a callback that emits back into the bus needs the bus - a true cycle.
# The house resolution: keep the participant's constructor clean, and resolve it lazily at the *callback* level.


@dc.dataclass(frozen=True)
class EventCallback:
    fn: ta.Callable[[str], None]


class EventBus:
    def __init__(self, callbacks: ta.AbstractSet[EventCallback]) -> None:
        self.callbacks = callbacks
        self.log: list = []

    def emit(self, event) -> None:
        self.log.append(event)
        for cb in self.callbacks:
            cb.fn(event)


class Timeline:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.seen: list = []

    def handle(self, event) -> None:
        self.seen.append(event)
        if event == 'begin':
            self.bus.emit('begun')  # a participant that also emits


def _provide_timeline_callback(late_tl: inj.Late[Timeline]) -> EventCallback:
    return EventCallback(lambda event: late_tl().handle(event))


def test_event_bus_cycle():
    i = inj.create_injector(
        inj.bind(EventBus, singleton=True),
        inj.bind(Timeline, singleton=True),
        inj.bind_late(Timeline),

        inj.bind(EventCallback, tag='timeline', to_fn=_provide_timeline_callback, singleton=True),
        inj.set_binder[EventCallback]().bind(inj.as_key(EventCallback, tag='timeline')),
    )

    bus = i[EventBus]
    bus.emit('begin')

    assert bus.log == ['begin', 'begun']
    assert i[Timeline].seen == ['begin', 'begun']


##
# Pattern: child injectors as instance scopes.
#
# 'N drivers in one app': each unit gets a child injector with its own identity and per-instance services, sharing
# the parent's singletons. Keys bound in the child shadow the parent's; unbound keys fall through. The known caveat:
# contributed items do *not* cross the boundary - a child's collection sees only the child's contributions (and a
# child with no collection of its own falls through to the parent's, wholesale). Data crosses via configs instead.


DriverId = ta.NewType('DriverId', str)


class AppClock:
    pass


class DriverBus:
    def __init__(self, driver_id: DriverId) -> None:
        self.driver_id = driver_id


def bind_one_driver(driver_id, *, extra_tools=()) -> inj.Elements:
    return inj.as_elements(
        inj.bind(DriverId, to_const=DriverId(driver_id)),
        inj.bind(DriverBus, singleton=True),

        # The items caveat's workaround, codified: values that must become items inside the child are carried in as
        # data and contributed by the child's own binder:
        tools().bind_items_provider(singleton=True),
        *([tools().bind_item_consts(*extra_tools)] if extra_tools else []),
    )


def test_child_injectors_per_instance():
    parent = inj.create_injector(
        inj.bind(AppClock, singleton=True),

        tools().bind_items_provider(singleton=True),
        tools().bind_item_consts(Tool('app-tool')),
    )

    a = inj.create_injector(inj.collect_elements(bind_one_driver('a', extra_tools=(Tool('a-tool'),))), parent=parent)
    b = inj.create_injector(inj.collect_elements(bind_one_driver('b')), parent=parent)

    # Per-child identity and services; shared parent singletons:
    assert a[DriverId] == 'a'
    assert b[DriverId] == 'b'
    assert a[DriverBus] is not b[DriverBus]
    assert a[AppClock] is b[AppClock] is parent[AppClock]

    # The parent knows nothing of its children's bindings:
    with pytest.raises(inj.UnboundKeyError):
        parent.provide(DriverBus)

    # Items do not cross the boundary: each child's collection is its own contributions only - the parent's 'app-tool'
    # is invisible to the children's collections, and vice versa:
    assert [t.name for t in a[Tools]] == ['a-tool']
    assert [t.name for t in b[Tools]] == []
    assert [t.name for t in parent[Tools]] == ['app-tool']


##
# Pattern: the phased pipeline (iceworm's architecture, on modern scopes).
#
# A processing engine runs a document through ordered *phases*. Each phase is a SeededScope: opened with the evolving
# document as its seed, hosting phase-scoped caches, per-phase contributed processor sets, and scope-open eagers
# (auditors) - while app singletons span all phases. This is the deepest scope/multis/eager interplay in the suite.


PIPELINE_PHASES = ('parse', 'analyze', 'render')

PHASE_SCOPES: ta.Mapping[str, inj.SeededScope] = {p: inj.SeededScope(('pipeline', p)) for p in PIPELINE_PHASES}


@dc.dataclass(frozen=True)
class PipelineDoc:
    text: str


class PipelineLog:
    def __init__(self) -> None:
        self.entries: list = []


class PhaseCache:
    pass


class PipelineProcessor(lang.Abstract):
    priority = 0

    @abc.abstractmethod
    def process(self, doc: PipelineDoc) -> PipelineDoc:
        raise NotImplementedError


class ParseProcessor(PipelineProcessor):
    def __init__(self, log: PipelineLog) -> None:
        super().__init__()

        self.log = log

    def process(self, doc: PipelineDoc) -> PipelineDoc:
        self.log.entries.append('parse')
        return PipelineDoc(doc.text.strip())


class AnalyzeProcessor(PipelineProcessor):
    def __init__(self, log: PipelineLog, cache: PhaseCache) -> None:
        super().__init__()

        self.log = log
        self.cache = cache

    def process(self, doc: PipelineDoc) -> PipelineDoc:
        self.log.entries.append('analyze')
        return PipelineDoc(f'{doc.text}({len(doc.text)})')


class CheckProcessor(PipelineProcessor):
    priority = -1  # runs before AnalyzeProcessor

    def __init__(self, log: PipelineLog, cache: PhaseCache) -> None:
        super().__init__()

        self.log = log
        self.cache = cache

    def process(self, doc: PipelineDoc) -> PipelineDoc:
        self.log.entries.append('check')
        return doc


class RenderProcessor(PipelineProcessor):
    def __init__(self, log: PipelineLog) -> None:
        super().__init__()

        self.log = log

    def process(self, doc: PipelineDoc) -> PipelineDoc:
        self.log.entries.append('render')
        return PipelineDoc(f'<{doc.text}>')


class PhaseAuditor:
    """Scope-open eager: constructed at phase entry, before any processor runs."""

    def __init__(self, log: PipelineLog, doc: PipelineDoc) -> None:
        self.log = log
        log.entries.append(f'open:{doc.text!r}')


def _phase_processors_key(phase) -> inj.Key:
    return inj.as_key(ta.AbstractSet[PipelineProcessor], tag=('processors', phase))


# Rough edge, codified: a seed key is an ordinary binding referencing one specific scope, so the *same* key cannot be
# seeded into multiple scopes - each phase's doc seed needs its own (tagged) key, and consumers of it are re-pointed
# per-phase via KwargsTarget.override.
def _phase_doc_key(phase) -> inj.Key:
    return inj.as_key(PipelineDoc, tag=('doc', phase))


def bind_pipeline_processor(phase, cls) -> inj.Elements:
    sc = PHASE_SCOPES[phase]
    return inj.as_elements(
        inj.bind(PipelineProcessor, tag=cls, to_ctor=cls, in_=sc),
        inj.set_binder[PipelineProcessor](tag=('processors', phase)).bind(inj.as_key(PipelineProcessor, tag=cls)),
    )


def bind_pipeline() -> inj.Elements:
    els: list[inj.Elemental] = [
        inj.bind(PipelineLog, singleton=True),
    ]

    for phase, sc in PHASE_SCOPES.items():
        els.extend([
            inj.bind_scope(sc),
            inj.bind_scope_seed(_phase_doc_key(phase), sc),
            inj.bind(
                PhaseAuditor,
                tag=phase,
                to_fn=inj.build_kwargs_target(PhaseAuditor).override(doc=_phase_doc_key(phase)),
                in_=sc,
                eager=True,
            ),
            inj.set_binder[PipelineProcessor](tag=('processors', phase)),
        ])

    els.append(inj.bind(PhaseCache, in_=PHASE_SCOPES['analyze']))

    els.extend([
        bind_pipeline_processor('parse', ParseProcessor),
        bind_pipeline_processor('analyze', AnalyzeProcessor),
        bind_pipeline_processor('analyze', CheckProcessor),
        bind_pipeline_processor('render', RenderProcessor),
    ])

    return inj.as_elements(*els)


def run_pipeline(i, doc):
    for phase in PIPELINE_PHASES:
        with inj.enter_seeded_scope(i, PHASE_SCOPES[phase], {_phase_doc_key(phase): doc}):
            for p in sorted(i[_phase_processors_key(phase)], key=lambda p: p.priority):
                doc = p.process(doc)
    return doc


def test_phased_pipeline():
    i = inj.create_injector(bind_pipeline())

    out = run_pipeline(i, PipelineDoc('  hi  '))
    assert out == PipelineDoc('<hi(2)>')

    # Auditors (scope-open eagers) fired at each entry, seeing that phase's seed, before its processors:
    assert i[PipelineLog].entries == [
        "open:'  hi  '", 'parse',
        "open:'hi'", 'check', 'analyze',
        "open:'hi(2)'", 'render',
    ]


def test_phased_pipeline_scoped_state():
    i = inj.create_injector(bind_pipeline())

    caches: list = []

    with inj.enter_seeded_scope(i, PHASE_SCOPES['analyze'], {_phase_doc_key('analyze'): PipelineDoc('x')}):
        ps = sorted(i[_phase_processors_key('analyze')], key=lambda p: p.priority)
        caches.append([p.cache for p in ps])

    with inj.enter_seeded_scope(i, PHASE_SCOPES['analyze'], {_phase_doc_key('analyze'): PipelineDoc('y')}):
        ps = sorted(i[_phase_processors_key('analyze')], key=lambda p: p.priority)
        caches.append([p.cache for p in ps])

    # Within one opening the phase's processors share one cache; across openings everything is fresh:
    assert caches[0][0] is caches[0][1]
    assert caches[1][0] is caches[1][1]
    assert caches[0][0] is not caches[1][0]


##
# Pattern: nested unit-of-work scopes.
#
# Session/turn (or session/query) nesting: an outer seeded scope stays open across many openings of an inner one.
# Inner-scoped services depend on outer-scoped ones and both kinds of seeds; outer state persists across inner units.


SESSION_SCOPE = inj.SeededScope('session')
TURN_SCOPE = inj.SeededScope('turn')

SessionId = ta.NewType('SessionId', str)
TurnInput = ta.NewType('TurnInput', str)


class SessionMemory:
    def __init__(self, session_id: SessionId) -> None:
        self.session_id = session_id
        self.turns: list = []


class TurnHandler:
    def __init__(self, memory: SessionMemory, turn_input: TurnInput) -> None:
        self.memory = memory
        self.turn_input = turn_input

    def handle(self) -> str:
        self.memory.turns.append(self.turn_input)
        return f'{self.memory.session_id}#{len(self.memory.turns)}: {self.turn_input}'


def bind_sessions() -> inj.Elements:
    return inj.as_elements(
        inj.bind_scope(SESSION_SCOPE),
        inj.bind_scope_seed(SessionId, SESSION_SCOPE),
        inj.bind(SessionMemory, in_=SESSION_SCOPE),

        inj.bind_scope(TURN_SCOPE),
        inj.bind_scope_seed(TurnInput, TURN_SCOPE),
        inj.bind(TurnHandler, in_=TURN_SCOPE),
    )


def test_nested_session_turn_scopes():
    i = inj.create_injector(bind_sessions())

    def run_session(session_id, turn_inputs):
        outs = []
        with inj.enter_seeded_scope(i, SESSION_SCOPE, {inj.as_key(SessionId): SessionId(session_id)}):
            for ti in turn_inputs:
                with inj.enter_seeded_scope(i, TURN_SCOPE, {inj.as_key(TurnInput): TurnInput(ti)}):
                    outs.append(i[TurnHandler].handle())
        return outs

    assert run_session('s1', ['hi', 'bye']) == ['s1#1: hi', 's1#2: bye']

    # A new session starts with fresh memory:
    assert run_session('s2', ['yo']) == ['s2#1: yo']


##
# Pattern: keyed executor registries in a work scope (iceworm's op execution).
#
# A map multibinding from op type to executor, with executors constructed *inside* a per-execution seeded scope so
# they see that execution's connections. Providing the map inside the scope builds that execution's executor set.


EXECUTION_SCOPE = inj.SeededScope('execution')


@dc.dataclass(frozen=True)
class ConnectionSet:
    name: str


class Op(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class ListOp(Op):
    pass


@dc.dataclass(frozen=True)
class ExecOp(Op):
    sql: str


class OpExecutor(lang.Abstract):
    @abc.abstractmethod
    def execute(self, op) -> str:
        raise NotImplementedError


class ListExecutor(OpExecutor):
    def __init__(self, conns: ConnectionSet) -> None:
        super().__init__()

        self.conns = conns

    def execute(self, op) -> str:
        return f'list@{self.conns.name}'


class ExecExecutor(OpExecutor):
    def __init__(self, conns: ConnectionSet) -> None:
        super().__init__()

        self.conns = conns

    def execute(self, op) -> str:
        return f'exec({op.sql})@{self.conns.name}'


def bind_op_executor(op_cls, oe_cls) -> inj.Elements:
    return inj.as_elements(
        inj.bind(OpExecutor, tag=op_cls, to_ctor=oe_cls, in_=EXECUTION_SCOPE),
        inj.map_binder[ta.Any, OpExecutor]().bind(op_cls, inj.as_key(OpExecutor, tag=op_cls)),
    )


def test_op_executor_registry():
    i = inj.create_injector(
        inj.bind_scope(EXECUTION_SCOPE),
        inj.bind_scope_seed(ConnectionSet, EXECUTION_SCOPE),

        inj.map_binder[ta.Any, OpExecutor](),
        bind_op_executor(ListOp, ListExecutor),
        bind_op_executor(ExecOp, ExecExecutor),
    )

    def execute_all(conns, ops):
        with inj.enter_seeded_scope(i, EXECUTION_SCOPE, {inj.as_key(ConnectionSet): conns}):
            executors = i[ta.Mapping[ta.Any, OpExecutor]]
            return [executors[type(op)].execute(op) for op in ops]

    assert execute_all(ConnectionSet('prod'), [ListOp(), ExecOp('select 1')]) == [
        'list@prod',
        'exec(select 1)@prod',
    ]
    assert execute_all(ConnectionSet('dev'), [ListOp()]) == ['list@dev']


##
# Pattern: contextvar-thunk request state (the app/server web stack).
#
# Absent a request scope, per-request values live in contextvars, with the *getter* bound as a `Callable[[], T]`
# constant - singleton handlers hold the thunk and call it per request. (A seeded scope is the structured
# alternative; this shape is nonetheless load-bearing in the web stack, and pins generic-alias-with-union keys.)


CURRENT_USER: contextvars.ContextVar[str | None] = contextvars.ContextVar('CURRENT_USER', default=None)


class WhoAmIHandler:
    def __init__(self, current_user: ta.Callable[[], str | None]) -> None:
        self.current_user = current_user

    def handle(self) -> str:
        return f'you are {self.current_user() or "nobody"}'


def test_contextvar_request_state():
    i = inj.create_injector(
        inj.bind(ta.Callable[[], str | None], to_const=CURRENT_USER.get),
        inj.bind(WhoAmIHandler, singleton=True),
    )

    h = i[WhoAmIHandler]
    assert h.handle() == 'you are nobody'

    tok = CURRENT_USER.set('alice')
    try:
        assert h.handle() == 'you are alice'
    finally:
        CURRENT_USER.reset(tok)


##
# Pattern: folding multibindings with a provider function (the route-table fold).
#
# Route tables and middleware chains are folded *outside* the injector: a singleton provider function takes the
# multibindings as parameters, and its (generic alias) return annotation is the folded collection's key.


@dc.dataclass(frozen=True)
class RouteHandler:
    route: str
    body: str


def _build_route_table(handlers: ta.AbstractSet[RouteHandler]) -> ta.Mapping[str, RouteHandler]:
    return {h.route: h for h in handlers}


def test_multibinding_fold():
    i = inj.create_injector(
        inj.set_binder[RouteHandler](),
        inj.bind_set_entry_const(ta.AbstractSet[RouteHandler], RouteHandler('/', 'index')),
        inj.bind_set_entry_const(ta.AbstractSet[RouteHandler], RouteHandler('/about', 'about')),

        inj.bind(_build_route_table, singleton=True),
    )

    table = i[ta.Mapping[str, RouteHandler]]
    assert table['/about'].body == 'about'
    assert i[ta.Mapping[str, RouteHandler]] is table


##
# Pattern: binding a bound method of an injected object.
#
# There is no `to_method` - the shipped workaround (verbatim from the app shell) synthesizes an annotated lambda so
# provider introspection can resolve the owner, then registers the tagged key into the task collection.


ShellTask = ta.NewType('ShellTask', lang.Func0[str])


class AsgiServerTask:
    def run(self) -> str:
        return 'served'


def test_bound_method_binding():
    i = inj.create_injector(
        inj.bind(AsgiServerTask, singleton=True),

        inj.bind(
            ShellTask,
            tag=AsgiServerTask,
            to_fn=lang.typed_lambda(ShellTask, o=AsgiServerTask)(lambda o: ShellTask(lang.Func0(o.run))),
        ),
        inj.set_binder[ShellTask]().bind(inj.as_key(ShellTask, tag=AsgiServerTask)),
    )

    tasks = i[ta.AbstractSet[ShellTask]]
    assert [t() for t in tasks] == ['served']


##
# Pattern: wrapper stacks with unwrapped_key= and with_= (the ai-driver stack).
#
# A stack can be built under an *internal* (tagged) key while its wrapper classes are written against the public
# interface - `unwrapped_key=` aliases the public key to the layer below within each level's private. `with_=`
# supplies extra elements visible only to that one layer's construction.


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


class PrefixRenderer(Renderer):
    def __init__(self, wrapped: Renderer, prefix: str) -> None:
        super().__init__()

        self.wrapped = wrapped
        self.prefix = prefix

    def render(self) -> str:
        return self.prefix + self.wrapped.render()


def test_wrapper_stack_unwrapped_and_with():
    stack = inj.wrapper_binder_helper(inj.as_key(Renderer, tag='stack'), unwrapped_key=Renderer)

    i = inj.create_injector(
        stack.push_bind(to_ctor=TextRenderer),
        stack.push_bind(to_ctor=BoldRenderer),
        stack.push_bind(to_ctor=PrefixRenderer, with_=[inj.bind('* ')]),
        inj.bind(Renderer, to_key=stack.top),
    )

    assert i[Renderer].render() == '* <b>hi</b>'

    # The with_ const stayed inside its layer's private:
    with pytest.raises(inj.UnboundKeyError):
        i.provide(str)


##
# Pattern: a provision listener as a lifecycle registrar (iceworm's LifecycleRegistrar).
#
# Every provisioned instance of a marker interface is auto-registered with a manager - instrumentation attached at
# the injector level, invisible to the bindings. Registration lands in dependency-first order, which is exactly the
# order a lifecycle manager wants.


class Lifecycle:
    pass


class LifecycleManager:
    def __init__(self) -> None:
        self.registered: list = []


class LcDb(Lifecycle):
    pass


class LcServer(Lifecycle):
    def __init__(self, db: LcDb) -> None:
        self.db = db


def test_provision_listener_lifecycle_registrar():
    mgr = LifecycleManager()

    async def registrar(injector, key, binding, fn):
        v = await fn()
        if isinstance(v, Lifecycle) and not any(r is v for r in mgr.registered):
            mgr.registered.append(v)
        return v

    i = inj.create_injector(
        inj.bind(LcDb, singleton=True),
        inj.bind(LcServer, singleton=True),
        inj.bind_provision_listener(registrar),
    )

    s = i[LcServer]
    assert mgr.registered == [s.db, s]


##
# Pattern: managed assembly, end to end.
#
# The usual entrypoint shape: a managed injector owning resource lifecycles, assembled from binder functions, torn
# down in reverse order at exit.


class Closeable:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class PatDb(Closeable):
    pass


class PatServer(Closeable):
    def __init__(self, db: PatDb) -> None:
        super().__init__()

        self.db = db


def test_managed_assembly():
    closed_order: list = []

    def track(o):
        @contextlib.contextmanager
        def inner():
            yield o
            o.close()
            closed_order.append(type(o).__name__)
        return inner()

    with inj.create_managed_injector(
        inj.bind(PatDb, singleton=True, to_fn=inj.make_managed_provider(PatDb, track)),
        inj.bind(PatServer, singleton=True, to_fn=inj.make_managed_provider(PatServer, track)),
    ) as i:
        server = i[PatServer]
        assert not closed_order

    # Teardown ran, dependents before dependencies:
    assert server.closed
    assert server.db.closed
    assert closed_order == ['PatServer', 'PatDb']
