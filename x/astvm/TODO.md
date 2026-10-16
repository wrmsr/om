# ASTVM TODO

Roadmap for the first-cut, closed-object-space Python AST interpreter. The implementation remains in
[`astvm.py`][implementation], with regression tests in [`test_astvm.py`][tests]. These are proposed work items,
not claims that the corresponding features already work. An item can extend an existing feature rather than
introduce it from scratch. IDs are stable references for dependencies; the ordering within each horizon is
roughly by priority, not a requirement to finish every earlier item before starting another.

## Architectural commitments

Keep the runtime pure stdlib, independent of `om`, and initially self-contained. Use PyPy's object-space and
interpreter-level/application-level distinctions where useful, while retaining an AST continuation machine:
no guest bytecode, no JIT requirement, no native guest functions or generators, and no fallback to arbitrary
host-object behavior. Exact host scalar primitives may remain explicitly selected implementation details.
Guest heap identity stays behind `ObjectRef`; guest execution stays in data records. Storage backends own
mutations, and the default mutable backend must not pay for an undo log or persistent snapshots it did not
request. See the [PyPy object-space overview][pypy-object-space] for the architectural inspiration.

Execution rollback is a goal. External-effect rollback is not: restored execution can repeat real IO, but
cannot undo a write, reopen a closed resource, rewind a real file offset, or retract output. Capability
authority and cumulative security budgets do not rewind with guest state. Async support means guest
coroutines and awaitable protocols, **not running asyncio**, and does not require an event loop in the core.
Introspection must expose guest objects and metadata, never native frames, callbacks, or implementation
records. Prefer documented language semantics over reproducing accidental CPython allocation identities.

The [README][readme] and [validation record][results] describe the starting point. The recorded full-suite
validation used CPython 3.13.5, not 3.14. Targeted probes while preparing this roadmap also used 3.13.5 and
confirmed the NaN comparison, `dict(None)`, numeric-method, intrinsic-key, keyword-argument, and floating
summation gaps called out below. No new Python 3.14 validation is implied.

## Near term — make ordinary Python dependable

- [ ] **N01 — Add a real, initially simple guest garbage collector.** Start with an iterative, non-moving,
  stop-the-world mark-and-sweep collector over the runtime-owned object graph. Collect at explicit safe points
  between complete machine steps, not halfway through borrowed mutable records or host capability calls.
  Enumerate references from globals, builtins, module state, active frames and continuations, operand stacks,
  closures, deferred annotations, exceptions, and reachable suspended generators. The collector must understand
  references embedded in every state record, not just collection payloads. Acceptance tests should force a
  collection between continuations and repeatedly create and discard cyclic containers, functions, and
  generators without growing the live heap indefinitely. Do not couple this first collector to guest
  `__del__`, weakref callbacks, or implicit generator cleanup; those arrive in M11/M12, with explicit `close()`
  remaining important in the meantime.

- [ ] **N02 — Define roots, handle ownership, and metadata retention.** Add explicit embedding roots or
  pin/unpin handles so a host-held guest function, result, or exception cannot silently become stale merely
  because it is absent from guest globals. Specify the distinction between an unrooted `ObjectRef` token and
  a retained handle. Account separately for checkpoint-owned graphs: a copied checkpoint must retain its own
  objects and programs without unnecessarily rooting every corresponding object in the current heap. Audit
  `Interpreter._programs`, `ObjectSpace._scalar_identities`, capability identity caches, and callback registries
  for lifetime-long retention. Preserve stable identities for live objects and never reuse reference serials
  from discarded futures. Test releasing the last host root, dropping checkpoints, retaining a generator only
  through a host handle, and collecting metadata after repeated `execute()`/`evaluate()` calls.

- [ ] **N03 — Separate live-memory limits from cumulative work limits.** GC alone will not make long-running
  instances practical while `Budget.objects` and allocation units only increase. Retain monotonic execution
  fuel and cumulative-allocation limits as separate protections, but add explicit live-object/live-storage
  accounting that collection and deletion can reduce. Include namespace entries, execution records, temporary
  intrinsic buffers, program metadata, and checkpoints rather than counting only obvious heap containers.
  Restoring a checkpoint must recompute or restore live-state accounting without refunding cumulative work.
  Audit preflight bounds for arithmetic, formatting, decoding, copying, and collection construction, and charge
  loops inside intrinsics. Demonstrate bounded live memory during allocation churn, predictable rejection of
  oversized single operations, and inability to evade quotas by collecting or restoring repeatedly. These
  remain conservative limits, not promises of exact byte accounting or wall-clock enforcement.

- [ ] **N04 — Fix small semantic errors before expanding the language.** Add targeted regressions for
  confirmed first-cut mismatches: a NaN compared directly with itself currently compares equal; `dict(None)`
  creates an empty dictionary; and `{}.update(None)` silently succeeds. Distinguish missing arguments from
  actual `None` using a dedicated sentinel, and distinguish ordinary scalar equality from container identity
  shortcuts. Audit constructor and builtin signatures systematically, including keyword-only and positional-only
  forms and 3.14's `map(..., strict=True)`. Also address the floating `sum([1e16, 1.0, -1e16])` discrepancy without
  materializing arbitrary iterators or delegating guest callbacks to host code. Give 3.14 numeric reductions
  their own oracle tests. This work should fix incorrect results and accepted-invalid calls, not merely add
  more builtin names. Reference: [Python builtins][py-builtins].

