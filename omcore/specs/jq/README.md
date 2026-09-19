# Pure-Python jq

`omcore.specs.jq` is a zero-required-dependency jq 1.8-compatible evaluator for embedding in Python. It implements jq
filters as lazy generators, compiles parsed syntax to Python closures, and operates directly on ordinary Python values.

```python
from omcore.specs.jq import compile_jq

program = compile_jq('.items[] | select(.active) | {id, name}')
results = list(program.evaluate({'items': [
    {'id': 1, 'name': 'one', 'active': True},
    {'id': 2, 'name': 'two', 'active': False},
]}))
```

The supported language includes generator composition, arrays and objects, navigation and recursive descent, lexical
variables, user functions with filter and value parameters, conditionals, reductions, `try`/`catch`, lexical labels,
path operations, copy-on-write assignment, lazy `input`, iterative standard controls, regular expressions, and the
common jq standard-library family documented by the package tests. Unsupported module/import, date, SQL join, debug,
environment, halt, and exact decimal-literal facilities fail rather than being approximated.

The v1 grammar deliberately omits destructuring bindings, module syntax, `@format` filters, and assignment through a
slice path. Slices remain supported for ordinary reads. Cyclic Python containers are not jq values and are rejected
when traversal encounters them.

## Values and ownership

Inputs may contain `None`, booleans, finite integers/floats, strings, reasonable `Sequence` values, and reasonable
`Mapping` values. Produced arrays and objects are lists and dictionaries. jq truth, equality, and total ordering are
implemented independently of Python's corresponding behavior.

Evaluation never mutates caller-owned containers. Assignment shallow-copies only containers on changed paths; untouched
subtrees remain shared, including large mutable lists or dictionaries referenced by more than one output. Outputs
should be treated as immutable. With `stable_outputs=True` (the default), advancing an evaluator cannot mutate an
earlier result. With `stable_outputs=False`, internal working containers may be exposed and subsequently reused;
callers must consume them before advancing and must not mutate them. The current evaluator is naturally stable in most
cases even when the guarantee is disabled; disabling it does not force reuse.

Non-string mapping keys raise by default. `JqValueOptions` can instead ignore them or provide an explicit stringifier.
Key handling occurs as keys are semantically encountered rather than through an eager validation pass.

## Input and streaming

`program.evaluate(value)` evaluates one current value. `program.run(inputs)` drives jq's outer input stream; the outer
driver and the `input`/`inputs` filters share one lazy iterator. Null-input mode evaluates once on `null` without first
consuming that iterator.

The independent `BeginArray`, `EndArray`, `BeginObject`, `ObjectKey`, `EndObject`, and `Scalar` event protocol can be
produced by arbitrary applications. `walk_structural_events` walks Python collections, while
`parse_json_structural_events` adapts the repository's streaming JSON parser without materializing a document.
`encode_jq_stream` converts either source to jq `--stream` records using O(depth) state. The `tostream` filter uses the
same walker and encoder.

## Regex and recursion

The default regex engine uses `re`. `RegexPackageEngine` in `regexoptional` uses the optional third-party `regex`
package, and passing `regex_engine=None` disables regex explicitly. Result objects follow jq's shape and offsets use
Unicode codepoint indexes, but pattern syntax is that of the selected Python backend rather than Oniguruma. Unsupported
flags raise explicitly.

User functions have a configurable jq recursion guard, defaulting to 1000, and no tail-call optimization is claimed.
`repeat`, `while`, `until`, and `recurse` are native iterative filters so bounded consumers can safely use logically
unbounded streams.

## CLI and attribution

Run `./python -m omcore.specs.jq FILTER [files...]`. The CLI supports compact/raw output, null and raw input, slurp,
`--stream`, `--arg`, and `--argjson`.

The packaged `prelude.jq` is adapted from jq 1.8.2 `src/builtin.jq`. jq is Copyright (C) 2012 Stephen Dolan and is
distributed under the MIT terms in `LICENSE`. Exact diagnostics, decimal literal preservation, Oniguruma compatibility,
CLI parsing quirks, and jq's C VM are intentionally outside this implementation's compatibility contract.
