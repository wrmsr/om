"""
Non-evaluating, error-tolerant Hy highlighting using the shared semantic code styles.

This follows the built-in reader grammar, not macro expansion. User reader macros are styled as dispatch tags but
never invoked: their arbitrary source consumption (and runtime name shadowing) cannot be inferred statically.
"""
import bisect
import builtins
import typing as ta

from omcore.text import styled as st
from omcore.text.highlights import HighlightedLines
from omcore.text.highlights import Highlighter

from .reader.hyreader import HyReader
from .reader.hyreader import _as_number
from .reader.mangling import mangle


##


# core/specials and core/macros.hy. Kept lexical so highlighting doesn't need to initialize a runtime.
_HY_HIGHLIGHT_KEYWORDS = frozenset("""
    do eval-and-compile eval-when-compile do-mac py pys pragma
    unquote unquote-splice unpack-mapping except except* finally else quote quasiquote
    setv setx let annotate deftype global nonlocal del get . cut unpack-iterable
    if while break continue with for lfor sfor gfor dfor match raise try assert
    fn defn defmacro return yield await defclass require import
    not bnot and or = is < <= > >= != is-not in not-in chainc
    + * | - / & @ ** // << >> % ^ += /= //= *= -= %= **= <<= >>= |= ^= &= @=
    cond when defreader get-macro local-macros export True False None
""".split())  # noqa: SIM905

_HY_HIGHLIGHT_MANGLED_KEYWORDS = frozenset(map(mangle, _HY_HIGHLIGHT_KEYWORDS))

_HY_HIGHLIGHT_DEFINITIONS = frozenset(('defn', 'defmacro', 'defclass', 'deftype', 'defreader'))
_HY_HIGHLIGHT_SPACE = frozenset(' \t\n\r\f\v')
_HY_HIGHLIGHT_BUILTINS = frozenset(dir(builtins)) | {'hy'}