- [ ] **N05 — Make compound intrinsic operations resumable and protocol-correct.** Replace recursive shortcuts
  in `ObjectSpace.equal`, `compare`, and `representation` with explicit continuation state wherever an operation
  can traverse an unbounded graph or invoke guest behavior. Nested list/tuple/dictionary comparisons and
  representations must dispatch to contained guest objects through the same machine as top-level operations.
  Preserve recursion guards, identity shortcuts in the appropriate container contexts, exception timing, and
  side effects from comparison or representation methods. Include cyclic and deeply nested graphs, methods
  that mutate the traversed container, and comparison results requiring guest truth conversion. Checkpoint and
  collect in the middle of these operations. Do not solve the problem by increasing host recursion limits,
  wrapping guest objects in host comparison proxies, or treating every recursive comparison as equal.

- [ ] **N06 — Fill out the basic numeric, text, and binary value surface.** Add the small operations that make
  an otherwise supported primitive usable: integer helpers and byte conversions, float helpers, complex
  `real`/`imag` and conjugation, ordinary string padding and translation helpers, bytes operations, and basic
  `bytearray` construction and mutation. The current absence of `(5).bit_length()` and `(1+2j).real` should become
  regression examples. Add `str.encode`, `bytes.decode`, and their constructor forms through a deliberately
  bounded codec interface, not arbitrary host codec/error-handler registration. Start with common encodings
  and document the supported set. Every mutable binary payload needs runtime-owned identity and write barriers;
  full buffer views can wait for M18. Include Unicode failures, output-size preflight, constructor edge cases,
  and mutations observed through aliases. Reference: [builtin types][py-types].

- [ ] **N07 — Finish intrinsic dictionary, set, and view semantics.** Expand the existing types before requiring
  user-defined class machinery: `dict.fromkeys`, set/frozenset methods and comparisons, dictionary-view
  membership and set operations, and correct ordering and replacement behavior. Add supported intrinsic
  hashable keys currently rejected, including ranges and slices with hashable components; test hash/equality
  consistency rather than matching CPython's exact numeric hash values. Exercise mixed numeric keys, repeated
  NaNs, duplicate keys, frozensets, and nested tuples. Keep views live rather than replacing them with snapshots,
  and avoid assuming values views have keys-view semantics. Preserve the original stored key when equal-key
  replacement requires it. Full guest-defined `__hash__`/`__eq__` key support belongs to M06; the initial fixes
  should nevertheless leave a clean path to that implementation.

- [ ] **N08 — Implement the small protocol bridges everyday objects need.** Make existing minimal classes
  useful with ordinary builtins by adding a shared guest `__index__` conversion path and routing indexing,
  slicing, ranges, repetition, and relevant numeric helpers through it. Implement the sequence-iteration
  fallback using indexed `__getitem__`, reversal fallbacks where applicable, and the mapping protocol needed
  by `dict`, `update`, unpacking, and keyword expansion. Keep the different requirements of these callers
  explicit: accepting an iterable of pairs is not the same operation as accepting a keyword mapping. Validate
  results and propagate guest errors rather than coercing them through host objects. Optional length hints
  must never authorize unchecked allocation. This is near-term protocol completion on today's classes, not a
  prerequisite to implement the entire descriptor or metaclass system.

- [ ] **N09 — Audit iterator mutation, exhaustion, and partial-progress behavior.** Strengthen list, mapping,
  set, view, and adapter iterators so their behavior is not accidentally defined by copied host key lists.
  Track the structural information required for the supported mutation semantics, including changes that
  leave container size unchanged, without promising behavior the language leaves unspecified. Test live view
  values, sticky exhaustion, self-extension, aliasing between adapters, exception recovery, and the exact
  inputs consumed before `zip`/`map` failure. Check iterable constructors and mutation methods for unintended
  eagerness and all-or-nothing behavior: a failed operation may have already consumed input or changed its
  target. Restore checkpoints halfway through that progress. Avoid adding hidden native iterators that would
  make iterator position or invalidation state impossible to restore.

- [ ] **N10 — Add `list.sort` and replace the insertion-based sorting path.** Reuse a guest-aware stable sorting
  engine for `sorted` and in-place list sorting. The first cut inserts each decorated result into an output
  list in `_task_sort_search`; replace that growth pattern with a sensible bounded-space merge-based or similar
  implementation, while keeping comparisons, key calls, and intermediate merge state visible to the machine.
  Compute keys once, preserve stability under reverse sorting, and document the treatment of mutation and
  exceptions during callbacks. Do not promise CPython's exact comparison schedule. Test aliased list identity,
  partially completed sorts, budget exhaustion, and restore during key extraction and merging. Benchmark several
  input sizes and distributions to establish that the implementation no longer suffers avoidable quadratic
  element movement on ordinary sorts.

