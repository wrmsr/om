# astvm — a first, closed-object-space AST interpreter

A single-file, pure-standard-library implementation, paired with a standalone pytest suite.
The runtime imports no `om` modules. The guest runs on explicit AST continuations, not generated
Python functions, native Python generators, or a guest bytecode instruction set.

**Status:** experimental implementation, not an audited security boundary and not a complete
Python implementation. The target is a substantial synchronous Python subset with selected 3.14
semantics. Actual validation in the development environment used **CPython 3.13.5**, not 3.14.
The delivered suite has **461 passing cases and 2 version-gated skips** in that environment.
The final branch-enabled coverage run measured 90.36% statement coverage and 82.36% branch coverage of `astvm.py`.
Those skipped cases require the 3.14 parser/annotation oracle. Run the suite on your 3.14 installation
before integrating it; the manual deferred-annotation tests do run on 3.13.

## Files and running the tests

Keep `astvm.py` and `test_astvm.py` in the same directory. Pytest is a **test-only** dependency.

```sh
python3.14 -m pytest -q test_astvm.py
```

`TEST_RESULTS.txt` records the actual development runner and test results. Only the two `.py` files
are needed to use and test the implementation; this document is not loaded at runtime.

The test suite's CPython-oracle helpers use native `exec`/`eval` on fixed or deliberately generated
**trusted test fixtures**. They are not sandbox APIs and must not be used with untrusted input.
The implementation module itself does not execute source with native `exec`, `eval`, or `compile`.
It uses `ast.parse` and `symtable.symtable` as frontends, without producing executable guest code objects.

## Quick example: generator state really rolls back

```python
import astvm

vm = astvm.Interpreter()
vm.execute('''
def counter():
    value = 0
    while True:
        increment = yield value
        value += 1 if increment is None else increment

g = counter()
''')

assert vm.evaluate('next(g)') == 0
checkpoint = vm.checkpoint()

assert vm.evaluate('g.send(10)') == 10
vm.restore(checkpoint)
assert vm.evaluate('g.send(3)') == 3
```

This restores the generator's suspended expression and control state, not merely a dictionary
containing its name. The suite also checkpoints in the middle of active execution, including
nested cleanup and delegation.

For single-stepping, `start(source)` installs a program, `step(count)` advances it and reports whether
execution is done, and `run()` completes it. A step is a machine-continuation step, not necessarily
one source line or one charged unit of work. Checkpoints are allowed between steps, not inside a
capability callback.

## Implemented language surface

### Values and expressions

Exact scalar values (`None`, booleans, integers, floats, complex numbers, strings and bytes), guest
lists, tuples, dictionaries, sets, frozensets, ranges and slices. Literals, unpacking, subscription,
slices, ordinary arithmetic and bitwise operations, comparisons, membership, short-circuiting,
conditional expressions, assignment expressions, f-strings, comprehensions and generator expressions.

The builtin and method sets are explicit in `ObjectSpace._FUNCTION_NAMES` and `ObjectSpace._METHODS`.
They include common collection operations, `sorted`, `min`/`max`, `sum`, `all`/`any`, `enumerate`,
`zip` including its strict form, `map`, `filter`, and `reversed`. They are deliberately not an
implicit export of native Python builtins. Some signatures and protocols remain restricted.

### Statements, functions, and cleanup

Assignment, augmented assignment, deletion, `if`, `for` and `while`, loop `else`, `break`, `continue`,
`return`, assertions, raising and handling guest exceptions, exception chaining, `try`/`except`/`else`/
`finally`, and single or nested `with` statements.

Functions and lambdas support lexical closures, recursion, `global`, `nonlocal`, positional-only and
keyword-only arguments, defaults, `*args`, `**kwargs`, and guest decorators. Binding is analyzed
before execution rather than implemented as an unrestricted outward dictionary search.

Cleanup retains pending outcomes as data. A `finally` suite can replace a pending return or exception;
context managers can suppress exceptions; exception targets are deleted when handlers exit.

### Generators

Guest generators implement lazy body execution, `next`, `send`, `throw`, `close`, `yield from`, return
values carried by `StopIteration`, unexpected-`StopIteration` conversion, running-state checks, and
suspension inside exception handlers, `finally`, context managers and larger expressions.

The implementation accepts the instance and legacy class/value forms of `throw`. A non-`None`
explicit traceback argument to `throw` is intentionally unsupported. Tracebacks are guest data, not
native traceback objects. Generator finalization on garbage collection is not implemented; use
explicit `close` where cleanup matters.

### Minimal classes

Class bodies, construction, instance attributes, method binding, single inheritance, guest exception
subclasses with custom initialization and fields, `staticmethod`, and `classmethod`. Useful special
methods are dispatched through the guest machine, including truth/length, iteration, subscription,
operators, representations and context management.

No metaclasses, multiple inheritance, `super`, descriptors/properties, builtin-container subclassing,
custom attribute-lookup hooks, `__new__`, finalizers, weak references or slots. Private-name mangling
and full class/function introspection are not implemented. Do not assume unsupported data-model
protocols are emulated just because defining a normally named method is syntactically possible.

