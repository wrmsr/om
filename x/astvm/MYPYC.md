**Very realistic—and the architecture is already much closer to a good mypyc target than a conventional recursive, dynamically dispatched Python interpreter would be.** But the current file is **not yet “add `mypycify()` and ship it.”** I would describe the remaining work as a moderate typing-and-compatibility pass, not a redesign of the VM.

The distinction I would make is between **getting it to compile**, **preserving its behavior—including checkpoints and uncompiled runtime subclasses—and actually getting substantial acceleration**. Those are three separate milestones.

I inspected the implementation against mypyc 2.4.0’s documentation and compiler sources. I also attempted to install the toolchain in a separate directory, but the environment’s package download failed because DNS/network access was unavailable. **I have not obtained compiler diagnostics, a successful build, or a benchmark.** The implementation and tests remain unchanged.

## 1. The important architectural decisions already fit

Most importantly, **mypy­c would compile the interpreter, not the guest program**.

Your guest functions, generators, classes, and eventual metaclasses remain records manipulated by the machine. They do not need to fit mypyc’s restrictions on the corresponding *host* Python constructs. A guest class with multiple inheritance would still be an instance of our ordinary host-side class record, not a multiply inherited native extension class. The existing `FunctionData`, `ClassData`, `Execution`, and `GeneratorData` representations already establish that separation. astvm astvm

Similarly, guest suspension already happens by retaining execution data. We would not be relying on mypyc to reproduce native Python generator-frame behavior for our guest generators.

**There is no architectural reason to introduce bytecode, native guest execution, a second interpreter implementation, or a different object model.** `ObjectRef`, the object space, the runtime write barriers, and the continuation machine can all stay.

The main qualification is that the current implementation uses those structures rather dynamically. The types describe much of the design, but do not yet express all of its invariants.

## 2. The largest immediate job is making the typing truthful and sufficiently precise

A programmatic inventory found **348 function/method definitions, all with return annotations**. That is a useful starting point, but it should not be confused with the module having passed mypy.

For example, the current task record says:

```python
class Task:
    kind: str
    env: Environment
    node: ast.AST | None = None
    data: ta.Any = None
    base: int = 0
```

Individual handlers then access things such as `task.node.elts` without establishing that the node is a list, tuple, or set expression. The association between the task tag and its node shape exists in the implementation, but not in the type system. astvm astvm

The same issue appears at the object-space boundary:

```python
def data(self, value: ObjectRef) -> ta.Any:
    ...
```

A caller may have a `Value`, check that `kind(value)` is `"tuple"`, and then call `data(value)`. That establishes the invariant for a human reading our object model, but a string returned from `kind()` does not express a static narrowing to `ObjectRef`. There are concrete examples of that pattern in exception matching. astvm astvm

There are also lifecycle invariants: `Machine._thread` is optional between steps, while `_execution()` assumes that a step is active and directly accesses its fields. astvm

I would address those with **typed helpers and local narrowing**, rather than making every payload `Any` or applying broad ignores. We do not need to turn the entire continuation representation into an elaborate generic type hierarchy immediately. A small number of carefully designed accessors would remove a lot of repetition.

### Some annotations need correction, not merely clarification

This is a particularly instructive existing example:

```python
def lookup_class(self, cls: ObjectRef, name: str) -> Value:
    while cls is not None:
        self.budget.tick()
        info = self.data(cls)
        namespace = self.data(info.namespace)
        if name in namespace:
            return namespace[name]
        cls = info.base
    return _MISSING
```

Here `cls` is annotated as an `ObjectRef`, but eventually receives `None`. Because `info` is `Any`, that assignment can hide the inconsistency from ordinary type checking. The nearby `subclass()` implementation already uses the more accurate pattern: a separate `current: ObjectRef | None` cursor. astvm astvm

That matters more under mypyc: annotations influence representation, checks, and compiler assumptions. “The type checker let an `Any` through” is not a guarantee that a variable can safely contain something inconsistent with its declared type. Mypyc explicitly requires attention to runtime type correctness, not merely silencing diagnostics. [Mypyc](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)

**My assessment:** this is a substantial number of small corrections across the module, but mostly repetitive, local work. It does not undermine the design.

