import ast


##


def _is_literal_statement(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)


def strip_literal_statements(tree: ast.AST) -> None:
    """
    Removes, in place, every expression statement that is a bare constant: docstrings, `...` placeholder bodies, and
    stray string-literal 'comments'. None of these affect behavior other than `__doc__`, which the compiler drops anyway
    for all but the first statement of a scope. A body left empty gets a `0` in place of a `pass` - it is a character
    shorter and compiles to nothing.
    """

    for node in ast.walk(tree):
        for _, value in ast.iter_fields(node):
            if not (isinstance(value, list) and value and isinstance(value[0], ast.stmt)):
                continue

            kept = [s for s in value if not _is_literal_statement(s)]
            if not kept:
                kept = [ast.Expr(ast.Constant(0))]
            value[:] = kept
