- refcycle hygiene (steady-state provision and injector/ElementCollection drop - privates and wrapper stacks
  included - are refcount-clean as of the weakref passes and cached_function's weak instance binding - see
  `tests/test_gc.py`; remaining known cycles):
  - Singletons that inject `Injector` itself cycle through the scope cache - accepted (it's the antipattern).
    Possible sugar: 'automatic' weakref-wrapping injection, analogous to optional-stripping - eg. a param annotated
    `weakref.ref[Foo]` (or a marker) provided as a weak ref. Maybe.
- create_asyncio_managed_injector? deal with that..
- ** can currently bind in a child/private scope shadowing an external parent binding **
- better source tracking
- validate binding scopes at collection - a binding in a never-registered scope (no `ScopeBinding`, not a default)
  currently dies with a raw `KeyError` from `_scopes[bi.scope]` at provision time; reject loudly at injector creation,
  as with eagers
- **multi-scope seeds** - direction undecided. A seed key can currently belong to only one scope:
  `bind_scope_seed(str, scope_a)` + `bind_scope_seed(str, scope_b)` is a `ConflictingKeyError`, because each emits an
  ordinary (unscoped) `Binding(k, ScopeSeededProvider(ss, k))` and two scopes means two unequal bindings for one key.
  - Current workaround, codified in `tests/test_patterns.py` (phased pipeline): per-scope *tagged* seed keys, with
    consumers re-pointed per scope via `build_kwargs_target(...).override(...)`. Workable, but ceremonious - and
    arguably tagged-per-scope keys are the honest model (a 'parse-phase doc' and a 'render-phase doc' *are* different
    keys)... which is an argument for keeping the restriction and just improving its error.
  - Candidate fix if merging is ever wanted, mirroring how multis already fold: keep the per-scope elements exactly
    as-is (independent binders can then seed the same key into their own scopes without coordination), and merge at
    collection - in `_build_binding_impl_map`, when all of a key's bindings carry `ScopeSeededProvider`s, fold them
    into a `MultiScopeSeededProviderImpl` holding every scope.
  - Provision resolution semantics: candidates = currently-open scopes whose state was *actually seeded* with the
    key; exactly one → serve it; none → `ScopeNotOpenError`; several → a new ambiguity error (overlapping scope
    lifetimes are legal - see `tests/test_adversarial.py::test_overlapping_scope_lifetimes` - so the multi-open case
    is real, and any silent priority rule would be a footgun).
  - Filtering candidates on 'actually seeded' rather than merely 'open' would incidentally fix the adjacent wart of
    a raw `KeyError` when a scope is entered without a declared seed
    (`tests/test_adversarial.py::test_missing_seed`) - the single-scope path could adopt the same check for a
    semantic error either way.
  - Open questions: is 'both open and both seeded' an error or a legitimate shadowing usecase (innermost wins?)?
    should `bind_scope_seed` of the same key into the same scope twice stay a squash? does merged-seed provision
    interact with frozen scopes (it shouldn't - seeds bypass the once-map)?
  - Rough effort: one `ProviderImpl`, one special-case branch in `_build_binding_impl_map`, one new error - the same
    size as the seeded-scope freeze change.
- scope bindings, auto in root
- injector-internal / blacklisted bindings (Injector itself, default scopes) without rebuilding ElementCollection
- config - proxies, impl select, etc
  - config is probably shared with ElementCollection... but not 'bound', must be shared everywhere
  - InjectorRoot object?
- ** eagers in any scope, on scope init/open
- unions - raise on ambiguous - usecase: sql.AsyncEngineLike
- multiple live request scopes on single injector - use private injectors?
- more listeners - UnboundKeyListener
  - lazy parent listener chain cache thing
- https://github.com/7mind/izumi-chibi-ts
  - Axis tagging for conditional bindings (e.g., dev vs prod implementations)
  - Fail-fast validation with circular and missing dependency detection
- *ta.Annotated as alternative to tag*
  - need to pre-collect all tags (/type pairs?) in CollectedElements, scan for only those, strip Annotated otherwise
    - KwargsTarget cache needs an additional weak key dimension of Annotated type set
- pre-generate, or cache, KT -> provision / injection action graph
  - move towards efficient RequestScope usecase
- DynamicSetBinding / DynamicMapBinding ? provider of set[T] / map[K, V] ?
  - doable not guicey - too much dynamism
- audit multis scopes
- inspect:
  - cache kwarg_keys
  - tag annotations? x: ta.Annotated[int, inj.Tag('foo')]
  - tag decorator - @inj.tag(x='foo')
  - *unpack optional here*
  - use omcore.metadata
- scopes
  - ContextVar ('context')
  - greenlet?
  - dynamic? https://github.com/wrmsr/iceworm/blob/2f6b4d5e9d237ef9665f7d57cfa6ce328efa0757/iceworm/utils/inject.py#L44
- proxy lol
- InjectorConfig by now probably
- internal_consts being weakrefs is weird