- [ ] **N11 — Complete ordinary formatting without introducing an escape hatch.** Add string `%` formatting,
  `str.format`, and `format_map`, and round out the existing `format`/f-string path. Parse replacement-field
  traversal and perform every attribute lookup, item lookup, conversion, and `__format__` call through guest
  operations; never hand a guest wrapper to host formatting and let native lookup take over. Keep parsing and
  expansion state explicit where callbacks or large output are possible. Bound widths, precision, nesting, and
  total output before expensive allocation. Test nested fields, escaped braces, mapping failures, conversion
  ordering, recursive guest formatting, and checkpointing inside a formatting callback. This is ordinary string
  formatting only: template strings remain intentionally deferred to L04.

- [ ] **N12 — Audit lexical binding and evaluation order against real examples.** Expand the existing frontend
  analysis around comprehensions, assignment expressions, nested closures, deleted cells, `global`/`nonlocal`,
  exception-handler targets, and names bound in unreachable branches. Check defaults, decorators, unpacking,
  chained assignments, and augmented-assignment targets for correct evaluation counts and ordering. Complete
  ordinary `locals()` behavior, including free variables and comprehension interactions, without confusing a
  locals snapshot with the runtime's actual storage dictionary. Preserve class-scope distinctions already
  needed by minimal classes; private-name mangling follows in M01. Add small side-effect trace fixtures rather
  than checking only final values, and rerun them across checkpoints and collection. Use the
  [execution model][py-execution] as the semantic contract; do not let accidental host scope behavior decide it.

- [ ] **N13 — Strengthen existing exceptions, generators, and context-manager cleanup.** Treat these as
  implemented features needing edge-case closure, not a second implementation. Extend the unwind matrices
  across nested `finally`, suppressing and raising `__exit__`, generator delegation, `send`/`throw`/`close`,
  reentrancy, invalid yielded-on-close behavior, and return values from closing generators. Exercise both
  exceptions replaced by cleanup and exceptions preserved through suspension. Ensure exception target cleanup,
  active exception state, and pending outcomes survive collection and restore. Add useful guest filename,
  line/column, and chained-error diagnostics without retaining native tracebacks. Keep forced budget termination
  separate from guest exception unwinding, with no promise that unbounded guest cleanup will finish. Full
  traceback objects and GC-triggered generator finalization are later work; the explicit protocol must already
  be dependable. Reference: [generator semantics][py-expressions].

- [ ] **N14 — Make ordinary checkpoints bounded, non-recursive, and precisely owned.** Replace the generic
  recursive `deepcopy` path with an explicit graph copier for known runtime records. Preserve cycles, aliases,
  active-generator/execution sharing, and immutable program references without invoking arbitrary host copy
  hooks. Add limits and accounting for checkpoint creation and restoration, including failure before excessive
  allocation, and avoid leaving a partially restored runtime on failure. Document reusable checkpoints,
  foreign-runtime rejection, stale references from discarded futures, and the interaction with host roots and
  GC. Protect or clearly encapsulate checkpoint internals instead of relying on callers not to mutate exposed
  record graphs. The default checkpoint can still be an O(live-state) copy; a persistent backend is not needed
  to fix these correctness and reliability issues.

- [ ] **N15 — Establish a genuine Python 3.14 conformance baseline.** Run the full suite on the target interpreter
  and replace version-gated uncertainty with recorded results. Add deterministic generated programs and focused
  oracle fixtures for every near-term item, comparing results, exception types, mutation traces, iterator
  consumption, and generator outcomes. Exercise multiple hash seeds and both normal execution and forced
  checkpoint/GC schedules. Keep compatibility differences explicit, distinguishing Python guarantees from
  CPython-specific details and resource-policy differences. Native `exec`/`eval` must remain confined to trusted
  test fixtures; fuzz inputs used with the CPython oracle need an independently bounded test worker. Preserve
  zero runtime dependencies, keep pytest test-only, and make reproductions small enough to become permanent
  regression cases rather than relying on a coverage percentage.

- [ ] **N16 — Tighten boundary contracts and abort/resource lifetime handling.** Audit every capability argument,
  return value, exception translation, host-object method table, and export/import path for alias handling,
  foreign references, subclasses, and accidentally exposed implementation objects. Add explicit embedding
  teardown for capability resources and a documented invalidation mechanism for handles whose external resource
  has closed; keep that outside guest rollback. Test failure during conversion, callback attempts at reentry,
  and hard abort while a guest context manager is active. Clarify which source/program/checkpoint inputs are
  trusted and which are validated. Maintain adversarial tests and a concrete outer-worker isolation contract
  for hostile deployments: parser/native primitive failures and blocking callbacks are not contained by guest
  fuel alone. Do not market passing probes as an independent security audit.

