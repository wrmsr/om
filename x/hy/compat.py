import ast
import copy
import keyword
import platform
import sys

from omcore import lang


##


PY3_15 = sys.version_info >= (3, 15)
PYPY = platform.python_implementation() == 'PyPy'


## ast.unparse keyword mincing


@lang.cached_function
def _needs_unparse_keyword_mincing() -> bool:
    return 'def' in ast.unparse(ast.parse('𝕕𝕖𝕗 = 1'))


def _mince_keyword(name: str) -> str:
    return chr(ord(name[0]) - ord('a') + ord('𝐚')) + name[1:]


def unparse(node: ast.AST) -> str:
    """
    :func:`ast.unparse`, backporting https://github.com/python/cpython/pull/31012 where necessary. Python keywords used
    as names (which Hy permits) are 'minced': their first letter is replaced by a mathematical bold letter, which
    NFKC-normalizes back to the original, so that the unparsed source still compiles to the same names.

    Upstream Hy installs this over `ast.unparse` itself - here, it must be called explicitly.
    """

    if not _needs_unparse_keyword_mincing():
        return ast.unparse(node)

    node = copy.deepcopy(node)

    for n in ast.walk(node):
        if type(n) is ast.Constant:
            # Don't touch string literals.
            continue

        for field in n._fields:
            v = getattr(n, field, None)
            if (
                type(v) is str and
                keyword.iskeyword(v) and
                v not in ('True', 'False', 'None')
            ):
                setattr(n, field, _mince_keyword(v))

    return ast.unparse(node)
