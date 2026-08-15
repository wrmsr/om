Very little. In the current [`mk.py`](sandbox:/mnt/data/mk.py), only two mappings are part of the persistent logical state:

```python
State.substitution
State.domains
```

The actual state-extension code has only three whole-dictionary copies:

```python
substitution = dict(state.substitution)
domains = dict(state.domains)
```

in `_bind_raw`, and:

```python
domains = dict(state.domains)
```

in `_set_domain_raw`.

Those are the only important sites to replace.

## Which `omcore` implementation to use

I would use `BtreeMap` initially, not `HamtMap`.

`PersistentMapping` is the abstract interface: it retains the normal `Mapping` read API and adds functional `with_`, `without`, and `default` operations. `BtreeMap` is a concrete implementation whose factory accepts a comparator; it uses a pure-Python backend by default and substitutes the C backend when available. 

`Var` has identity equality and is not orderable, so the B-tree needs an identity-order comparator:

```python
from omcore.collections.btreemap.btreemap import new_btree_map
from omcore.collections.persistent import PersistentMapping
```

Add this immediately before `State`:

```python
def _compare_vars(left: Var, right: Var) -> int:
    return (id(left) > id(right)) - (id(left) < id(right))


def _new_substitution() -> PersistentMapping[Var, object]:
    return new_btree_map(cmp=_compare_vars)


def _new_domains() -> PersistentMapping[Var, FdDomain]:
    return new_btree_map(cmp=_compare_vars)
```

The `id` ordering is safe here: two simultaneously live objects cannot have the same identity, and the mapping itself keeps every key alive. The ordering is process-specific, but nothing in the solver depends on substitution-map iteration order.

## Change `State`

Replace:

```python
@dc.dataclass(frozen=True, slots=True)
class State:
    substitution: ta.Mapping[Var, object]
    constraints: tuple[_Constraint, ...]
    domains: ta.Mapping[Var, FdDomain]
    occurs_check: bool
    runtime: _Runtime

    @classmethod
    def empty(
            cls,
            *,
            occurs_check: bool = True,
            max_steps: int | None = None,
            trace: TraceFn | None = None,
    ) -> 'State':
        return cls({}, (), {}, occurs_check, _Runtime(max_steps, trace))
```

with:

```python
@dc.dataclass(frozen=True, slots=True)
class State:
    substitution: PersistentMapping[Var, object]
    constraints: tuple[_Constraint, ...]
    domains: PersistentMapping[Var, FdDomain]
    occurs_check: bool
    runtime: _Runtime

    @classmethod
    def empty(
            cls,
            *,
            occurs_check: bool = True,
            max_steps: int | None = None,
            trace: TraceFn | None = None,
    ) -> 'State':
        return cls(
            _new_substitution(),
            (),
            _new_domains(),
            occurs_check,
            _Runtime(max_steps, trace),
        )
```

Also tighten `_state_with`:

```python
def _state_with(
        state: State,
        *,
        substitution: PersistentMapping[Var, object] | None = None,
        constraints: tuple[_Constraint, ...] | None = None,
        domains: PersistentMapping[Var, FdDomain] | None = None,
) -> State:
    return State(
        state.substitution if substitution is None else substitution,
        state.constraints if constraints is None else constraints,
        state.domains if domains is None else domains,
        state.occurs_check,
        state.runtime,
    )
```

The tighter type is worthwhile: after this change, accidentally passing an ordinary dictionary would fail later when the solver calls `.with_`.

## Replace `_bind_raw`

The complete persistent version is:

```python
def _bind_raw(state: State, variable: Var, value: object) -> State | None:
    value = walk(value, state)
    if value is variable:
        return state
    if state.occurs_check and _occurs(variable, value, state):
        return None

    substitution = state.substitution
    domains = state.domains

    variable_domain = domains.get(variable)
    if variable_domain is not None:
        domains = domains.without(variable)

    if isinstance(value, Var):
        value_domain = domains.get(value)

        if variable_domain is not None and value_domain is not None:
            merged = variable_domain.intersect(value_domain)
            if not merged:
                return None

            if merged != value_domain:
                domains = domains.with_(value, merged)

        elif variable_domain is not None:
            domains = domains.with_(value, variable_domain)

        substitution = substitution.with_(variable, value)

        next_state = _state_with(
            state,
            substitution=substitution,
            domains=domains,
        )

        merged_domain = domains.get(value)
        if (
                merged_domain is not None and
                merged_domain.singleton is not None
        ):
            return _bind_raw(
                next_state,
                value,
                merged_domain.singleton,
            )

        return next_state

    if variable_domain is not None:
        if not _is_fd_int(value) or value not in variable_domain:
            return None

    substitution = substitution.with_(variable, value)

    return _state_with(
        state,
        substitution=substitution,
        domains=domains,
    )
```

This preserves the original behavior:

* a bound variable’s FD domain is removed;
* variable-to-variable binding transfers or intersects domains;
* variable-to-value binding checks the domain;
* singleton domains still immediately instantiate the target variable.

The only substantive difference is structural sharing instead of whole-map copying.

The check:

```python
if merged != value_domain:
```

is a small new optimization. `FdDomain.intersect()` creates a new object even when the resulting domain equals the existing one. Since `BtreeMap.with_()` uses value identity to recognize an unchanged insertion, avoiding the call here prevents an unnecessary tree path copy.

## Replace `_set_domain_raw`

Replace:

```python
    domains = dict(state.domains)
    domains[value] = merged
    out = _state_with(state, domains=domains)
```

with:

```python
    domains = state.domains.with_(value, merged)
    out = _state_with(state, domains=domains)
```

The surrounding function already has:

```python
if old_domain == merged:
    return state
```

so it will not create a new mapping when the domain is semantically unchanged.

## Nothing else should become persistent

These dictionaries should remain ordinary mutable dictionaries:

```python
_Runtime.tables
_Canonicalizer._variables
_Freshener._variables
_Reifier._variables
assignments
per_variable
```

They serve different purposes:

* `_Runtime.tables` is intentionally shared among branches. Tabled consumers observe mutable `_TableEntry` objects as new answers are added. Turning the table registry into branch-local persistent state would complicate or break that coordination.
* Canonicalizer, freshener, and reifier maps are short-lived operation-local caches.
* `assignments` and `per_variable` are scratch accumulators inside one constraint-propagation step.

Likewise, Python dictionaries used as **logical terms** are unrelated to the substitution representation. All of these checks should remain unchanged:

```python
isinstance(value, dict)
```

Changing those to support arbitrary `Mapping` terms would be a separate feature affecting normalization, unification, constraint handling, canonicalization, freshening, and reification.

## Why I would not directly use `HamtMap`

A HAMT is conceptually the more natural structure for identity-hashed `Var` keys, and `omcore` does provide `HamtMap`. But its current wrapper has two relevant properties:

1. It depends on the native `_hamt` module; unlike `BtreeMap`, there is no pure-Python backend in that module.
2. It uses `None` as the internal “missing” result and consequently rejects `None` values in `with_()` via `check.not_none(v)`. ([GitHub][1])

The second point matters because this is valid miniKanren:

```python
x = mk.var('x')

assert mk.run_star(
    x,
    mk.eq(x, None),
) == [None]
```

That creates a substitution entry whose value really is `None`, so this would fail:

```python
substitution = substitution.with_(variable, None)
```

### Using `HamtMap` anyway

Wrap substitution values:

```python
@dc.dataclass(frozen=True, slots=True)
class _Binding:
    value: object
```

Then store:

```python
substitution = substitution.with_(
    variable,
    _Binding(value),
)
```

and change the two substitution reads:

```python
value = state.substitution[value].value
```

in both `walk` and `_walk_path`.

Domains can use `HamtMap[Var, FdDomain]` directly because a domain value is never `None`.

A hybrid factory could select HAMT when available and otherwise use the B-tree:

```python
from omcore.collections.btreemap.btreemap import new_btree_map
from omcore.collections.hamt.hamtmap import is_hamt_available
from omcore.collections.hamt.hamtmap import new_hamt_map
from omcore.collections.persistent import PersistentMapping


def _new_var_map() -> PersistentMapping[Var, object]:
    if is_hamt_available():
        return new_hamt_map()

    return new_btree_map(cmp=_compare_vars)
```

But once `_Binding` is required for the HAMT, I would use it consistently with both backends rather than making storage representation backend-dependent.

## Expected effect

The old behavior extends a substitution by copying every existing entry:

```text
bind cost ≈ O(number of current bindings)
```

The persistent B-tree copies only the nodes along one search path:

```text
bind cost ≈ O(log(number of current bindings))
```

More importantly for miniKanren, sibling branches now retain the exact same substitution and domain structure for their common prefix rather than each owning a copied dictionary.

There is still a constant-factor tradeoff:

* very small Python dictionaries are exceptionally fast;
* the B-tree performs Python-level traversal and calls the variable comparator;
* branch-heavy searches with moderate or large substitutions should benefit much more than tiny relations.

So I would treat this as an architectural improvement with plausible performance benefits, then benchmark representative searches rather than assuming it wins at every substitution size.

I applied the above transformation against an API-compatible persistent-map implementation and the existing `test_mk.py` suite remained at **44 passing tests**. The actual `omcore` wheel was not installed in this execution environment, so that validation covered the solver changes and API shape rather than the concrete `omcore` backend.

[1]: https://github.com/wrmsr/om/blob/master/omcore/collections/hamt/hamtmap.py?utm_source=chatgpt.com "om/omcore/collections/hamt/hamtmap.py at master · wrmsr/om · GitHub"