- [ ] **N17 — Measure and remove obvious default-path overhead.** Build a small stdlib-driven benchmark/profile
  harness for loops, function calls, container operations, generator delegation, exception cleanup, repeated
  evaluation, and checkpoint-heavy workloads. Separate dispatch cost, temporary allocation, retained metadata,
  and snapshot cost, and report scaling instead of one aggregate slowdown number. Optimize demonstrated
  problems such as unnecessary container materialization, repeated metadata walks, redundant method wrappers,
  and avoidable continuation churn. Keep checkpoints, tracing, history, and expensive invariant checks opt-in;
  retain a test runtime that rejects implicit checkpointing. Add a defensive copy-on-read/debug runtime to
  broader tests so speedups cannot silently bypass storage ownership. Do not trade away data-only execution,
  safepoints, or guest protocol dispatch for a faster but non-restorable host call stack.

## Mid term — a useful object model and bare async machinery

- [ ] **M01 — Implement private-name mangling and complete lexical class metadata.** Perform name mangling in
  the frontend using the correct lexical class context, covering attribute names, parameters, relevant bindings,
  nested scopes, annotations, and class names with leading underscores. Keep nested-class contexts distinct
  and do not mangle strings passed to `getattr` or other runtime APIs. Build accurate class/function qualified
  names and the class-cell infrastructure required by `__class__` and zero-argument `super`. Test methods,
  comprehensions, nested functions, nested classes, and source-module boundaries together, not only direct
  `self.__field` assignments. Preserve immutable analyzed program metadata so these rules do not become
  repeated runtime work. This is a compiler/frontend correctness feature even though its primary beneficiaries
  are classes; dynamic source strings must receive their own appropriate compilation context.

- [ ] **M02 — Add descriptors, properties, and custom attribute access.** Introduce guest descriptor dispatch
  with the correct ordering between data descriptors, instance dictionaries, and non-data descriptors. Build
  `property` on that mechanism, and expand `staticmethod`/`classmethod` consistently instead of accumulating
  unrelated lookup exceptions. Implement guest `__getattribute__`, `__getattr__`, `__setattr__`, and `__delattr__`
  through resumable operations, including a usable base-object path that custom hooks can delegate to without
  recursing forever. Cover descriptor exceptions, deletion, inheritance, and class-versus-instance access.
  Lookups may execute arbitrary guest code, mutate the class, or be interrupted by a checkpoint; store their
  intermediate state accordingly. Do not use host descriptors or forward attribute access to the native
  dataclasses that happen to represent guest objects. Reference: [the data model][py-data-model].

- [ ] **M03 — Complete ordinary class construction without custom metaclasses.** Implement the allocation and
  initialization stages around guest `__new__` and `__init__`, including constructors that return a different
  object and the resulting initialization rules. Add `__set_name__` and `__init_subclass__` support, class-body
  metadata initialization, and correct ordering relative to descriptors and class decorators. Keep normal
  `object`/`type` behavior intrinsic for now rather than quietly enabling arbitrary metaclass execution.
  Checkpoint partway through construction and test failed initialization, inherited hooks, custom exceptions,
  constructor argument forwarding, and objects whose initialization makes them reachable before completion.
  Ensure partially constructed objects remain ordinary GC-managed guest state. These hooks cover many common
  class-customization use cases before L01's full metaclass work. Reference: [PEP 487][pep-487].

- [ ] **M04 — Add multiple inheritance, C3 lookup, and `super`.** Replace single-base `ClassData` assumptions
  with explicit base tuples and a validated method-resolution order. Implement both explicit and zero-argument
  `super`, using frontend-created class cells rather than searching native frames. Support cooperative methods,
  diamonds, inherited constructors, classmethods, descriptor access through `super`, and rejection of
  inconsistent hierarchies. Expose the resulting guest bases and MRO through the introspection model, and make
  lookup caches respond correctly to class-dictionary mutation and restore. Keep arbitrary post-creation base
  replacement and exotic mixed builtin layouts explicitly unsupported until their invariants are implemented.
  This item should make ordinary mixins practical, not require reproducing CPython's physical instance layout
  or completing custom metaclasses first.

- [ ] **M05 — Complete class special-method overrides consistently.** Unify implicit special-method lookup,
  reflected operators, in-place operators, rich comparisons, conversion hooks, callability, containment,
  iteration, reversal, formatting, and context-manager protocols. Make lookup follow the guest type rules
  rather than ordinary instance attribute lookup; a same-named attribute should not accidentally override
  every implicit operation. Test subclass precedence, `NotImplemented`, missing methods versus methods set to
  `None`, non-boolean comparison results, and return-type validation. Extend dispatch to every applicable
  builtin, including less common numeric hooks, without duplicating subtly different fallback logic. Use
  mutation/version guards for any optimized method caches, including after restore. N05/N08 handle the
  immediate container and conversion holes; this item completes the general class-level contract.

