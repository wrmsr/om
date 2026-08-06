"""
The Runtime is the state-owning heart of a marshaling universe: one config registry, one reflection mirror, one pair of
root factories, and all handler caches, under one lock. Factories and handlers remain stateless and shareable;
contexts remain ephemeral per-op views; the Runtime is the one thing with a lifetime.

Handler caching is footprint-keyed: while a handler is being constructed, every config read made through the
construction context is recorded (including misses, and transitively through recursively-constructed child handlers)
as that cache entry's config footprint. The registry's snapshot version is the fast-path fence - an entry built at the
current version is served without further checks - and on version mismatch the footprint is revalidated against the
live registry, either restamping the entry in place (nothing it read has changed) or discarding it for rebuild. Late
config registrations therefore invalidate exactly the handlers whose construction observed the touched keys.

The registry is the only mutable config source and thus the only footprinted one - object metadata, dataclass field
metadata, and manifests are append-only and deliberately outside the invalidation model. Reflection-time config reads
(ReflectOverride) are likewise not footprinted: the mirror is built once per runtime and bakes overrides in, preserving
the documented register-before-first-reflection contract.
"""
import threading
import typing as ta

from ... import check
from ... import lang
from ... import reflect as rfl
from .configs import Config
from .configs import ConfigRegistry
from .configs import ConfigValues
from .configs import LazyInit
from .contexts import BaseFactoryContext
from .contexts import MarshalContext
from .contexts import MarshalFactoryContext
from .contexts import UnmarshalContext
from .contexts import UnmarshalFactoryContext
from .errors import UnhandledTypeError
from .reflect import _make_context_mirror
from .specs import InternalSpec
from .specs import Spec
from .types import Factory
from .types import Handler
from .types import Marshaler
from .types import MarshalerFactory
from .types import Unmarshaler
from .types import UnmarshalerFactory


if ta.TYPE_CHECKING:
    from .values import Value


T = ta.TypeVar('T')

HandlerT = ta.TypeVar('HandlerT', bound=Handler)
FactoryT = ta.TypeVar('FactoryT', bound=Factory)
FactoryContextT = ta.TypeVar('FactoryContextT', bound=BaseFactoryContext)


##


class _ConfigDep(ta.NamedTuple):
    key: ta.Any
    identity: bool | None
    cls: type | None  # The TypedValue class sliced out of the ConfigValues, or None for the whole collection.

    expected: ta.Any

    @property
    def map_key(self) -> _ConfigDepMapKey:
        return (
            id(self.key),
            self.identity,
            self.cls,
        )


_ConfigDepMapKey: ta.TypeAlias = tuple[
    int,          # id(dep.key)
    bool | None,  # dep.identity
    type | None,  # dep.cls
]


class _Frame:
    def __init__(self) -> None:
        super().__init__()

        self.deps: dict[_ConfigDepMapKey, _ConfigDep] = {}

    def record(
            self,
            key: ta.Any,
            identity: bool | None,
            cls: type | None,
            expected: ta.Any,
    ) -> None:
        d = _ConfigDep(
            key,
            identity,
            cls,
            expected,
        )
        self.deps[d.map_key] = d

    def fold(self, deps: ta.Iterable[_ConfigDep]) -> None:
        for d in deps:
            self.deps[d.map_key] = d


def _validate_deps(cr: ConfigRegistry, deps: ta.Iterable[_ConfigDep]) -> bool:
    for d in deps:
        try:
            cvs = cr.get(d.key, identity=d.identity)
        except TypeError:
            return False

        cur: ta.Any = cvs.get(d.cls) if d.cls is not None else cvs

        if cur is d.expected:
            continue

        try:
            eq = bool(cur == d.expected)
        except Exception:  # noqa
            return False
        if not eq:
            return False

    return True


##


class _RecordingConfigValues(ConfigValues):
    """
    Duck-typed stand-in for a ConfigValues returned by a recording Configs view. Class-sliced `get` calls are recorded
    fine-grained - a footprint dep on only that (key, class) slice - so unrelated writes under the same registry key
    (most importantly LazyInit registrations under the global None key) don't invalidate. Any other use of the
    collection records a coarse whole-collection dep.
    """

    def __init__(
            self,
            cr: ConfigRegistry,
            frame: _Frame,
            key: ta.Any,
            identity: bool | None,
            cvs: ConfigValues,
    ) -> None:
        super().__init__()

        self._cr = cr
        self._frame = frame
        self._key = key
        self._identity = identity
        self._cvs = cvs

    def _record_coarse(self) -> None:
        # Merged (identity=None) collections are rebuilt fresh per registry snapshot, so their identity is unstable
        # across unrelated updates - record the two stable underlying collections instead.
        if self._identity is None and self._key is not None:
            self._frame.record(
                self._key,
                False,
                None,
                self._cr.get(self._key, identity=False),
            )

            self._frame.record(
                self._key,
                True,
                None,
                self._cr.get(self._key, identity=True),
            )

        else:
            idn = False if self._key is None else bool(self._identity)
            self._frame.record(
                self._key,
                idn,
                None,
                self._cr.get(self._key, identity=idn),
            )

    #

    def __iter__(self) -> ta.Iterator[ta.Any]:
        self._record_coarse()
        return iter(self._cvs)

    def __len__(self) -> int:
        self._record_coarse()
        return len(self._cvs)

    def __bool__(self) -> bool:
        self._record_coarse()
        return bool(self._cvs)

    def _typed_value_contains(self, cls):
        self._record_coarse()
        return cls in self._cvs

    def _typed_value_getitem(self, key):
        if isinstance(key, int):
            self._record_coarse()
            return self._cvs[key]

        cls = check.isinstance(key, type)
        check.issubclass(key, Config)

        raw = self._cvs.get(cls)
        self._frame.record(self._key, self._identity, cls, raw)

        return self._cvs.get(key)

    def _typed_value_get_any(self, cls):
        self._record_coarse()
        return self._cvs.get_any(cls)