I would also annotate the shared operation tables explicitly with `ClassVar`, or `Final` where appropriate. Mypyc’s class-generation code treats explicitly marked class variables differently from instance attributes; leaving all of those tables to inference is unnecessarily ambiguous for a dual-mode implementation. [GitHub](https://raw.githubusercontent.com/python/mypy/v2.4.0/mypyc/irbuild/classdef.py)

## 3. Runtime pluggability needs an explicit mypyc accommodation

This is a real compatibility issue, not just an optimization opportunity.

The existing suite deliberately creates ordinary Python subclasses of `DictRuntime`, including `CopyOnReadRuntime` and `NoSnapshotsRuntime`. That is exactly the sort of embedding behavior we want to preserve. test_astvm test_astvm

By default, a mypyc native class does not allow arbitrary interpreted subclasses. The intended mechanism is:

```python
@mypyc_attr(allow_interpreted_subclasses=True)
```

The relevant base hierarchy must opt in consistently; the compiler checks the ancestors as well. For this implementation, that means considering both `Runtime` and `DictRuntime`, not merely decorating the final class someone happens to subclass. [Mypyc](https://mypyc.readthedocs.io/en/stable/native_classes.html)

**I would preserve a normal subclassable runtime base—not make the public extension point a mypyc trait.** Interpreted code cannot subclass native traits, which would defeat the purpose here. The ordinary native default runtime can remain the optimized implementation, while Python overrides take the interoperability path. [Mypyc](https://mypyc.readthedocs.io/en/stable/native_classes.html)

This also does not require making mypy a runtime dependency. A dual-mode source can use an optional import of the real `mypy_extensions.mypyc_attr`, with an inert fallback when that package is absent. The compiler must see the decorator it recognizes during compilation; an arbitrary lookalike decorator is not sufficient. Its recognition is based on the actual qualified name. [GitHub](https://raw.githubusercontent.com/python/mypy/v2.4.0/mypyc/irbuild/util.py)

I would leave the pytest suite **uncompiled** when testing the compiled VM. Otherwise it becomes too easy to test a more restrictive environment than real Python callers will use.

## 4. Dataclasses and checkpoint copying are the biggest compatibility unknown

The module contains **34 dataclasses, 27 using `slots=True`**. They are pervasive, rather than confined to a few convenience objects.

Mypyc has native dataclass support, but its implementation is a hybrid: explicitly written methods are compiled, while methods synthesized by the dataclass decorator remain interpreted. So “this dataclass became a native class” does not mean every constructor, comparison, or other generated operation became a direct native operation. [GitHub](https://raw.githubusercontent.com/python/mypy/v2.4.0/mypyc/irbuild/classdef.py)

I would not immediately rewrite all of them. I would first run small compiled probes for the exact combinations we use:

- Frozen and slotted records, including equality and hashing.
- `dataclasses.fields()` and `dataclasses.replace()`.
- `deepcopy()` of required-argument records, shared references, and cycles.

**I cannot establish from this inspection that every current `slots=True` declaration works unchanged.** That is an import/construction smoke-test question, not a blocker I can honestly claim to have reproduced.

Checkpointing deserves particular attention. Mypyc documents additional requirements for copying native instances, including initialization and `serializable` behavior. We cannot assume that a graph copied successfully as ordinary Python will necessarily copy identically after its records become native classes. [Mypyc](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)

For this VM, the acceptance criteria are stricter than “`deepcopy()` returns something.” We need the copied graph to preserve the relationship between an active execution and its generator record, preserve `ObjectRef` ownership and aliases, and continue sharing immutable program data.

There are two reasonable directions: retain generic copying with appropriate native-class configuration, or implement explicit record copying. **I lean toward explicit copying eventually**, because it also addresses the existing recursive-`deepcopy` limitation and makes the state boundary easier to audit. But it need not be a prerequisite if a small compatibility adjustment makes the current checkpoint tests pass.

This is not a reason to add copying to ordinary execution. The current separation between the mutable fast path and explicitly requested checkpoints should remain.

## 5. A few semantic differences matter unusually much for a VM

An ordinary application can sometimes tolerate small representation differences between interpreted and compiled code. An interpreter needs to be more deliberate, because it can expose them as guest behavior.

### Exact scalar types and identity

Mypyc can unbox numeric values, and its documentation notes consequences for identity and for values such as booleans passed through integer-typed locations. Union representations are boxed, so our broad `Value` union is useful here—it is not automatically necessary to wrap every integer in a heap object. [Mypyc](https://mypyc.readthedocs.io/en/stable/using_type_annotations.html)

Nevertheless, I would specifically test guest distinctions between booleans and integers, identity of retained guest values, capability round trips, and values passing through typed intrinsic helpers.

I would **not** weaken the existing exact-type boundary checks merely to make type checking easier. A typed internal integer index and an arbitrary guest value serve different purposes. Likewise, fixed-width integer substitutions would be inappropriate for guest arbitrary-precision arithmetic.

The goal is preservation of our guest semantics, not matching incidental CPython small-integer interning between two builds.

### Host generator expressions need a targeted audit

There are **38 host generator expressions** in the module. These are distinct from the guest generators implemented by the VM.

Mypyc’s general documentation warns that generator expressions can be evaluated eagerly. However, inspecting 2.4.0’s compiler makes the situation more nuanced: direct `any(...)`, `all(...)`, and certain other consumers have specializations, including genuine short-circuiting for `any` and `all`. **It would be wrong to conclude that all 38 expressions need rewriting.** [Mypyc](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)

I would examine compiler warnings and audit expressions whose evaluation performs mutations, consumes fuel, raises exceptions, or depends on stopping early. Where the semantics are important and the lowering is unclear, an explicit loop is an inexpensive clarification.

### Native compilation does not eliminate host recursion hazards

The guest call stack is already explicit, which helps enormously. Some intrinsic operations still recurse through the host, however. Mypyc warns that compiled recursive calls can overflow the C stack without the usual Python recursion check. Existing depth budgets therefore remain necessary, and should be audited rather than relaxed after compilation. [Mypyc](https://mypyc.readthedocs.io/en/stable/differences_from_python.html)

## 6. I expect useful acceleration opportunities—but the current dynamic hot paths limit them

The optimistic case is sensible: this interpreter does a great deal of small-scale host work—method calls, record-field access, branching, stack manipulation, and bookkeeping. Those are plausible places to benefit from compiling the implementation.

But there are two conspicuous limits in the current code.

**First, payloads are frequently `Any`.** `HeapObject.data` and `Task.data` discard useful structure, and `ObjectSpace.data()` propagates that erasure throughout the evaluator. astvm astvm astvm

Mypyc can still compile operations involving erased types, but they do not offer the same optimization opportunities as precisely typed native data and calls. [Mypyc](https://mypyc.readthedocs.io/en/stable/using_type_annotations.html)

**Second, continuation dispatch goes through a dynamically assembled callable table:**

```python
self._handlers = {
    name.removeprefix('_task_'): method.__get__(self, type(self))
    for name, method in vars(type(self)).items()
    if name.startswith('_task_')
}
```

That is the actual current construction. astvm

I would not label it inherently unsupported. The more important performance question is what happens after native methods are bound, stored as generic callable values, and invoked indirectly. It should not be assumed equivalent to a statically resolved native method call.

After achieving parity, my first experiments would be **typed payload accessors and better-typed dispatch**, not replacing the object space or eliminating continuation records. Those changes can help both implementations, and still require no guest bytecode.

I would also measure dataclass construction and `dc.replace()` separately. Given their hybrid implementation, they could remain significant costs even when the surrounding evaluator is compiled. That is a hypothesis to benchmark, not an argument for prematurely replacing every dataclass.

**I have no defensible speedup multiplier to offer yet.** A successful build alone would not answer that question.

## 7. How I would stage the work

**First: establish ordinary mypy correctness without changing the architecture.** Correct the optional-state mismatches, narrow AST nodes and guest references, type the shared tables, and identify places where `Any` hides an actual invariant violation. Do not require the most restrictive possible mypy configuration immediately; require that the annotations used for compilation be accurate.

**Second: validate the host compatibility mechanisms in isolation.** Compile representative records, checkpoint graphs, the handler-table construction, and the runtime subclass hierarchy. This separates “our types are wrong” from “this particular mypyc/dataclass combination needs accommodation.”

**Third: run the existing Python suite against both implementations.** Use separate processes and verify which module was imported, so a purported compiled test run cannot accidentally load the `.py` file. Keep the interpreted runtime subclasses in the test path. Add focused parity tests for copying, scalar types, exceptions, fuel accounting, and failure paths.

**Fourth: optimize measured costs.** Benchmark prepared-program execution separately from parsing, and ordinary execution separately from checkpoint creation/restoration. That will show whether the next worthwhile change is dispatch, payload typing, record construction, or something else.

I would make the compiled target **CPython 3.14 from the start**, rather than treating a successful 3.13 build as validation of the actual target. Mypy’s current distribution includes 3.14 support, but the VM itself still needs that version-specific testing. [PyPI](https://pypi.org/project/mypy/)

## Bottom line

**The architecture is ready for this goal; the implementation needs a deliberate preparation pass.**

The biggest work is making existing invariants visible and truthful to the compiler. The most important explicit compatibility change is preserving interpreted runtime subclasses. The biggest untested risk is native dataclass construction/copying, especially checkpoint semantics. Performance tuning comes after those.

I would absolutely keep **one source implementation that works without mypyc and optionally compiles with it** as the target. I would not fork the evaluator, introduce bytecode, or compromise the closed object model to get there. And I would establish that dual-mode test requirement relatively early: it is much easier to keep future features compatible than to retrofit it after another several thousand lines of dynamic implementation accumulate.