- [ ] **M06 — Support guest-defined dictionary and set keys.** Implement resumable hash-table operations that
  can call guest `__hash__`, `__eq__`, and truth conversion without hiding execution inside native dictionary
  callbacks. Handle default identity hashing, deliberately unhashable classes, hash/equality inheritance rules,
  collisions, cross-type equal keys, and exceptions or table mutations during comparison. Retain a fast path
  for proven intrinsic keys where it preserves the same semantics. Represent pending probes and mutation
  checks as execution data so collection, interruption, and restore remain valid during a lookup. Preserve
  dictionary ordering and existing-key identity independently of the chosen hash-table layout. Test adversarial
  collision workloads under fuel limits, self-mutating equality methods, nested lookups, and tuple/frozenset
  keys containing guest instances. Never introduce a native wrapper whose `__hash__` runs guest code.

- [ ] **M07 — Provide useful, exclusively guest introspection.** Add ordinary function attributes, defaults,
  keyword defaults, names, qualified names, module metadata, custom attribute dictionaries, bound-method
  `__self__`/`__func__`, closure cells, and guest globals/builtins access. Complete `dir`, `vars`, class and
  instance dictionaries, bases, MRO, and suitably read-only namespace views. Route writable metadata through
  runtime mutations and explicitly specify which views are live. Expose source/AST metadata rather than
  inventing native code objects or a `co_code` compatibility promise. Test traversal from every exposed
  object to ensure it never reaches host callbacks, modules, frames, or implementation classes. A read-only
  metadata wrapper can still contain authority-bearing references, so validate its entire reachable guest
  graph, not just whether direct assignment to the wrapper is prohibited.

- [ ] **M08 — Improve exception objects, guest tracebacks, and debugging views.** Expand exception attributes,
  notes, chaining, and traceback manipulation beyond the current simplified metadata, with guest-only
  representations for any frame or traceback information exposed. Add source-oriented stepping, stack views,
  and optional event hooks that observe the machine without requiring native frames or bytecode offsets.
  Define whether each debugger view is a snapshot or a live rooted handle, and keep captured frames from
  accidentally retaining every completed computation forever. Add guest traceback validation for APIs such as
  generator throwing and exception traceback replacement before accepting those values. Preserve pending
  exception state through checkpoints, and ensure debugging is opt-in with low disabled-path cost. Rich
  diagnostics must not turn the introspection API into unrestricted access to runtime records.

- [ ] **M09 — Add `__slots__` and enforce guest instance layouts.** Represent slotted storage explicitly, with
  slot descriptors and the appropriate presence or absence of instance dictionaries and weak-reference
  support. Handle inheritance, private slot-name mangling, duplicate/conflicting declarations, and layout
  conflicts under multiple inheritance. Enforce attribute restrictions through all mutation paths, including
  `setattr`, descriptors, introspection views, and restored state; do not merely optimize storage while leaving
  a hidden unrestricted attributes dictionary. Test mixed slotted/unslotted inheritance and deletion or
  reinitialization of slot values. Slot references must be visible to GC and every slot write to the storage
  backend. Prioritize language behavior over matching CPython's byte layout or promising memory savings before
  the record representation has been measured.

- [ ] **M10 — Support useful builtin subclassing within the guest object model.** Add a deliberate path for
  subclasses of containers and selected immutable primitives, starting with common `list`, `dict`, `tuple`,
  `str`, and numeric cases rather than arbitrary combinations of builtin layouts. Separate intrinsic payload
  storage from guest class identity and instance attributes; an integer subclass, for example, cannot simply
  disappear into an exact native integer without losing its overrides. Integrate allocation through guest
  `__new__`, builtin method descriptors, reflected-operation precedence, and the correct result types of
  inherited operations. Test explicit base-method calls as well as implicit operators, with aliases and
  checkpoints across mutations. Reject unsupported layout combinations explicitly. No host subclass or
  operator proxy should become the implementation shortcut for invoking guest behavior.

- [ ] **M11 — Add guest finalization, including abandoned-generator cleanup.** Extend the collector with explicit
  pending-finalization state and run guest `__del__` and generator closing through the normal machine at
  controlled safe points, never from native object destructors. Handle cycles, resurrection, callback errors,
  repeated collections, and interpreter shutdown with documented semantics and bounded work. Record completed
  and pending finalization as guest execution state so checkpoint/restore can reproduce the corresponding
  guest history; external effects performed by a replayed finalizer remain real and irreversible. Do not
  promise immediate CPython-style reference-count timing, and do not rely on guest finalization to release
  host resources after a forced abort. Coordinate ordering with M12 and keep resurrected objects valid under
  subsequent collections. Reference: [PEP 442][pep-442].

- [ ] **M12 — Add guest weak references and weak containers.** Implement weak references as runtime-recognized
  non-owning edges, not native weakrefs to `ObjectRef` wrappers or payload dataclasses. Define callbacks,
  cleared-target access, equality/hash behavior, weak methods, and then useful weak containers in terms of
  guest identity and collection state. Keep weakref callbacks as scheduled guest work, and coordinate their
  ordering with finalization and resurrection. Test cycles involving callbacks, weak references to slotted
  instances, and targets retained only by embedding pins. A checkpoint can preserve a target in its own graph
  without making that target live in every other timeline; restoring must restore weak-reference state
  consistently. Do not implement ephemeron-like reachability rules by accident or pretend native weakref
  support supplies the required semantics. Reference: [weak-reference documentation][py-weakref].

