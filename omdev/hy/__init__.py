# fmt: off
# ruff: noqa: I001
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
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from . import models  # noqa

from .finders import (  # noqa
    DirectoryHyModuleFinder,
    HyModuleFinder,
    HyModuleSource,
    MappingHyModuleFinder,
    PackageHyModuleFinder,
)

from .importing import (  # noqa
    HyModules,
    IsolatedHyModules,
    SysHyModules,
)

from .models import (  # noqa
    as_model,
)

from .reader import (  # noqa
    mangle,
    read,
    read_many,
    unmangle,
)

from .reader.exceptions import (  # noqa
    PrematureEndOfInput,
)

from .reader.hyreader import (  # noqa
    HyReader,
)

from .reader.reader import (  # noqa
    Reader,
)

from .runtime import (  # noqa
    DEFAULT_HY_PRELUDE,
    HyCoreCodeCache,
    HyNamespace,
    HyPreludeImport,
    HyRuntime,
)