class _HyHighlightScanner:
    def __init__(self, source: str, *, bracketed_templates: bool) -> None:
        super().__init__()

        self.source = source
        self.pos = 0
        self.spans: list[tuple[int, int, str]] = []
        self.bracketed_templates = bracketed_templates

    def _add(self, start: int, tag: str) -> None:
        if self.pos > start:
            self.spans.append((start, self.pos, tag))

    def _peek(self) -> str:
        return self.source[self.pos:self.pos + 1]

    def _space(self) -> None:
        while self._peek() and self._peek() in _HY_HIGHLIGHT_SPACE:
            self.pos += 1

    def _ident(self, *, annotation: bool = False) -> str:
        start = self.pos
        while (
                (c := self._peek()) and
                c not in HyReader.NON_IDENT and
                c not in _HY_HIGHLIGHT_SPACE and
                not (annotation and c == '|')
        ):
            self.pos += 1
        return self.source[start:self.pos]

    def _comment(self) -> None:
        start = self.pos
        end = self.source.find('\n', start)
        self.pos = len(self.source) if end < 0 else end
        self._add(start, 'code.comment')

    def _sequence(
            self,
            closer: str,
            *,
            expression: bool = False,
            definition: bool = False,
            annotation: bool = False,
    ) -> str | None:
        head: str | None = None
        pending = False
        first = True
        annotated_name: str | None = None
        while self._peek():
            self._space()
            if self._peek() == closer:
                self.pos += 1
                break
            if not self._peek():
                break
            value = self._try_form(definition=pending, annotation=annotation)
            if value is False:
                continue
            if first:
                head = mangle(value) if expression and value else None
                pending = head in _HY_HIGHLIGHT_DEFINITIONS or (definition and head == 'annotate')
                first = False
            elif pending and value is not None and not value.startswith(':'):
                annotated_name = value
                pending = False
        return annotated_name if definition and head == 'annotate' else None

    def _string(
            self,
            start: int,
            closing: str,
            *,
            interpolate: bool,
            raw: bool,
            annotation: bool,
    ) -> None:
        segment = start
        quoted = closing == '"'
        while self._peek():
            if self.source.startswith(closing, self.pos):
                self.pos += len(closing)
                self._add(segment, 'code.string')
                return
            c = self._peek()
            if quoted and c == '\\':
                # Raw strings still escape quotes. Other escapes don't suppress interpolation.
                if self.source[self.pos + 1:self.pos + 2] in ('\\', '"'):
                    self.pos = min(self.pos + 2, len(self.source))
                    continue
            if interpolate and not raw and c == '{' and self.source[max(0, self.pos - 2):self.pos] == '\\N':
                end = self.source.find('}', self.pos + 1)
                self.pos = len(self.source) if end < 0 else end + 1
                continue
            if interpolate and c in '{}':
                if self.source.startswith(c * 2, self.pos):
                    self.pos += 2
                    continue
                if c == '{':
                    self.pos += 1
                    self._add(segment, 'code.string')
                    self._field(raw=raw, annotation=annotation)
                    segment = self.pos
                    continue
            self.pos += 1
        self._add(segment, 'code.string')

    def _field(self, *, raw: bool, annotation: bool) -> None:
        self._space()
        self._form(annotation=annotation)
        self._space()
        start = self.pos
        if self._peek() == '=':
            self.pos += 1
            self._space()
        if self._peek() == '!':
            self.pos = min(self.pos + 2, len(self.source))
        self._space()
        if self._peek() == ':':
            self.pos += 1
            self._string(start, '}', interpolate=True, raw=raw, annotation=annotation)
        elif self._peek() == '}':
            self.pos += 1
            self._add(start, 'code.string')
        else:
            # Incomplete or malformed field: leave the outer string scanner to recover.
            self._add(start, 'code.string')

    def _primary(self, *, definition: bool, annotation: bool) -> str | None | ta.Literal[False]:
        self._space()
        if self._peek() == ';':
            self._comment()
            return False
        start = self.pos
        if self._peek() == '#':
            self.pos += 1
            tag = self._ident(annotation=annotation)
            if not tag and self._peek():
                tag = self._peek()
                self.pos += 1
            if tag == '_':
                saved = len(self.spans)
                self._form(annotation=annotation)
                del self.spans[saved:]
                self._add(start, 'code.comment')
                return False
            if tag == '[':
                end = self.source.find('[', self.pos)
                invalid = self.source.find(']', self.pos)
                if end < 0 or (0 <= invalid < end):
                    self.pos = len(self.source)
                    self._add(start, 'code.string')
                else:
                    delim = self.source[self.pos:end]
                    self.pos = end + 1
                    interpolate = delim == 'f' or delim.startswith('f-') or (
                        self.bracketed_templates and (delim == 't' or delim.startswith('t-'))
                    )
                    self._string(start, ']' + delim + ']', interpolate=interpolate, raw=True, annotation=annotation)
                return None
            self._add(start, 'code.keyword')
            if tag in ('(', '{'):
                self._sequence(')' if tag == '(' else '}', annotation=annotation)
                return None
            if tag.startswith('^'):
                # The built-in annotation reader accepts an adjacent type after #^.
                self.pos = start + 2
                self.spans[-1] = (start, self.pos, 'code.keyword')
                self._form(annotation=True)
                return self._form(definition=definition, annotation=annotation)
            if tag in ('*', '**'):
                return self._form(annotation=annotation)
            # Custom dispatch tags have unknowable consumption. Don't execute them.
            return None
        self._space()
        start = self.pos
        c = self._peek()
        if not c:
            return None
        self.pos += 1
        value: str | None = None
        if c in '([{':
            value = self._sequence(
                {'(': ')', '[': ']', '{': '}'}[c],
                expression=c == '(',
                definition=definition,
                annotation=annotation,
            )
        elif c in "'`~":
            if c == '~' and self._peek() == '@':
                self.pos += 1
            self._add(start, 'code.keyword')
            self._form(annotation=annotation)
        elif c == '"':
            self._string(start, '"', interpolate=False, raw=False, annotation=annotation)
        elif c not in ')]}':
            value = c + self._ident(annotation=annotation)
            if self._peek() == '"' and c != ':':
                self.pos += 1
                self._string(
                    start,
                    '"',
                    interpolate='f' in value or 't' in value,
                    raw='r' in value,
                    annotation=annotation,
                )
                value = None
            else:
                tag_name: str | None = None
                if c == ':':
                    tag_name = 'code.keyword'
                elif _as_number(value) is not None:
                    tag_name = 'code.number'
                elif definition:
                    tag_name = 'code.def'
                elif mangle(value) in _HY_HIGHLIGHT_MANGLED_KEYWORDS:
                    tag_name = 'code.keyword'
                elif mangle(value) in _HY_HIGHLIGHT_BUILTINS:
                    tag_name = 'code.builtin'
                elif '.' in value and (root := value.split('.')[0]) and mangle(root) in _HY_HIGHLIGHT_BUILTINS:
                    self.spans.append((start, start + len(root), 'code.builtin'))
                if tag_name is not None:
                    self._add(start, tag_name)

        return value

    def _try_form(
            self,
            *,
            definition: bool = False,
            annotation: bool = False,
            no_union: bool = False,
    ) -> str | None | ta.Literal[False]:
        value = self._primary(definition=definition, annotation=annotation)
        if value is not False and annotation:
            while self._peek() == '[':
                self.pos += 1
                self._sequence(']', annotation=True)
            if not no_union:
                while self._peek() == '|':
                    start = self.pos
                    self.pos += 1
                    self._add(start, 'code.keyword')
                    self._form(annotation=True, no_union=True)
        return value

    def _form(
            self,
            *,
            definition: bool = False,
            annotation: bool = False,
            no_union: bool = False,
    ) -> str | None:
        # Unlike sequence loops, prefixes and fields need the next *surviving* form.
        while True:
            value = self._try_form(definition=definition, annotation=annotation, no_union=no_union)
            if value is not False:
                return value

    def scan(self) -> None:
        if self.source.startswith('#!'):
            self._comment()
        try:
            while self._peek():
                self._form()
        except RecursionError:
            # Pathologically deep or unfinished editor input must not break rendering.
            pass


class HyHighlighter(Highlighter):
    """
    Built-in Hy syntax without evaluating source or loading pygments.

    Set `bracketed_templates` to match the embedded reader's option. In-source pragmas and custom reader macros aren't
    executed; quoted strings with a `t` prefix always interpolate, while bracketed `t` strings opt in like the reader.
    """

    def __init__(self, *, bracketed_templates: bool = False) -> None:
        super().__init__()

        self._bracketed_templates = bracketed_templates

    def highlight(self, lines: ta.Sequence[str]) -> HighlightedLines:
        scanner = _HyHighlightScanner('\n'.join(lines), bracketed_templates=self._bracketed_templates)
        scanner.scan()
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line) + 1)
        spans: list[list[st.StyleSpan]] = [[] for _ in lines]
        for start, end, tag in scanner.spans:
            row = bisect.bisect_right(offsets, start) - 1
            while row < len(lines) and offsets[row] < end:
                left = max(0, start - offsets[row])
                right = min(len(lines[row]), end - offsets[row])
                if right > left:
                    spans[row].append(st.StyleSpan.of(left, right, tag))
                row += 1
        return [st.StyledText(line, tuple(sorted(row, key=lambda s: s.start))) for line, row in zip(lines, spans)]