- [ ] **M13 — Finish deferred annotations and support ordinary annotation values.** Complete the function,
  module, and class annotation behavior beyond v1's execution-time collection of annotated assignments.
  Implement annotation scopes, conditional declarations, cache invalidation and replacement, retry after
  failure, the `__annotate__` interface, and deliberately supported annotation inspection formats. Honor
  `from __future__ import annotations` as a distinct mode. Provide simple guest generic-alias and union values
  so common annotations such as `list[int]` and `int | None` do not require the advanced type system first;
  elaborate type parameters and aliases remain L02. Preserve deferred computations and their caches across
  GC and restore, including annotation expressions that call guest functions. Keep forward-reference handling
  explicit rather than silently converting every failed evaluation into a string. Reference: [PEP 749][pep-749].

- [ ] **M14 — Make guest source imports useful for multi-file programs.** Extend the current explicit module
  provider to packages, parent/submodule bindings, relative imports, and star imports with `__all__` handling.
  Store package metadata, initialization state, and cache entries as guest state, preserving circular-import
  and failed-initialization behavior through suspension and restore. The provider should identify permitted
  modules and sources; it must not fall back to host import hooks or infer unrestricted filesystem access
  from permission to import a name. Test packages with recursive imports, attributes shadowing submodule
  names, and module initialization that raises after publishing objects. Keep reloading, arbitrary loader
  frameworks, and native extensions out of the initial scope. Package support should make existing guest
  programs composable without changing their authority. Reference: [the import system][py-import].

- [ ] **M15 — Implement bare coroutines and the awaitable protocol.** Add guest `async def` functions,
  coroutine objects, `await`, and guest `__await__` handling using explicit continuation records. Define
  creation, first resume, suspension, sending, throwing, closing, completion, reuse errors, and reentrancy
  checks, including validation that an awaitable supplies the appropriate iterator protocol. Provide a small
  host-facing drive/resume interface with explicit suspension results; a deterministic test driver is enough.
  Do not import, emulate, or aim to run asyncio, and do not add an event loop, tasks, timers, or native
  coroutine objects as hidden runtime prerequisites. Checkpoint at nested awaits and preserve pending cleanup,
  operand state, and exception context. Resource limits remain shared across delegated guest execution.
  Reference: [PEP 492][pep-492].

- [ ] **M16 — Extend async to iteration, context managers, and generators.** Build `async for`, `async with`,
  async comprehensions, and async generators on M15's protocol machinery. Implement `__aiter__`, `__anext__`,
  `__aenter__`, and `__aexit__`, plus async-generator `asend`, `athrow`, and `aclose` awaitables with correct
  distinction between yielded values, coroutine completion, and `StopAsyncIteration`. Preserve cleanup while
  awaiting inside exits and while closing suspended async generators. Use explicit guest lifecycle hooks
  rather than native async-generator hooks or host coroutine stacks. Test nested suspension, concurrent-resume
  rejection, early loop exit, failures during awaited cleanup, and checkpoint restoration of both a generator
  and its outstanding operation awaitable. Event-loop scheduling and an asyncio compatibility layer remain
  outside the feature. Reference: [PEP 525][pep-525].

- [ ] **M17 — Add exception groups and `except*` without simplifying their semantics.** Introduce guest
  `BaseExceptionGroup`/`ExceptionGroup` trees and the splitting, subgroup derivation, matching, and recombination
  needed by `except*`. Preserve cause/context/traceback metadata while distinguishing reraised portions from
  newly raised exceptions. Extend frontend checks for handler restrictions rather than accepting invalid
  control flow and discovering it during unwinding. Keep group traversal and partially handled subgroups
  explicit for fuel accounting, GC, and checkpoints. Test mixed matching/nonmatching leaves, nested groups,
  custom group subclasses, failures inside handlers, and interactions with `finally` and coroutine exceptions.
  This does not require a task-group scheduler: exception groups are useful guest values and control flow
  independently of any particular concurrency library. Reference: [compound statements][py-compound].

- [ ] **M18 — Add guest buffer views over owned binary storage.** After N06's `bytearray`, implement a limited
  but coherent `memoryview`-like guest object whose backing store is identified by a guest reference and whose
  offset, shape, mutability, and release state are ordinary runtime data. Start with the common one-dimensional
  byte case and explicitly reject unsupported formats or layouts. Writes through a view must be visible
  through aliases and checkpoints, with proper resizing/release restrictions; do not retain a native writable
  memoryview that can bypass storage write barriers. Treat host-backed buffers as separate explicit
  capabilities rather than ordinary guest-owned memory. Test overlapping views, release, backing-object
  lifetime, restoration after mutation, and attempted resizing with live views before expanding the format
  or multidimensional surface.

