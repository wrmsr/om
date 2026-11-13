# hy

An internal fork of [Hy](https://github.com/hylang/hy), a Lisp dialect embedded in Python, reworked to be usable as an
isolated, embedded 'scripting engine' - for things like inline one-liners - in an otherwise regular, type-annotated
Python codebase.

Unlike upstream Hy, importing this package has **no side effects** and it holds **no global state**: no import hooks,
no `builtins` injection, no monkeypatching of `inspect` / `runpy` / `codeop` / `multiprocessing`. All of that is
available, but only by opting in to the [global runtime](#the-global-runtime).

The package never refers to its own absolute name, and may be relocated anywhere (and named anything).

## Runtimes

Hy is used through instances of `HyRuntime`:

```python
from x.hy import HyRuntime

rt = HyRuntime()

rt.eval('(+ 1 2)')                                  # => 3
rt.eval('(+ a b)', globals={'a': 1}, locals={'b': 2})  # => 3

mod = rt.exec("""
  (defmacro twice [x] `(do ~x ~x))
  (defn #^int inc [#^int x] (+ x 1))
""")
mod.inc(1)                     # => 2
rt.eval('(twice (inc 1))', mod)  # macros are looked up in `mod`

tree = rt.compile('(setv x 1)')  # => an `ast.Module`
```

Each runtime is a self-contained engine, owning:

- its own copy of the **core macros** (visible to Hy code as `hy._hy_macros` - upstream keeps these in
  `builtins._hy_macros`),
- its own instances of the **core Hy modules** - the core macros written in Hy, `hy.pyops`, and those implementing
  `hy.repr` (and its `hy.repr-register` registry) and `hy.gensym`,
- its own **`hy` namespace** (`rt.hy`, a `HyNamespace`) - which is what the name `hy` refers to in all Hy code the
  runtime compiles. It's a view of this package, with the stateful parts of the API (`hy.eval`, `hy.repr`, `hy.pyops`,
  `hy.I`, `hy.macros.require`, ...) bound to the runtime,
- its own **module system** (see below).

Any number of runtimes may coexist without affecting one another. Compiling the core Hy modules takes a moment (~0.3s),
but the resulting code objects are cached process-wide (in a `HyCoreCodeCache`, which may be injected), after which
creating a runtime is cheap (~1ms).

### The prelude

All code compiled by a runtime sees `hy` and the runtime's *prelude*: by default just `ta`, bound to `typing`. The
prelude is configurable:

```python
HyRuntime(prelude=[HyPreludeImport('ta', 'typing'), HyPreludeImport('dc', 'omcore.dataclasses')])
```

### Type annotations

In addition to upstream's `#^ type target` syntax, annotations accept Python-style postfix type syntax, and may
immediately follow the `#^` (unless that would spell the name of a defined reader macro, like `#^foo`):

```hy
(defn #^ta.Sequence[int] f [#^ta.Mapping[str int]|None m #^ta.Callable[[int str] None] cb #^tuple[int ...] t]
  ...)

(defclass [(dc.dataclass :frozen True)] Point []
  #^int x
  #^int|None y)
```

Within an annotation form only, a form *immediately* followed by `[...]` is a subscript (`X[a]` reads as `(get X a)`,
`X[a b]` as `(get X #(a b))`), and forms *immediately* separated by `|` are a union (`a|b|c` reads as `(| a b c)`).
These nest arbitrarily. Plain Hy forms - `(get ta.Sequence int)`, `(| int None)` - remain valid annotations.

## Module systems

How a runtime finds, loads, and registers modules is delegated to a `HyModules` instance, constructed by the
`modules` factory given to the runtime.

### Isolated (the default)

`IsolatedHyModules` keeps a module registry private to its runtime, and touches no interpreter state. Hy modules are
found through a list of `HyModuleFinder`s (and the core Hy modules are always available); anything else is imported as a
regular Python module through Python's own import system. Hy code running in an isolated runtime gets a private
`__builtins__` whose `__import__` consults the runtime first:

```python
rt = HyRuntime(modules=functools.partial(IsolatedHyModules, finders=[
    DirectoryHyModuleFinder('scripts'),          # scripts/foo.hy, scripts/pkg/__init__.hy, ...
    MappingHyModuleFinder({'cfg': '(setv x 1)'}),  # in-memory sources
    PackageHyModuleFinder(prefixes=['myapp']),     # .hy files alongside .py files in packages, via importlib.resources
]))

rt.import_module('foo')
rt.eval('(import cfg [x]) x')
```

Runtime-owned Hy modules are never added as attributes of the regular Python packages they may live in - instead,
`import pkg.hymod` / `from pkg import hymod` get a `HyModuleOverlay` of `pkg` through which the Hy module is visible.

Limitations, compared to the global runtime: Python modules can't be found *inside* runtime-owned Hy packages, runtime
modules are invisible to tools that go through `sys.modules` (`inspect.getmodule`, pickling classes by reference, ...),
and Hy-aware source inspection (`inspect.getsource` of Hy functions) requires the global runtime. The entire native test
suite is additionally run in isolated runtimes (`tests/test_native_isolated.py`).

### The global runtime

`globalruntime.install()` opts in to a single, process-wide runtime using `SysHyModules` - Python's own module system -
and installs, reversibly (`globalruntime.uninstall()`):

- `sys.path_hooks` entries making `.hy` files importable from directories and zip archives, preferred over same-named
  `.py` files, and bytecode-cached like them (`HyLoader`, `HyZipImporter`),
- Hy-aware source inspection in `inspect` (`hy_inspect`),
- `multiprocessing` support: `spawn` children run `install()` first (by way of their bootstrap command line), and the
  `forkserver` preloads `autoinstall`.

Code compiled by the global runtime (bytecode-cached modules, `hy2py` output) binds `hy` and the prelude in a preamble:

```python
import typing as ta
from x.hy.autoinstall import hy
```

`autoinstall` is a deliberately side-effecting module which installs the global runtime - so, as with upstream's
`import hy`, merely running such compiled code installs the global runtime.

Note that bytecode caches don't record which version of the compiler produced them: after changing the compiler or the
global runtime's prelude, delete stale `__pycache__` entries of `.hy` files.

## Command line

`python -m x.hy` is the `hy` command (with `cmdline.hyc_main` and `cmdline.hy2py_main` the `hyc` and `hy2py` commands).
The command line is a process entrypoint, and so installs the global runtime. Unlike upstream, it leaves
`sys.executable` alone, and runs Hy files itself (rather than through a patched `runpy`) - giving the main module a spec
naming the script, as Python does for `-m`, so that `multiprocessing` children re-import it by name.

## Layout

- `runtime` - `HyRuntime`, `HyNamespace`, the prelude, and core module loading.
- `importing` - the `HyModules` interface, `IsolatedHyModules` (and its `__import__`), and `SysHyModules`.
- `finders` - `HyModuleFinder` and its implementations.
- `globalruntime` / `autoinstall` - the opt-in global runtime, and its loaders and path hooks.
- `reader` - reading source into models (`models`); `compiler` / `results` / `scoping` / `macros` / `core` - compiling
  models to Python ASTs; `pyops.hy`, `core/*.hy` - the core Hy modules.
- `repl`, `completer`, `cmdline`, `hy_inspect` - the interactive and command-line tooling.
