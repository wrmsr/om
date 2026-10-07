"""
Languages: the stateless half of a backend - what is true of python or javascript regardless of which interpreter
instance happens to be running it. Prompts, the name highlighters resolve, and completeness checking for the
line-oriented frontends. Interpreters (the stateful half) each point at one of these; a session may hold several
interpreters of the same language - a fresh one, a running one, a restored one.
"""
import abc
import codeop
import enum

from omcore import lang


##


class Completeness(enum.Enum):
    COMPLETE = enum.auto()
    INCOMPLETE = enum.auto()  # more lines are needed before this can run
    INVALID = enum.auto()     # no further lines will make it valid - run it and let the interpreter report


class Language(lang.Abstract):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def highlight_name(self) -> str:
        """The name `omcore.text.highlights` and minitui's tree-sitter registry resolve a highlighter by."""

        return self.name

    @property
    def prompt(self) -> str:
        return '>>> '

    @property
    def continuation_prompt(self) -> str:
        return '... '

    @abc.abstractmethod
    def check_complete(self, source: str) -> Completeness:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'


##


def _strip_final_indent(text: str) -> str:
    """Drop trailing spaces and tabs only when they follow a newline: an editor's auto-indent, not content."""

    short = text.rstrip(' \t')
    n = len(short)
    if n > 0 and text[n - 1] == '\n':
        return short
    return text


class PythonLanguage(Language):
    @property
    def name(self) -> str:
        return 'python'

    def check_complete(self, source: str) -> Completeness:
        """
        codeop's judgement in the builtin repl's 'single' mode (a block needs its closing blank line), with pyrepl's
        heuristic for the sources it rejects outright: an indented or non-empty last line still missing its newline is
        still being typed; anything else is as invalid as it will ever be. Line-oriented by nature: a source of several
        statements over several lines is one the line frontends never produce.
        """

        src = _strip_final_indent(source)
        try:
            code = codeop.compile_command(src, '<input>', 'single')
        except (SyntaxError, OverflowError, ValueError):
            lines = src.splitlines(keepends=True)
            if len(lines) <= 1:
                return Completeness.INVALID
            last = lines[-1]
            was_indented = last.startswith((' ', '\t'))
            not_empty = last.strip() != ''
            incomplete = not last.endswith('\n')
            if (was_indented or not_empty) and incomplete:
                return Completeness.INCOMPLETE
            return Completeness.INVALID
        return Completeness.INCOMPLETE if code is None else Completeness.COMPLETE


class JavascriptLanguage(Language):
    @property
    def name(self) -> str:
        return 'javascript'

    @property
    def display_name(self) -> str:
        return 'js'

    @property
    def prompt(self) -> str:
        return 'js> '

    def check_complete(self, source: str) -> Completeness:
        """
        A bracket and quote scan - the engine offers no compile-only check. Good enough for line frontends; the
        whole-buffer frontends never ask.
        """

        depth = 0
        quote: str | None = None
        escaped = False
        in_block_comment = False

        i = 0
        n = len(source)
        while i < n:
            c = source[i]

            if in_block_comment:
                if c == '*' and i + 1 < n and source[i + 1] == '/':
                    in_block_comment = False
                    i += 1

            elif quote is not None:
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == quote:
                    quote = None
                elif c == '\n' and quote != '`':
                    quote = None  # an unterminated plain string is a syntax error, not a request for more input

            elif c in ('"', "'", '`'):
                quote = c

            elif c == '/' and i + 1 < n and source[i + 1] == '/':
                nl = source.find('\n', i)
                i = n if nl < 0 else nl

            elif c == '/' and i + 1 < n and source[i + 1] == '*':
                in_block_comment = True
                i += 1

            elif c in '([{':
                depth += 1

            elif c in ')]}':
                depth -= 1
                if depth < 0:
                    return Completeness.INVALID

            i += 1

        if in_block_comment or quote == '`' or depth > 0:
            return Completeness.INCOMPLETE
        return Completeness.COMPLETE


##


PYTHON_LANGUAGE = PythonLanguage()
JAVASCRIPT_LANGUAGE = JavascriptLanguage()