- [ ] **M19 — Grow a curated application-level library, not ambient host imports.** Provide small useful
  guest modules, using application-level guest Python where the supported language suffices and
  interpreter-level intrinsics only where needed. Good candidates are focused pieces of `itertools`,
  `functools`, `operator`, `collections`, and `contextlib`, plus explicitly selected numerical helpers. Keep
  each module's scope visible rather than suggesting that supplying its name means the complete native module
  is available. Callback-driven helpers must reenter the guest machine; stateful utilities must use owned
  heap/execution records. Test representative real snippets as integration cases across class, generator,
  import, and annotation features. Avoid importing the host module wholesale or depending on source-library
  helpers that secretly compile native Python or inspect CPython bytecode.

## Long term — advanced language features and runtime experiments

- [ ] **L01 — Implement full guest metaclasses and advanced class creation.** Extend the ordinary construction
  pipeline to metaclass selection, custom namespace preparation, guest `type` construction, metaclass methods,
  and the interactions between metaclass calls and instance creation. Add non-type base resolution and other
  class-creation customization only with explicit ordering and validation. Preserve the distinction between
  instance, class, and metaclass attribute lookup and descriptor behavior. Exercise conflicting metaclasses,
  prepared namespace objects with guest side effects, and checkpoints during class construction. Dynamic base
  changes or class reassignment need separate layout/cache invariants before being accepted. None of this
  authorizes host `type`, host class creation, native descriptor execution, or a fallback to native `exec` for
  complex class bodies.

- [ ] **L02 — Support complex runtime type forms and generic scopes.** Expand M13's ordinary annotation values
  into type statements, lazy type aliases, type-parameter scopes, bounds/defaults, variadic parameters,
  parameter specifications, forward references, and the corresponding guest introspection objects. Model
  lazy evaluation and substitution as explicit guest computations where appropriate, preserving captured
  scopes and identity across collection and checkpoints. Separate runtime syntax/object behavior from
  optional type checking: this is not a plan to build mypy inside the interpreter. Add deliberate policies
  for annotation-format evaluation and invalid type operations rather than treating every subscribed class
  as interchangeable metadata. Do not make host `typing` objects or host-generated generic classes part of
  the guest graph. Use targeted source programs and version-pinned reference tests for each supported form.

- [ ] **L03 — Implement structural pattern matching.** Add `match`/`case` with literal, value, capture,
  wildcard, sequence, mapping, class, OR, and AS patterns, plus guards and the necessary binding analysis.
  Drive value lookup, equality, class matching, `__match_args__`, and attribute access through guest operations.
  Preserve side effects and exceptions without turning a pattern into an opaque host helper or accidentally
  making failed matches transactional. Identify unspecified binding/evaluation details and choose documented
  behavior rather than claiming exact CPython scheduling everywhere. Represent partially matched patterns
  as continuation data, allowing budget interruption, collection, and restore before a guard or nested
  pattern completes. Test against descriptors, inherited match metadata, unusual mappings, and recursive
  subjects. Reference: [pattern matching specification][pep-634].

- [ ] **L04 — Add template strings as guest structured values.** Implement the 3.14 template-string AST nodes
  and guest template/interpolation objects rather than translating them into f-strings. Preserve the
  distinction between evaluating interpolation expressions and later processing their stored values,
  conversion information, and format specifications. Keep construction, concatenation, iteration, and any
  supported metadata access within the object space, with bounded storage and accurate evaluation order.
  Test templates containing guest objects, nested format expressions, and deferred processing after the
  originating frame has gone away. Any renderer that performs IO is a separate granted capability; creating
  a template should not silently acquire one. This stays behind everyday formatting and annotation work,
  matching the deliberate v1 decision to reject the syntax. Reference: [PEP 750][pep-750].

- [ ] **L05 — Build an optional undo-log storage backend.** Record reversible mutations at the existing storage
  boundaries, including allocations, namespace/cell changes, container writes, module state, iterator positions,
  execution stacks, generator/coroutine records, and finalization state. Define the grouping of mutations into
  reversible steps, history truncation, nested checkpoints, and discard/replay behavior before adding a
  debugger UI. Retain the required old values as GC-visible history roots and reclaim them when history is
  dropped. Avoid copying the whole interpreter at every write merely to claim an undo log; benchmark both
  write-heavy execution and rollback. Capability authority, real IO, and cumulative security accounting remain
  outside the log. The mutable default backend must continue to work without allocating history records.

- [ ] **L06 — Build persistent and copy-on-write storage backends.** Preserve stable `ObjectRef` identity while
  mapping that identity to versioned object state, so aliases continue to observe one logical object within
  each branch. Extend persistence to execution records and pending intrinsic operations, not just globals
  and containers; explicitly preserve shared active-generator/thread records. Explore structural sharing,
  paged copy-on-write, and persistent maps/sequences under the zero-external-dependency constraint, measuring
  their tradeoffs instead of assuming constant-time checkpoints imply cheap execution. Make retained roots,
  branch disposal, stale references, and history GC explicit. Run the same semantic and restore tests against
  all backends. Checkpoint copying can remain available as a simple baseline even if a sophisticated backend
  eventually offers inexpensive forks.