##


class _Proxy(ta.Generic[T]):
    __obj: T | None = None

    @property
    def _obj(self) -> T:
        if self.__obj is None:
            raise TypeError('recursive proxy not set')
        return self.__obj

    def _set_obj(self, obj: T) -> None:
        if self.__obj is not None:
            raise TypeError('recursive proxy already set')
        self.__obj = obj

    @classmethod
    def _new(cls) -> tuple[ta.Any, ta.Callable[[ta.Any], None]]:
        return (p := cls()), p._set_obj  # noqa


class _ProxyMarshaler(_Proxy[Marshaler], Marshaler):
    def marshal(self, ctx: MarshalContext, o: ta.Any) -> Value:
        return self._obj.marshal(ctx, o)


class _ProxyUnmarshaler(_Proxy[Unmarshaler], Unmarshaler):
    def unmarshal(self, ctx: UnmarshalContext, v: Value) -> ta.Any:
        return self._obj.unmarshal(ctx, v)


##


@ta.final
class Runtime(lang.Final):
    def __init__(
            self,
            *,
            config_registry: ConfigRegistry | None = None,
            marshaler_factory: MarshalerFactory | None = None,
            unmarshaler_factory: UnmarshalerFactory | None = None,
    ) -> None:
        super().__init__()

        if config_registry is None:
            config_registry = ConfigRegistry()
        self._config_registry = config_registry

        self._marshaler_factory = marshaler_factory
        self._unmarshaler_factory = unmarshaler_factory

        self._lock = threading.RLock()
        self._tl = self._ConstructionTls()

        self._mirror_: rfl.Mirror | None = None

        self._m: Runtime._Side[
            MarshalerFactory,
            MarshalFactoryContext,
            Marshaler,
        ] = Runtime._Side(  # noqa
            marshaler_factory,
            _ProxyMarshaler._new,  # noqa
            lambda fac, ctx, spec: fac.make_marshaler(
                check.isinstance(ctx, MarshalFactoryContext),
                spec,
            ),
        )

        self._u: Runtime._Side[
            UnmarshalerFactory,
            UnmarshalFactoryContext,
            Unmarshaler,
        ] = Runtime._Side(  # noqa
            unmarshaler_factory,
            _ProxyUnmarshaler._new,  # noqa
            lambda fac, ctx, spec: fac.make_unmarshaler(
                check.isinstance(ctx, UnmarshalFactoryContext),
                spec,
            ),
        )

        self._warm_lock = threading.RLock()
        self._warm_tl = self._WarmTls()
        self._ran_lazy_inits: set[LazyInit] = set()
        self._last_global_configs: ConfigValues | None = None

        #

    class _ConstructionTls(threading.local):
        def __init__(self) -> None:
            super().__init__()

            self.frames: list[_Frame] = []

    class _WarmTls(threading.local):
        def __init__(self) -> None:
            super().__init__()

            self.running = False

    #

    class _Entry(ta.Generic[HandlerT]):
        __slots__ = (
            'handler',
            'deps',
            'generation',
        )

        def __init__(
                self,
                handler: HandlerT,
                deps: tuple[_ConfigDep, ...],
                generation: int,
        ) -> None:
            super().__init__()

            self.handler = handler  # None for a cached negative (unhandled type)
            self.deps = deps
            self.generation = generation

    class _Side(ta.Generic[FactoryT, FactoryContextT, HandlerT]):
        def __init__(
                self,
                factory: FactoryT | None,
                new_proxy: ta.Callable[[], tuple[HandlerT, ta.Callable[[HandlerT], None]]],
                call: ta.Callable[[FactoryT, FactoryContextT, Spec], ta.Callable[[], HandlerT] | None],
        ) -> None:
            super().__init__()

            self.factory = factory
            self.new_proxy = new_proxy
            self.call = call

            self.entries: dict[ta.Any, Runtime._Entry[HandlerT]] = {}
            self.building: dict[ta.Any, tuple[HandlerT, ta.Callable[[HandlerT], None]]] = {}

    #

    @property
    def config_registry(self) -> ConfigRegistry:
        return self._config_registry

    def get_factory_configs(
            self,
            key: ta.Any = None,
            *,
            identity: bool | None = None,
    ) -> ConfigValues:
        """The construction-time view: reads made through this while a handler is being built are footprinted."""

        if not (frames := self._tl.frames):
            raise RuntimeError(
                'Cannot access factory_configs without an active factory frame. '
                'This can happen when calling `factory.make_` methods directly, rather than the preferred '
                'equivalent `factory_context.make_` methods.',
            )
        return _RecordingConfigValues(
            cr := self._config_registry,
            frames[-1],
            key,
            identity,
            cr.get(key, identity=identity),
        )

    @property
    def marshaler_factory(self) -> MarshalerFactory | None:
        return self._marshaler_factory

    @property
    def unmarshaler_factory(self) -> UnmarshalerFactory | None:
        return self._unmarshaler_factory

    def get_mirror(self) -> rfl.Mirror:
        if (m := self._mirror_) is not None:
            return m

        with self._lock:
            if (m := self._mirror_) is None:
                m = self._mirror_ = _make_context_mirror(self._config_registry.get)
            return m

    #

    def ensure_warm(self) -> None:
        # Never warm mid-construction: the main lock is held, and warming takes the warm lock while lazy init code may
        # itself marshal (taking the main lock) - the two must never be acquired in opposite orders.
        if self._tl.frames:
            return

        gcs = self._config_registry.get()
        if gcs is self._last_global_configs:
            return

        if self._warm_tl.running:
            return

        with self._warm_lock:
            while True:
                gcs = self._config_registry.get()

                lis = gcs.get(LazyInit)
                # FIXME: can we avoid rescanning all of them every time?
                pending = [li for li in lis if li not in self._ran_lazy_inits] if lis else []

                if not pending:
                    self._last_global_configs = gcs
                    return

                self._warm_tl.running = True
                try:
                    for li in pending:
                        li.fn(self._config_registry)
                        self._ran_lazy_inits.add(li)
                finally:
                    self._warm_tl.running = False

    #

    def flush(self) -> None:
        with self._lock:
            self._m.entries.clear()
            self._u.entries.clear()
            self._mirror_ = None

    #

    def _hit(self, e: _Entry, spec: Spec) -> ta.Any:
        if (frames := self._tl.frames):
            frames[-1].fold(e.deps)

        if e.handler is None:
            raise UnhandledTypeError(spec)
        return e.handler

    def _make_locked(
            self,
            side: _Side[FactoryT, FactoryContextT, HandlerT],
            ctx: FactoryContextT,
            spec: Spec,
            ek: ta.Any,
    ) -> HandlerT:
        gen = self._config_registry.version

        if (e := side.entries.get(ek)) is not None:
            if e.generation == gen or _validate_deps(self._config_registry, e.deps):
                e.generation = gen
                return self._hit(e, spec)
            del side.entries[ek]

        if (px := side.building.get(ek)) is not None:
            # Recursive knot: this can only be the lock-holding thread re-entering for a type already under
            # construction - other threads are blocked on the lock and never observe in-progress state.
            return px[0]

        fac = check.not_none(side.factory)

        frames = self._tl.frames
        frame = _Frame()
        frames.append(frame)

        px = side.new_proxy()
        side.building[ek] = px

        h: ta.Any
        try:
            thunk = side.call(fac, ctx, spec)
            h = thunk() if thunk is not None else None
        finally:
            frames.pop()
            del side.building[ek]

        deps = tuple(frame.deps.values())
        side.entries[ek] = Runtime._Entry(h, deps, gen)

        if frames:
            frames[-1].fold(deps)

        if h is None:
            raise UnhandledTypeError(spec)

        px[1](h)
        return h

    def _make(
            self,
            side: _Side[FactoryT, FactoryContextT, HandlerT],
            ctx: FactoryContextT,
            o: ta.Any,
    ) -> HandlerT:
        self.ensure_warm()

        # A Spec passes through as-is; anything else is an annotation-ish object sent to the mirror. InternalSpecs are
        # value-keyed by themselves; reflected types are keyed by their TypeKey.
        spec: Spec = o if isinstance(o, (rfl.Type, InternalSpec)) else self.get_mirror().reflect_type(o)
        ek = spec.type_key() if isinstance(spec, rfl.Type) else spec

        if (e := side.entries.get(ek)) is not None and e.generation == self._config_registry.version:
            return self._hit(e, spec)

        with self._lock:
            return self._make_locked(
                side,
                ctx,
                spec,
                ek,
            )

    #

    def make_marshaler(self, ctx: MarshalFactoryContext, o: ta.Any) -> Marshaler:
        return self._make(self._m, ctx, o)

    def make_unmarshaler(self, ctx: UnmarshalFactoryContext, o: ta.Any) -> Unmarshaler:
        return self._make(self._u, ctx, o)