### Annotations and imports

Function annotations are deferred guest computations, cached after successful evaluation. Failure
is retryable. Basic module/class annotation collection is included; local variable annotations are
not evaluated. This is **not complete PEP 649/749 support**: no `annotationlib` formats, `__annotate__`
interface, generic aliases, type parameters, or future-import annotation mode. Module/class annotated
assignments are collected as they execute, not with full compiler-level conditional-annotation behavior.

Imports consult only the module mapping supplied by the host. A value may be an intrinsic namespace
mapping or `SourceModule(source, filename=...)`. Source modules execute through this interpreter with
separate globals and a guest module cache; circular imports and removal of failed initializations are
tested. There is no fallback to host imports or host `sys.modules`. Package/relative/star imports and
native extension imports are not implemented.

```python
vm = astvm.Interpreter(modules={
    'constants': {'answer': 42},
    'arithmetic': astvm.SourceModule('def square(x): return x * x'),
})
vm.execute('from arithmetic import square\nresult = square(9)')
assert vm.get('result') == 81
```

## Architecture and runtime interface

`Frontend` validates a closed set of AST nodes, performs binding analysis, and returns a reusable
`Program`. Unsupported syntax is rejected before executing that program, even in dead branches.
Parsing itself precedes AST-size validation and is part of the trusted host boundary.

`ObjectSpace` owns the guest object model. Scalars can be represented directly as exact native scalar
values; compound values use `ObjectRef`. Guest attribute lookup never means generic host `getattr` on
the implementation object. Guest functions, classes, exceptions and generators remain guest objects.
Native arithmetic/string primitives are explicit intrinsic implementations on validated operands,
not a fallback to arbitrary host-object behavior.

`Runtime` is the nominal storage interface. `DictRuntime` implements it using ordinary dictionaries,
lists and dataclass records. All guest heap changes go through allocation, replacement, item writing,
deleting or appending. `read()` lends read-only state by contract. `edit_thread()` and `edit_generator()`
are explicit write barriers that lend mutable execution records to the machine.

`Machine` drives explicit `Task` continuations and data-only execution state. Calls, operand temporaries,
loop handlers, active exceptions, cleanup outcomes and generator suspension do not live in native guest
frames. Host implementation methods still execute normally, of course. The suite runs guest recursion
beyond the host's ordinary recursive-evaluator comfort zone and checks that checkpointed execution
records contain no native functions, generators, frames or tracebacks.

The runtime extension point is storage and execution-state ownership. Alternative object-space semantics
would require further factoring; there is not yet a separate injected abstract object-space API.

### Snapshot costs and semantics

Ordinary execution **does not construct checkpoints or maintain an undo log**. The default write barriers
return the current mutable records. Tests include a runtime that rejects any implicit checkpoint request.

A requested checkpoint is a full, in-memory copy of the retained heap, thread state and module cache,
sharing immutable programs/ASTs. Restore copies it again, so one checkpoint can be reused. This has time
and memory cost proportional to the copied graph; it is not a cheap persistent root. Copying uses the
host's recursive `deepcopy` and can hit its recursion limit for sufficiently deeply nested graphs.

No logging or persistent backend is included. The suite does include a copy-on-read runtime test that
helps detect accidental writes outside the runtime interface. Future backends must maintain aliasing
between active execution records and their generator records, not merely copy each borrowed record
independently.

Restored objects retain their guest identities and aliases. Object-reference serials are never reused:
a host-held reference from a discarded future remains stale. Newly allocated objects in a replay get
fresh serials, so replay is **not promised to reproduce numeric `id()` results** for new objects.
Checkpoints belong to one runtime and are trusted embedding objects, not a serialization or interchange
format. Programs and returned checkpoint structures must not be mutated by callers.

External IO, host capability registrations and cumulative budget charges are not rolled back. Replaying
code repeats its IO. Real external resource state can consequently differ after a restore; that is
intentional, not a transaction failure.

## Explicit host capabilities

No `open`, `print`, `exec`, `eval`, `compile`, `input`, host imports or other ambient authority is granted.
Grant a callable explicitly:

```python
events = []
vm = astvm.Interpreter()
vm.grant('emit', events.append)
vm.execute("emit({'value': 42})")
assert events == [{'value': 42}]
```

Ordinary capability arguments and results are copied, exact data values. Mutable aliases and list/dict
cycles are preserved within a conversion graph. Native subclasses and arbitrary objects are rejected.
Native functions or modules cannot accidentally become guest values by being returned from a callback.
Some cyclic immutable exports are unsupported.

A `HostObject` is an explicit method table, **not a proxy that forwards attribute access**. Returning the
same `HostObject` repeatedly preserves its guest identity. Expected callback failures can be explicitly
translated with `CapabilityFailure('ValueError', 'message')`. Unexpected host failures raise
`CapabilityError` to the embedding; their native frames and exception objects never become guest data.

For context-manager methods that need to receive non-exportable guest exception/type arguments, a
trusted adapter may explicitly opt into `HostCall(..., guest_arguments=True)`. It receives opaque guest
references and exact scalars, not native versions of guest classes. Results still undergo the ordinary
closed import check. Returning a raw `ObjectRef`, host function or arbitrary native object is rejected.