- [ ] **L07 — Experiment with branching execution and advanced heap tooling.** Build object-graph inspection,
  snapshot diffs, time-travel stepping, branch-local execution, and selective state comparison on the proven
  runtime interfaces. Treat branch merging as a separate research problem: aliasing and conflicting mutations
  cannot be resolved by naively merging variable dictionaries. Explore generational/incremental collection,
  compact storage, and object-space instrumentation only after measuring workloads and stating their barrier
  requirements. Keep cross-branch handles and checkpoint-retained objects unambiguous. Branching is most useful
  for pure guest computation; externally supplied nondeterminism and repeated real IO prevent a general
  deterministic-replay promise. The goal is useful experiments without forcing their costs or representation
  choices into the default interpreter.

- [ ] **L08 — Design an explicit durable checkpoint format.** Replace trusted in-memory checkpoint assumptions
  with a versioned data-only format only when there is an actual need to save, transport, or resume execution
  across processes. Encode graph identity, program/source identifiers, record schemas, execution continuations,
  and supported runtime-version constraints without serializing native functions, frames, or Python pickle
  payloads. Load under size/depth limits and validate references and state invariants before execution.
  Capability identifiers must be rebound through an explicit receiving-host policy; serialized data must not
  manufacture authority or reset cumulative quotas. Decide what happens to pending IO-facing operations and
  unavailable programs before advertising resumability. Start with same-version, same-feature-set snapshots
  rather than promising arbitrary compatibility across interpreter revisions.

- [ ] **L09 — Develop deliberate real-IO capability adapters.** Build practical file, stream, clock, and selected
  network adapters with explicit grants, bounded operations, expected-error translation, resource ownership,
  and teardown behavior. A filesystem adapter needs real path/resource policy rather than a string-prefix
  check, and must not accidentally grant arbitrary descriptors or opener callbacks. Keep blocking execution
  and cooperative guest-await integration separate; an async adapter can suspend through M15's explicit
  protocol without putting native awaitables into guest state. **IO stays real and irreversible:** restore
  does not rewind file offsets, resurrect closed handles, retract writes, or replay a cached fake result.
  Test restored guest handles against changed external state and document resulting failures. Strong hostile
  deployments still need independently restricted workers and external termination limits.

- [ ] **L10 — Consider dynamic guest source execution, without native compilation.** Add optional guest
  `eval`/`exec`-style entry points only after namespace, scope, budget, and introspection behavior is mature.
  Parse and analyze supplied source through the same validated frontend and execute it with the same object
  space, capabilities, limits, and continuation machine. Specify how explicit namespaces and function-local
  execution interact with cells and locals snapshots, and propagate future/compiler modes deliberately.
  Newly supplied source must not bypass parser limits, source accounting, module policy, or language feature
  validation. Any guest compiled-program value would represent analyzed AST data, not bytecode or a native
  code object. This feature expands how guest programs obtain code, not the host authority they possess, and
  remains optional for embeddings that prefer a fixed program set.

## Acceptance standard for every horizon

A feature is not complete just because one happy-path snippet works. Its tests should cover values and
errors, side-effect ordering, mutation/aliasing, resource exhaustion, GC reachability, and checkpoint/restore
where applicable. Any operation capable of calling guest code must remain in the explicit machine. Every
new guest-visible value must stay within the closed object graph, and every new mutable field must have an
owner and a storage write path. Document unsupported behavior instead of filling a gap with host execution.

The near-term exit condition is a practical long-lived interpreter for ordinary synchronous code with bounded
live-state growth and dependable checkpoints. The mid-term exit condition is a useful Python object model
plus scheduler-independent async protocols. Long-term work broadens compatibility and explores alternative
state representations; it must not turn bytecode, asyncio compatibility, or external-effect rollback into
implicit requirements.

## Reference points

The [implementation][implementation], [tests][tests], [README][readme], and [recorded validation][results]
are the baseline for current-state claims. The Python references below define intended language behavior;
backend architecture, prioritization, GC safe points, checkpoint contracts, and embedding policy are design
proposals rather than claims that those documents prescribe this implementation.

[implementation]: astvm.py
[tests]: test_astvm.py
[readme]: README.md
[results]: TEST_RESULTS.txt
[pypy-object-space]: https://doc.pypy.org/en/latest/objspace.html
[py-data-model]: https://docs.python.org/3.14/reference/datamodel.html
[py-expressions]: https://docs.python.org/3.14/reference/expressions.html
[py-execution]: https://docs.python.org/3.14/reference/executionmodel.html
[py-compound]: https://docs.python.org/3.14/reference/compound_stmts.html
[py-import]: https://docs.python.org/3.14/reference/import.html
[py-builtins]: https://docs.python.org/3.14/library/functions.html
[py-types]: https://docs.python.org/3.14/library/stdtypes.html
[py-weakref]: https://docs.python.org/3.14/library/weakref.html
[pep-442]: https://peps.python.org/pep-0442/
[pep-487]: https://peps.python.org/pep-0487/
[pep-492]: https://peps.python.org/pep-0492/
[pep-525]: https://peps.python.org/pep-0525/
[pep-634]: https://peps.python.org/pep-0634/
[pep-749]: https://peps.python.org/pep-0749/
[pep-750]: https://peps.python.org/pep-0750/
