"""
The one rule that makes whitespace-free output tokenize correctly: two adjacent tokens need a separating space only when
the last character of the first and the first character of the second would otherwise fuse into one token. That is the
case exactly when both are identifier characters (letters, digits, underscore) - `return x`, `1 if y`, `a and b`, `in
f'x'`. Punctuation never fuses with an identifier (`if(x)`, `else'y'`, `lambda:0`), and Python has no operator that is a
prefix of another operator across the boundaries this printer produces (`a--b` is `a - (-b)`, `a<-b` is `a < (-b)`).
"""


##


def _is_ident_char(c: str) -> bool:
    return c.isalnum() or c == '_'


class SourceWriter:
    def __init__(self, *, indent: str = ' ') -> None:
        super().__init__()

        self._indent = indent
        self._parts: list[str] = []
        self._last_char = '\n'

    def write(self, s: str) -> None:
        if not s:
            return

        if _is_ident_char(self._last_char) and _is_ident_char(s[0]):
            self._parts.append(' ')

        self._parts.append(s)
        self._last_char = s[-1]

    def newline(self, depth: int) -> None:
        self._parts.append('\n')
        if depth:
            self._parts.append(self._indent * depth)
        self._last_char = '\n'

    def getvalue(self) -> str:
        return ''.join(self._parts)
