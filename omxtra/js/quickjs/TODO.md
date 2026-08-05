# TODO

Remaining work for the save/restore ('snapshot') feature.

## Current state

The engine's binary serializer is exposed data-only: `Object.serialize() -> bytes` and `Context.deserialize(blob)`,
both hardwired to the `REFERENCE` flags (never `BYTECODE`, never `SAB`). Round-trip, error-path, and cross-context
clone/fan-out tests live in `tests/test_serialize.py` and `tests/test_clone.py`, and pass on both the default and
freethreaded builds. `_quickjs/quickjs.c` carries one local patch (`@om-local-patch` in `JS_ReadRegExp`) fixing the
upstream reference-desync bug; `tests/test_serialize.py` holds its regression tests.

Blobs are version-locked: valid only for the exact vendored engine build that wrote them (the format's `BC_VERSION`
byte plus build invariants the byte does not cover - opcode numbering, the predefined-atom table, the libregexp
bytecode format). They are caches and transfer envelopes, not archives.

## Context.snapshot() / Context.restore() - data snapshots of user globals

Convenience pair capturing the *user-defined* globals of a context and grafting them onto another (usually fresh)
context. Together with code images (below) this is the template-clone story: template = code image + data snapshot.

- Semantics: snapshot = own enumerable string-keyed properties of `globalThis`, minus a pristine-context baseline
  key set, packed into a plain object and serialized. Restore = deserialize + `Object.assign(globalThis, obj)`.
  - On a fresh context the engine's own globals are non-enumerable, so `Object.keys(globalThis)` is already almost
    exactly the user set - but diff against a baseline anyway rather than assuming.
  - Baseline: computed from a throwaway `Context()`, cached process-wide (`lang.cached_function`, not module-body
    work).
- Suggested implementation: pure Python over the existing primitives, in a new `snapshots.py` module in this package
  (functions taking a `Context`; no new C). Build the diff object JS-side via one `eval`, serialize it, done.
- Policy decision needed for non-serializable globals (functions, promises, class instances - and every Python
  callable registered via `set()`, which are host objects):
  - Proposed: strict by default (raise, naming the offending keys), with an opt-in skip mode that returns the
    skipped names alongside the blob. Functions-as-state is exactly what the engine cannot express - user code
    should persist as a code image and be re-run, and Python callables must be re-registered after restore.
- Known limits to document (inherited from the engine serializer): prototypes/class identity not preserved
  (everything rehydrates as plain objects), unique `Symbol()` identity lost (only `Symbol.for()` re-interns),
  non-enumerable and symbol-keyed properties silently dropped, accessors throw. Mutations *to* builtins (e.g. a
  patched `Math.random`) are invisible to the diff and will not be captured.
- Tests: round trip incl. shared refs across separate globals; strict-mode raise on a function/host callable;
  skip-mode reporting; restore onto a non-fresh context (collision policy: last-write-wins via assign - assert it);
  compose with a code image once those exist.

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
