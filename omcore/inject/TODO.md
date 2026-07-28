- Bugs
  - **`omcore/inject`: `eager=True` on a `ThreadScope` binding is silently ignored.** `_init`
    (`omcore/inject/impl/injector.py`) instantiates eagers for `Unscoped`/`Singleton` only, `SeededScope` eagers run at
    scope entry, and `ThreadScope` eagers are grouped into `_ekbs` but never instantiated. Needs a behavior decision:
    reject loudly at injector init, or instantiate per-thread on first use.
  - **`omcore/inject`: override replaces per-key element lists wholesale.** In `_build_raw_element_multimap`
    (`omcore/inject/impl/elements.py`), an override's elements for a key *replace* the source's rather than merge: an
    override `SetBinding`/`MapBinding` replaces all of src's entries for that multi-key (instead of adding to them), and
    a `bind(..., eager=True)` overridden by a plain binding silently loses its `Eager`. Adjacent to the existing `#
    FIXME: merge None keys?` there.
- create_asyncio_managed_injector? deal with that..
- ** can currently bind in a child/private scope shadowing an external parent binding **
- better source tracking
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
