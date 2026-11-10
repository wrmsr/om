"""97dd2327b0a2ceb3c1e0bf8d9c6b5d04ace974c2"""
__version__ = 'unreleased'
nickname = None
last_version = '1.3.1'
# This is used by `(pragma :hy …)` to guess whether an unreleased
# version of Hy is new enough. In a released version, it's simply
# equal to `__version__`.


def _initialize_env_var(env_var, default_val):
    import os

    return bool(os.environ.get(env_var, default_val))


# Import for side-effects.
from . import hy_inspect
from . import importer


importer._inject_builtins()



class I:
    """
    ``hy.I`` is an object that provides syntactic sugar for imports. It allows syntax like ``(hy.I.math.sqrt 2)``  to mean ``(import math) (math.sqrt 2)``, except without bringing ``math`` or ``math.sqrt`` into scope. (See :ref:`hy.R <hy.R>` for a version that requires a macro instead of importing a Python object.) This is useful in macros to avoid namespace pollution. To refer to a module with dots in its name, use slashes instead: ``hy.I.os/path.basename`` gets the function ``basename`` from the module ``os.path``.

    You can also call ``hy.I`` like a function, as in ``(hy.I "math")``, which is useful when the module name isn't known until run-time. This interface just calls :py:func:`importlib.import_module`, avoiding (1) mangling due to attribute lookup, and (2) the translation of ``/`` to ``.`` in the module name. The advantage of ``(hy.I modname)`` over ``importlib.import_module(modname)`` is merely that it avoids bringing ``importlib`` itself into scope.
    """

    def __call__(self, module_name):
        import importlib
        return importlib.import_module(module_name)
    def __getattr__(self, s):
        from .reader.mangling import slashes2dots
        return self(slashes2dots(s))
I = I()


# Import some names on demand so that the dependent modules don't have
# to be loaded if they're not needed.

_jit_imports = dict(
    pyops=['x.hy.pyops', None],
    read='x.hy.reader',
    read_many='x.hy.reader',
    mangle='x.hy.reader',
    unmangle='x.hy.reader',
    eval=['x.hy.compiler', 'hy_eval_user'],
    repr=['x.hy.core.hy_repr', 'hy_repr'],
    repr_register=['x.hy.core.hy_repr', 'hy_repr_register'],
    gensym='x.hy.core.util',
    macroexpand='x.hy.core.util',
    macroexpand_1='x.hy.core.util',
    disassemble='x.hy.core.util',
    as_model='x.hy.models',
    REPL='x.hy.repl',
    Reader='x.hy.reader.reader',
    HyReader='x.hy.reader.hy_reader',
    PrematureEndOfInput='x.hy.reader.exceptions',
)


def __getattr__(k):
    if k not in _jit_imports:
        raise AttributeError(f'module {__name__!r} has no attribute {k!r}')

    v = _jit_imports[k]
    module, original_name = v if isinstance(v, list) else (v, k)
    import importlib
    module = importlib.import_module(module)

    globals()[k] = getattr(module, original_name) if original_name else module
    return globals()[k]
