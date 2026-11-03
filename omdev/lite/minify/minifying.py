import ast

from .statements import StatementPrinter
from .transforms import strip_literal_statements
from .verification import verify_roundtrip
from .writing import SourceWriter


##


def print_minified(tree: ast.Module) -> str:
    writer = SourceWriter()
    StatementPrinter(writer).print_module(tree)
    return writer.getvalue() + '\n'


def minify(
        source: str,
        *,
        keep_literal_statements: bool = False,
        no_verify: bool = False,
        no_shebang: bool = False,
) -> str:
    tree = ast.parse(source)

    if not keep_literal_statements:
        strip_literal_statements(tree)

    out = print_minified(tree)

    if not no_verify:
        verify_roundtrip(tree, out)

    if not no_shebang and source.startswith('#!'):
        out = source.split('\n', 1)[0] + '\n' + out

    return out
