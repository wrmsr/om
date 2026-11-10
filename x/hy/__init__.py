"""97dd2327b0a2ceb3c1e0bf8d9c6b5d04ace974c2"""
import importlib
import types
import typing as ta

from . import hy_inspect  # noqa: F401  # Register Hy inspection hooks.
from . import importer
from .reader.mangling import slashes2dots


##


class _Importer:
    """
    ``hy.I`` is an object that provides syntactic sugar for imports. It allows syntax like ``(hy.I.math.sqrt 2)``  to
    mean ``(import math) (math.sqrt 2)``, except without bringing ``math`` or ``math.sqrt`` into scope. (See :ref:`hy.R
    <hy.R>` for a version that requires a macro instead of importing a Python object.) This is useful in macros to avoid
    namespace pollution. To refer to a module with dots in its name, use slashes instead: ``hy.I.os/path.basename`` gets
    the function ``basename`` from the module ``os.path``.

    You can also call ``hy.I`` like a function, as in ``(hy.I "math")``, which is useful when the module name isn't
    known until run-time. This interface just calls :py:func:`importlib.import_module`, avoiding (1) mangling due to
    attribute lookup, and (2) the translation of ``/`` to ``.`` in the module name. The advantage of ``(hy.I modname)``
    over ``importlib.import_module(modname)`` is merely that it avoids bringing ``importlib`` itself into scope.
    """

    def __call__(self, module_name: str) -> types.ModuleType:
        return importlib.import_module(module_name)

    def __getattr__(self, s: str) -> types.ModuleType:
        return self(slashes2dots(s))


I = _Importer()


# Import some names on demand so that the dependent modules don't have to be loaded if they're not needed.


_jit_imports: dict[str, str | tuple[str, str | None]] = dict(
    pyops=('.pyops', None),
    read='.reader',
    read_many='.reader',
    mangle='.reader',
    unmangle='.reader',
    eval=('.compiler', 'hy_eval_user'),
    repr=('.core.hy_repr', 'hy_repr'),
    repr_register=('.core.hy_repr', 'hy_repr_register'),
    gensym='.core.util',
    macroexpand='.core.util',
    macroexpand_1='.core.util',
    disassemble='.core.util',
    as_model='.models',
    REPL='.repl',
    Reader='.reader.reader',
    HyReader='.reader.hy_reader',
    PrematureEndOfInput='.reader.exceptions',
)


def __getattr__(k: str) -> ta.Any:
    if k not in _jit_imports:
        raise AttributeError(f'module {__name__!r} has no attribute {k!r}')

    v = _jit_imports[k]
    module_name, original_name = v if isinstance(v, tuple) else (v, k)
    module = importlib.import_module(module_name, __package__)

    globals()[k] = getattr(module, original_name) if original_name else module
    return globals()[k]


importer._inject_builtins()  # noqa: SLF001
