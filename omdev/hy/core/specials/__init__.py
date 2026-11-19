"""
Hy's special forms: the core macros written in Python, which compile directly to compiler results (or Python AST
objects) rather than expanding to other Hy models. All ordinary macros eventually expand to these, or to the forms
handled by the compiler's own model compilers.

As with any Python module defining Hy macros, each submodule registers its macros in its own `_hy_macros`. They're all
collected here, so that the package as a whole may be `require`d.
"""
from . import assignment
from . import classes
from . import comprehensions
from . import control
from . import exceptions
from . import functions
from . import fundamentals
from . import imports
from . import matching
from . import operators
from . import quoting
from . import subsetting


##


_hy_macros = {
    name: fn
    for mod in [
        fundamentals,
        quoting,
        operators,
        assignment,
        subsetting,
        control,
        comprehensions,
        matching,
        exceptions,
        functions,
        classes,
        imports,
    ]
    for name, fn in mod.__dict__['_hy_macros'].items()
}