A narrowly granted file facade can look like this:

```python
def open_note():
    file = open('/explicitly/authorized/note.txt', encoding='utf-8')
    handle = astvm.HostObject({
        'read': file.read,
        'close': file.close,
        '__enter__': lambda: handle,
        '__exit__': astvm.HostCall(
            lambda *guest_exception_info: file.close() or False,
            guest_arguments=True,
        ),
    })
    return handle

vm.grant('open_note', open_note)
```

This is an adaptation example, not a hardened filesystem policy. A production facade must enforce its
own resource/path/mode policy, translate expected host IO errors, bound reads **before** host allocation,
and arrange host-side cleanup on forced termination. There is no automatic capability-resource cleanup
or revocation framework. In particular, an unbounded callback can block outside cooperative guest fuel,
and a hard abort cannot rely on arbitrary guest `finally` code completing. The host embedding remains
responsible for the lifetime of real resources.

Capabilities are trusted code with real authority. They are not made harmless by registration. The VM
is single-owner, not thread-safe, and rejects callback reentry into its public execution APIs.

## Embedding API

`execute(source)` runs statements; `evaluate(source)` runs an expression and exports ordinary data.
`get(name)` and `set(name, data)` cross the ordinary data boundary. `evaluate_value`, `get_value`,
`call_value`, `resume_value`, and `export` provide the explicit guest-value interface for trusted hosts.
`call(guest_function_ref, *plain_args, **plain_kwargs)` converts data arguments and exports its result.
Generator exhaustion through `resume_value` is a `GuestError` named `StopIteration`, not a native
Python generator wrapper. `prepare` can build reusable programs; `start`, `step` and `run` control
execution. The constructor accepts `runtime`, `limits`, and `modules` keyword arguments.

A guest uncaught exception raises `GuestError` to the host, with its guest exception reference attached.
Hard budget failures raise `ResourceLimitError`; unexpected host-boundary and implementation failures
remain host failures. Hard failures during stepping poison the instance; create a new interpreter.
They are not catchable by guest `except BaseException`.

## Resource limits and security status

`Limits` controls cumulative fuel, allocation units and object allocations; per-value container/string/
integer size; guest call depth; source and AST size/depth; and conversion/recursive intrinsic depth.
Accounting is conservative and incomplete as a model of actual CPU and bytes. There are early checks
for oversized powers, shifts, repetition and formatting, and builtin iteration charges fuel.
A charged unit is not a promise of bounded wall-clock time.

This interpreter is **not audited**, and passing escape probes is not a security proof. In-process
parsing, native scalar primitives, hashing, recursive snapshot copying, implementation bugs and trusted
capability bodies remain part of its trusted computing base. There is no OS sandbox, worker-process
launcher, hard wall-clock enforcement, hard memory enforcement, or side-channel claim included here.
Use an independently restricted worker for actively hostile code and hard containment requirements.

The heap does not yet have a guest garbage collector: allocated temporary objects and program metadata
are retained for the interpreter lifetime. Cumulative limits therefore matter even for programs that
would have a small live heap under CPython. Checkpoint cost is over retained state, not only live state.

## Important remaining semantic gaps

This is not a claim of full Python 3.14 conformance. In addition to the intentional class/import/annotation
restrictions above:

* No async syntax, async generators, pattern matching, exception groups/`except*`, type statements,
  type parameters, template strings, dynamic guest compilation, or future imports.
* Nested intrinsic container equality/ordering and representations do not fully dispatch to contained
  guest instances' special methods. Top-level guest special-method dispatch is implemented. Guest
  instance hashing/custom-key protocols are not implemented. Set ordering and full dict-view protocols
  are incomplete, as are generic mapping and sequence-protocol fallbacks.
* Builtin signatures and methods are subsets: for example there is `sorted` but not `list.sort`, no
  `str.format`/`format_map` or string `%` formatting, and not every scalar conversion or builtin keyword
  form is supported. Some collection construction/error timing differs from CPython.
* Native frame/code/traceback introspection is deliberately unavailable; guest traceback metadata is
  simplified. Function custom attributes, exact `__qualname__`, full `locals()` free-variable behavior,
  private-name mangling, and numerous implementation-specific details are not complete.

These are compatibility limitations, not occasions to delegate the unsupported operation to CPython.
The current code rejects many unsupported operations explicitly; other supported subsets still have
known semantic differences as listed above. There are almost certainly further conformance bugs.

## What the tests establish—and what they do not

The suite combines differential checks against CPython for trusted fixtures, explicit expected results
for deferred annotations, deterministic generated expressions and cleanup matrices, generator protocol
checks, storage-boundary checks, checkpoint replay at multiple continuation offsets, capability and
introspection probes, source-import behavior, and adversarial resource-limit cases.

It is a useful regression baseline for the first implementation, not an exhaustive conformance suite,
a fuzzer campaign, a formal proof, or an independent security review. Two 3.14-specific cases remain
unrun in the development environment; no result is being represented as a Python 3.14 test run.
