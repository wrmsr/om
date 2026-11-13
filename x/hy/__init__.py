"""
An internal fork of Hy (https://github.com/hylang/hy, at 97dd2327b0a2ceb3c1e0bf8d9c6b5d04ace974c2), a Lisp dialect
embedded in Python.

This package has no import-time side effects and holds no global state. Hy is used through instances of
:class:`HyRuntime`: self-contained engines with their own core macros, core modules, ``hy`` namespace, and - by default
- private module registries, which leave ``sys.modules``, ``builtins``, and Python's import system untouched::

    rt = HyRuntime()
    rt.eval('(+ 1 2)')  # => 3

    mod = rt.exec('(defn #^int inc [#^int x] (+ x 1))')
    mod.inc(1)  # => 2

All Hy code compiled by a runtime sees ``hy`` (bound to its runtime's namespace) and the runtime's prelude, by default
just ``ta`` (bound to :mod:`typing`). Type annotations accept Python-style subscripts and unions, so
``#^ta.Sequence[int]`` and ``#^str|None`` work as written.

Alternatively, :func:`.globalruntime.install` opts in to a single process-wide runtime integrated with Python's import
system, under which ``.hy`` files are importable just like ``.py`` files.

The package never refers to its own absolute name: it may be relocated, and code it generates refers to ``hy`` only as a
name which is either injected into the namespace it runs in, or imported in a preamble derived from ``__package__``.
"""
from . import models  # noqa
from .finders import DirectoryHyModuleFinder  # noqa
from .finders import HyModuleFinder  # noqa
from .finders import HyModuleSource  # noqa
from .finders import MappingHyModuleFinder  # noqa
from .finders import PackageHyModuleFinder  # noqa
from .importing import HyModules  # noqa
from .importing import IsolatedHyModules  # noqa
from .importing import SysHyModules  # noqa
from .models import as_model  # noqa
from .reader import mangle  # noqa
from .reader import read  # noqa
from .reader import read_many  # noqa
from .reader import unmangle  # noqa
from .reader.exceptions import PrematureEndOfInput  # noqa
from .reader.hy_reader import HyReader  # noqa
from .reader.reader import Reader  # noqa
from .runtime import DEFAULT_HY_PRELUDE  # noqa
from .runtime import HyCoreCodeCache  # noqa
from .runtime import HyNamespace  # noqa
from .runtime import HyPreludeImport  # noqa
from .runtime import HyRuntime  # noqa
