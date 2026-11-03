"""
The safety net: the minified source must parse back to exactly the tree it was printed from. This is what makes the
printer's whitespace and parenthesization decisions provably behavior-preserving - the AST, not the text, is what gets
compiled.
"""
import ast


##


class VerificationError(Exception):
    def __init__(self, message: str, *, lineno: int | None = None) -> None:
        super().__init__(message)

        self.lineno = lineno

    def __str__(self) -> str:
        message = super().__str__()
        return f'line {self.lineno}: {message}' if self.lineno is not None else message


def verify_roundtrip(expected: ast.Module, source: str) -> None:
    try:
        actual = ast.parse(source)
    except SyntaxError as exc:
        raise VerificationError(f'minified source does not parse: {exc}') from exc

    if ast.dump(expected) == ast.dump(actual):
        return

    # Only reached on a bug - find the offending top-level statement for the report.
    for e, a in zip(expected.body, actual.body):
        if ast.dump(e) != ast.dump(a):
            raise VerificationError(
                f'minified statement differs: {ast.unparse(e)[:200]!r} vs {ast.unparse(a)[:200]!r}',
                lineno=e.lineno,
            )

    raise VerificationError(f'statement count differs: {len(expected.body)} vs {len(actual.body)}')
