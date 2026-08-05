# TODO

Remaining work for the save/restore ('snapshot') feature.

## Current state

The engine's binary serializer is exposed data-only: `Object.serialize() -> bytes` and `Context.deserialize(blob)`,
both hardwired to the `REFERENCE` flags (never `BYTECODE`, never `SAB`). Round-trip, error-path, and cross-context
clone/fan-out tests live in `tests/test_serialize.py` and `tests/test_clone.py`, and pass on both the default and
freethreaded builds. `_quickjs/quickjs.c` carries one local patch (`@om-local-patch` in `JS_ReadRegExp`) fixing the
upstream reference-desync bug; `tests/test_serialize.py` holds its regression tests.

`snapshots.py` provides data snapshots of a context's user globals on top of that. Contexts are capability-free by
default, with opt-in `with_std=True` (qjs:std / qjs:os) and `with_bjson=True` (JS-side serializer) modules.

Blobs are version-locked: valid only for the exact vendored engine build that wrote them (the format's `BC_VERSION`
byte plus build invariants the byte does not cover - opcode numbering, the predefined-atom table, the libregexp
bytecode format). They are caches and transfer envelopes, not archives.

## ~~Context.snapshot() / Context.restore()~~ - DONE, see `snapshots.py`

Implemented as `snapshots.take_snapshot(ctx, *, skip_unsupported=False) -> Snapshot` and
`snapshots.restore_snapshot(ctx, snapshot) -> Sequence[str]` - pure Python over `Object.serialize()` /
`Context.deserialize()`, no new C. Strict by default (`UnsupportedGlobalsError` naming the offending globals), with
opt-in skip mode reporting them in `Snapshot.skipped`. The pristine baseline is one cached throwaway `Context` (on
0.16.1 it is exactly `{'performance'}`).

Every limitation below is now demonstrated and locked in by `tests/test_snapshots.py`. Two entries in the original
plan turned out to be wrong when probed, and are corrected here:

- Symbol-keyed properties are **not** dropped - they are carried. But a *unique* symbol key deserializes as a fresh
  symbol, so the property becomes unreachable via any separately-restored reference to 'the same' symbol.
- Prototype loss is as described (class instances rehydrate as plain objects, methods gone), but `Object.create(p)`
  with a method-bearing prototype fails outright, since the prototype object is itself an unsupported global.

Also-real limitations not in the original plan: object integrity (`freeze`/`seal`/`preventExtensions`) is lost,
property attributes are normalized to writable/enumerable/configurable, array holes are filled in and non-index
array properties dropped, and `let`/`const` globals are invisible (they live in the lexical scope, not
`globalThis`).

Possible follow-ups, none blocking:

- A `Context.snapshot()` / `Context.restore()` method pair as sugar over the module functions, if the free-function
  form proves awkward in practice.
- Capturing `let`/`const` is not possible through `globalThis`; if it ever matters, the answer is a code image
  (below) re-running the declarations, not a data snapshot.

## Context.compile() / Context.load() - code images

Bytecode caching / fast startup / shipping code across processes. Real C work in `_pyqjsng.c`.

- `compile(code, *, filename='<compiled>', module=False, strip_debug=False) -> bytes`:
  `JS_Eval` with `JS_EVAL_FLAG_COMPILE_ONLY` (global or module type), then `JS_WriteObject` with
  `JS_WRITE_OBJ_BYTECODE | JS_WRITE_OBJ_STRIP_SOURCE` (plus `STRIP_DEBUG` opt-in).
- `load(blob)`: `JS_ReadObject` with `JS_READ_OBJ_BYTECODE`; for a module value, `JS_ResolveModule` then
  `JS_EvalFunction` (module evaluation yields a promise, mirroring `eval(module=True)`); for a bytecode function,
  `JS_EvalFunction` directly.
- Security posture: a *separate, visibly distinct* API - never a flag on `deserialize()`. Upstream SECURITY.md is
  explicit that the bytecode format does not resist a hostile producer; loading adversarial bytecode is memory
  corruption. Docstrings must say 'trusted input only'. Data-only `deserialize` stays the safe default.
- Blocker/limitation: the binding installs no module loader (`JS_SetModuleLoaderFunc` is unset), so a module blob
  whose imports need resolving will fail at `JS_ResolveModule`. Scope v1 to import-free scripts/modules, or design
  the loader hook first (a Python callback loader is its own feature with its own reentrancy story - the trampoline
  pattern from `qjs_call_python` applies).
- Cache-key guidance for users: key on the extension build itself (any om release/rebuild may change `BC_VERSION`,
  atoms, opcodes). `QJS_VERSION` alone is *not* sufficient - the local-patch state matters too.
- Tests: compile once / load into many fresh contexts; module blob (promise result, pending-jobs settle);
  strip-source actually strips (blob size or error-stack spot check); corrupt-blob rejection; loading a data blob
  via `load` and a bytecode blob via `deserialize` both fail cleanly.

## Misc

- `Context(with_std=True)` installs `qjs:std`/`qjs:os` but nothing drives the libc event loop (`js_std_loop`), so
  `os.setTimeout` callbacks never fire and `os.Worker` is untested. If a real need appears, add an explicit
  `Context.run_std_loop()`-style entry point (with the interrupt/deadline machinery applied) rather than driving it
  implicitly.
- Upstream the `JS_ReadRegExp` / `BC_add_object_ref` fix (the patch is PR-shaped; reproducer distills from
  `tests/test_serialize.py`). When a future vendor-pull brings the upstream fix, resolve the conflict by dropping
  the local patch - the regression tests keep guarding either way.
- Keep the SAB flags disabled permanently: 'serialized' SharedArrayBuffers embed a live host pointer and are only
  meaningful in-process with a SAB allocator installed.
- Possible small gap: only `Object` handles serialize; a bare primitive cannot (workaround: wrap in an
  array/object). Add `Context.serialize(value)` only if a real use appears.
- A live-heap snapshot (closures, pending promises, mid-await coroutines) remains out of scope - the engine has no
  serializable representation for it. If resume-mid-execution semantics are ever truly needed, the answer is
  application-level event sourcing/replay, not engine snapshots.
