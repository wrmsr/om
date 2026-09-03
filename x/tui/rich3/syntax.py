# ruff: noqa: SLF001
# Copyright (c) 2020 Will McGugan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import abc
import os.path
import pathlib
import re
import textwrap
import typing as ta

import pygments.lexer as pgl
import pygments.lexers as pgls
import pygments.style as pgs
import pygments.styles as pgss
import pygments.token as pgt
import pygments.util as pgu

from ._utils.loops import loop_first
from .cells import cell_len
from .containers import Lines
from .measure import Measurement
from .padding import Padding
from .padding import PaddingDimensions
from .segment import Segment
from .segment import Segments
from .styles.colors import Color
from .styles.colors import blend_rgb
from .styles.styles import Style
from .styles.styles import StyleType
from .text import Text


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import JustifyMethod
    from .console import RenderResult


##


TokenType: ta.TypeAlias = pgt._TokenType

DEFAULT_THEME = 'monokai'

# The following styles are based on https://github.com/pygments/pygments/blob/master/pygments/formatters/terminal.py
# A few modifications were made

ANSI_LIGHT: dict[TokenType, Style] = {
    pgt.Token: Style(),
    pgt.Whitespace: Style(color='white'),
    pgt.Comment: Style(dim=True),
    pgt.Comment.Preproc: Style(color='cyan'),
    pgt.Keyword: Style(color='blue'),
    pgt.Keyword.Type: Style(color='cyan'),
    pgt.Operator.Word: Style(color='magenta'),
    pgt.Name.Builtin: Style(color='cyan'),
    pgt.Name.Function: Style(color='green'),
    pgt.Name.Namespace: Style(color='cyan', underline=True),
    pgt.Name.Class: Style(color='green', underline=True),
    pgt.Name.Exception: Style(color='cyan'),
    pgt.Name.Decorator: Style(color='magenta', bold=True),
    pgt.Name.Variable: Style(color='red'),
    pgt.Name.Constant: Style(color='red'),
    pgt.Name.Attribute: Style(color='cyan'),
    pgt.Name.Tag: Style(color='bright_blue'),
    pgt.String: Style(color='yellow'),
    pgt.Number: Style(color='blue'),
    pgt.Generic.Deleted: Style(color='bright_red'),
    pgt.Generic.Inserted: Style(color='green'),
    pgt.Generic.Heading: Style(bold=True),
    pgt.Generic.Subheading: Style(color='magenta', bold=True),
    pgt.Generic.Prompt: Style(bold=True),
    pgt.Generic.Error: Style(color='bright_red'),
    pgt.Error: Style(color='red', underline=True),
}

ANSI_DARK: dict[TokenType, Style] = {
    pgt.Token: Style(),
    pgt.Whitespace: Style(color='bright_black'),
    pgt.Comment: Style(dim=True),
    pgt.Comment.Preproc: Style(color='bright_cyan'),
    pgt.Keyword: Style(color='bright_blue'),
    pgt.Keyword.Type: Style(color='bright_cyan'),
    pgt.Operator.Word: Style(color='bright_magenta'),
    pgt.Name.Builtin: Style(color='bright_cyan'),
    pgt.Name.Function: Style(color='bright_green'),
    pgt.Name.Namespace: Style(color='bright_cyan', underline=True),
    pgt.Name.Class: Style(color='bright_green', underline=True),
    pgt.Name.Exception: Style(color='bright_cyan'),
    pgt.Name.Decorator: Style(color='bright_magenta', bold=True),
    pgt.Name.Variable: Style(color='bright_red'),
    pgt.Name.Constant: Style(color='bright_red'),
    pgt.Name.Attribute: Style(color='bright_cyan'),
    pgt.Name.Tag: Style(color='bright_blue'),
    pgt.String: Style(color='yellow'),
    pgt.Number: Style(color='bright_blue'),
    pgt.Generic.Deleted: Style(color='bright_red'),
    pgt.Generic.Inserted: Style(color='bright_green'),
    pgt.Generic.Heading: Style(bold=True),
    pgt.Generic.Subheading: Style(color='bright_magenta', bold=True),
    pgt.Generic.Prompt: Style(bold=True),
    pgt.Generic.Error: Style(color='bright_red'),
    pgt.Error: Style(color='red', underline=True),
}

RICH_SYNTAX_THEMES = {'ansi_light': ANSI_LIGHT, 'ansi_dark': ANSI_DARK}
NUMBERS_COLUMN_DEFAULT_PADDING = 2


class SyntaxTheme(abc.ABC):
    """Base class for a syntax theme."""

    @abc.abstractmethod
    def get_style_for_token(self, token_type: TokenType) -> Style:
        """Get a style for a given Pygments token."""

        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_background_style(self) -> Style:
        """Get the background color."""

        raise NotImplementedError  # pragma: no cover


class PygmentsSyntaxTheme(SyntaxTheme):
    """Syntax theme that delegates to Pygments theme."""

    def __init__(self, theme: str | type[pgs.Style]) -> None:
        self._style_cache: dict[TokenType, Style] = {}
        if isinstance(theme, str):
            try:
                self._pygments_style_class = pgss.get_style_by_name(theme)
            except pgu.ClassNotFound:
                self._pygments_style_class = pgss.get_style_by_name('default')
        else:
            self._pygments_style_class = theme

        self._background_color = self._pygments_style_class.background_color
        self._background_style = Style(bgcolor=self._background_color)

    def get_style_for_token(self, token_type: TokenType) -> Style:
        """Get a style from a Pygments class."""

        try:
            return self._style_cache[token_type]
        except KeyError:
            try:
                pygments_style = self._pygments_style_class.style_for_token(token_type)
            except KeyError:
                style = Style.null()
            else:
                color = pygments_style['color']
                bgcolor = pygments_style['bgcolor']
                style = Style(
                    color='#' + color if color else '#000000',
                    bgcolor='#' + bgcolor if bgcolor else self._background_color,
                    bold=pygments_style['bold'],
                    italic=pygments_style['italic'],
                    underline=pygments_style['underline'],
                )
            self._style_cache[token_type] = style
        return style

    def get_background_style(self) -> Style:
        return self._background_style


class ANSISyntaxTheme(SyntaxTheme):
    """Syntax theme to use standard colors."""

    def __init__(self, style_map: dict[TokenType, Style]) -> None:
        self.style_map = style_map
        self._missing_style = Style.null()
        self._background_style = Style.null()
        self._style_cache: dict[TokenType, Style] = {}

    def get_style_for_token(self, token_type: TokenType) -> Style:
        """Look up style in the style map."""

        try:
            return self._style_cache[token_type]
        except KeyError:
            # Styles form a hierarchy
            # We need to go from most to least specific
            # e.g. ("foo", "bar", "baz") to ("foo", "bar")  to ("foo",)
            get_style = self.style_map.get
            token = tuple(token_type)
            style = self._missing_style
            while token:
                _style = get_style(token)
                if _style is not None:
                    style = _style
                    break
                token = token[:-1]
            self._style_cache[token_type] = style
            return style

    def get_background_style(self) -> Style:
        return self._background_style


SyntaxPosition = tuple[int, int]


class _SyntaxHighlightRange(ta.NamedTuple):
    """
    A range to highlight in a Syntax object. `start` and `end` are 2-integers tuples, where the first integer is the
    line number (starting from 1) and the second integer is the column index (starting from 0).
    """

    style: StyleType
    start: SyntaxPosition
    end: SyntaxPosition
    style_before: bool = False


class PaddingProperty:
    """Descriptor to get and set padding."""

    def __get__(self, obj: Syntax, objtype: type[Syntax]) -> tuple[int, int, int, int]:
        """Space around the Syntax."""

        return obj._padding

    def __set__(self, obj: Syntax, padding: PaddingDimensions) -> None:
        obj._padding = Padding.unpack(padding)


class Syntax:
    """
    Construct a Syntax object to render syntax highlighted code.

    Args:
        code (str): Code to highlight.
        lexer (Lexer | str): Lexer to use (see https://pygments.org/docs/lexers/)
        theme (str, optional): Color theme, aka Pygments style (see
            https://pygments.org/docs/styles/#getting-a-list-of-available-styles). Defaults to "monokai".
        dedent (bool, optional): Enable stripping of initial whitespace. Defaults to False.
        line_numbers (bool, optional): Enable rendering of line numbers. Defaults to False.
        start_line (int, optional): Starting number for line numbers. Defaults to 1.
        line_range (tuple[int | None, int | None], optional): If given should be a tuple of the start and end line to
            render. A value of None in the tuple indicates the range is open in that direction.
        highlight_lines (Set[int]): A set of line numbers to highlight.
        code_width: Width of code to render (not including line numbers), or ``None`` to use all available width.
        tab_size (int, optional): Size of tabs. Defaults to 4.
        word_wrap (bool, optional): Enable word wrapping.
        background_color (str, optional): Optional background color, or None to use theme color. Defaults to None.
        indent_guides (bool, optional): Show indent guides. Defaults to False.
        padding (PaddingDimensions): Padding to apply around the syntax. Defaults to 0 (no padding).
    """

    _pygments_style_class: type[pgs.Style]
    _theme: SyntaxTheme

    @classmethod
    def get_theme(cls, name: str | SyntaxTheme) -> SyntaxTheme:
        """Get a syntax theme instance."""

        if isinstance(name, SyntaxTheme):
            return name
        theme: SyntaxTheme
        if name in RICH_SYNTAX_THEMES:
            theme = ANSISyntaxTheme(RICH_SYNTAX_THEMES[name])
        else:
            theme = PygmentsSyntaxTheme(name)
        return theme

    def __init__(
        self,
        code: str,
        lexer: pgl.Lexer | str,
        *,
        theme: str | SyntaxTheme = DEFAULT_THEME,
        dedent: bool = False,
        line_numbers: bool = False,
        start_line: int = 1,
        line_range: tuple[int | None, int | None] | None = None,
        highlight_lines: set[int] | None = None,
        code_width: int | None = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: str | None = None,
        indent_guides: bool = False,
        padding: PaddingDimensions = 0,
    ) -> None:
        self.code = code
        self._lexer = lexer
        self.dedent = dedent
        self.line_numbers = line_numbers
        self.start_line = start_line
        self.line_range = line_range
        self.highlight_lines = highlight_lines or set()
        self.code_width = code_width
        self.tab_size = tab_size
        self.word_wrap = word_wrap
        self.background_color = background_color
        self.background_style = (
            Style(bgcolor=background_color) if background_color else Style()
        )
        self.indent_guides = indent_guides
        self._padding = Padding.unpack(padding)

        self._theme = self.get_theme(theme)
        self._stylized_ranges: list[_SyntaxHighlightRange] = []

    padding = PaddingProperty()

    @classmethod
    def from_path(
        cls,
        path: str,
        encoding: str = 'utf-8',
        lexer: pgl.Lexer | str | None = None,
        theme: str | SyntaxTheme = DEFAULT_THEME,
        dedent: bool = False,
        line_numbers: bool = False,
        line_range: tuple[int, int] | None = None,
        start_line: int = 1,
        highlight_lines: set[int] | None = None,
        code_width: int | None = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: str | None = None,
        indent_guides: bool = False,
        padding: PaddingDimensions = 0,
    ) -> Syntax:
        """
        Construct a Syntax object from a file.

        Args:
            path (str): Path to file to highlight.
            encoding (str): Encoding of file.
            lexer (str | Lexer, optional): Lexer to use. If None, lexer will be auto-detected from path/file content.
            theme (str, optional): Color theme, aka Pygments style (see
                https://pygments.org/docs/styles/#getting-a-list-of-available-styles). Defaults to "emacs".
            dedent (bool, optional): Enable stripping of initial whitespace. Defaults to True.
            line_numbers (bool, optional): Enable rendering of line numbers. Defaults to False.
            start_line (int, optional): Starting number for line numbers. Defaults to 1.
            line_range (tuple[int, int], optional): If given should be a tuple of the start and end line to render.
            highlight_lines (Set[int]): A set of line numbers to highlight.
            code_width: Width of code to render (not including line numbers), or ``None`` to use all available width.
            tab_size (int, optional): Size of tabs. Defaults to 4.
            word_wrap (bool, optional): Enable word wrapping of code.
            background_color (str, optional): Optional background color, or None to use theme color. Defaults to None.
            indent_guides (bool, optional): Show indent guides. Defaults to False.
            padding (PaddingDimensions): Padding to apply around the syntax. Defaults to 0 (no padding).

        Returns:
            [Syntax]: A Syntax object that may be printed to the console
        """

        code = pathlib.Path(path).read_text(encoding=encoding)

        if not lexer:
            lexer = cls.guess_lexer(path, code=code)

        return cls(
            code,
            lexer,
            theme=theme,
            dedent=dedent,
            line_numbers=line_numbers,
            line_range=line_range,
            start_line=start_line,
            highlight_lines=highlight_lines,
            code_width=code_width,
            tab_size=tab_size,
            word_wrap=word_wrap,
            background_color=background_color,
            indent_guides=indent_guides,
            padding=padding,
        )

    @classmethod
    def guess_lexer(cls, path: str, code: str | None = None) -> str:
        """
        Guess the alias of the Pygments lexer to use based on a path and an optional string of code. If code is
        supplied, it will use a combination of the code and the filename to determine the best lexer to use. For
        example, if the file is ``index.html`` and the file contains Django templating syntax, then "html+django" will
        be returned. If the file is ``index.html``, and no templating language is used, the "html" lexer will be used.
        If no string of code is supplied, the lexer will be chosen based on the file extension..

        Args:
            path (AnyStr): The path to the file containing the code you wish to know the lexer for.
            code (str, optional): Optional string of code that will be used as a fallback if no lexer is found for the
                supplied path.

        Returns:
            str: The name of the Pygments lexer that best matches the supplied path/code.
        """

        lexer: pgl.Lexer | None = None
        lexer_name = 'default'
        if code:
            try:
                lexer = pgls.guess_lexer_for_filename(path, code)
            except pgu.ClassNotFound:
                pass

        if not lexer:
            try:
                _, ext = os.path.splitext(path)
                if ext:
                    extension = ext.lstrip('.').lower()
                    lexer = pgls.get_lexer_by_name(extension)
            except pgu.ClassNotFound:
                pass

        if lexer:
            if lexer.aliases:
                lexer_name = lexer.aliases[0]
            else:
                lexer_name = lexer.name

        return lexer_name

    def _get_base_style(self) -> Style:
        """Get the base style."""

        default_style = self._theme.get_background_style() + self.background_style
        return default_style

    def _get_token_color(self, token_type: TokenType) -> Color | None:
        """
        Get a color (if any) for the given token.

        Args:
            token_type (TokenType): A token type tuple from Pygments.

        Returns:
            Optional[Color]: Color from theme, or None for no color.
        """

        style = self._theme.get_style_for_token(token_type)
        return style.color

    @property
    def lexer(self) -> pgl.Lexer | None:
        """
        The lexer for this syntax, or None if no lexer was found.

        Tries to find the lexer by name if a string was passed to the constructor.
        """

        if isinstance(self._lexer, pgl.Lexer):
            return self._lexer
        try:
            return pgls.get_lexer_by_name(
                self._lexer,
                stripnl=False,
                ensurenl=True,
                tabsize=self.tab_size,
            )
        except pgu.ClassNotFound:
            return None

    @property
    def default_lexer(self) -> pgl.Lexer:
        """A Pygments Lexer to use if one is not specified or invalid."""

        return pgls.get_lexer_by_name(
            'text',
            stripnl=False,
            ensurenl=True,
            tabsize=self.tab_size,
        )

    def highlight(
        self,
        code: str,
        line_range: tuple[int | None, int | None] | None = None,
    ) -> Text:
        """
        Highlight code and return a Text instance.

        Args:
            code (str): Code to highlight.
            line_range(tuple[int, int], optional): Optional line range to highlight.

        Returns:
            Text: A text instance containing highlighted syntax.
        """

        base_style = self._get_base_style()
        justify: JustifyMethod = (
            'default' if base_style.transparent_background else 'left'
        )

        text = Text(
            justify=justify,
            style=base_style,
            tab_size=self.tab_size,
            no_wrap=not self.word_wrap,
        )
        _get_theme_style = self._theme.get_style_for_token

        lexer = self.lexer or self.default_lexer

        if line_range:
            # More complicated path to only stylize a portion of the code. This speeds up further operations as there
            # are less spans to process.
            line_start, line_end = line_range

            def line_tokenize() -> ta.Iterable[tuple[ta.Any, str]]:
                """Split tokens to one per line."""

                for token_type, token in lexer.get_tokens(code):
                    while token:
                        line_token, new_line, token = token.partition('\n')
                        yield token_type, line_token + new_line

            def tokens_to_spans() -> ta.Iterable[tuple[str, Style | None]]:
                """Convert tokens to spans."""

                tokens = iter(line_tokenize())
                line_no = 0
                _line_start = line_start - 1 if line_start else 0

                # Skip over tokens until line start
                while line_no < _line_start:
                    try:
                        _token_type, token = next(tokens)
                    except StopIteration:
                        break
                    yield (token, None)
                    if token.endswith('\n'):
                        line_no += 1
                # Generate spans until line end
                for token_type, token in tokens:
                    yield (token, _get_theme_style(token_type))
                    if token.endswith('\n'):
                        line_no += 1
                        if line_end and line_no >= line_end:
                            break

            text.append_tokens(tokens_to_spans())

        else:
            text.append_tokens(
                (token, _get_theme_style(token_type))
                for token_type, token in lexer.get_tokens(code)
            )
        if self.background_color is not None:
            text.stylize(f'on {self.background_color}')

        if self._stylized_ranges:
            self._apply_stylized_ranges(text)

        return text

    def stylize_range(
        self,
        style: StyleType,
        start: SyntaxPosition,
        end: SyntaxPosition,
        style_before: bool = False,
    ) -> None:
        """
        Adds a custom style on a part of the code, that will be applied to the syntax display when it's rendered. Line
        numbers are 1-based, while column indexes are 0-based.

        Args:
            style (StyleType): The style to apply.
            start (tuple[int, int]): The start of the range, in the form `[line number, column index]`.
            end (tuple[int, int]): The end of the range, in the form `[line number, column index]`.
            style_before (bool): Apply the style before any existing styles.
        """

        self._stylized_ranges.append(
            _SyntaxHighlightRange(style, start, end, style_before),
        )

    def _get_line_numbers_color(self, blend: float = 0.3) -> Color:
        background_style = self._theme.get_background_style() + self.background_style
        background_color = background_style.bgcolor
        if background_color is None or background_color.is_system_defined:
            return Color.default()
        foreground_color = self._get_token_color(pgt.Token.Text)
        if foreground_color is None or foreground_color.is_system_defined:
            return foreground_color or Color.default()
        new_color = blend_rgb(
            background_color.get_truecolor(),
            foreground_color.get_truecolor(),
            cross_fade=blend,
        )
        return Color.from_triplet(new_color)

    @property
    def _numbers_column_width(self) -> int:
        """Get the number of characters used to render the numbers column."""

        column_width = 0
        if self.line_numbers:
            column_width = (
                len(str(self.start_line + self.code.count('\n')))
                + NUMBERS_COLUMN_DEFAULT_PADDING
            )
        return column_width

    def _get_number_styles(self, console: Console) -> tuple[Style, Style, Style]:
        """Get background, number, and highlight styles for line numbers."""

        background_style = self._get_base_style()
        if background_style.transparent_background:
            return Style.null(), Style(dim=True), Style.null()
        if console.color_system in ('256', 'truecolor'):
            number_style = Style.chain(
                background_style,
                self._theme.get_style_for_token(pgt.Token.Text),
                Style(color=self._get_line_numbers_color()),
                self.background_style,
            )
            highlight_number_style = Style.chain(
                background_style,
                self._theme.get_style_for_token(pgt.Token.Text),
                Style(bold=True, color=self._get_line_numbers_color(0.9)),
                self.background_style,
            )
        else:
            number_style = background_style + Style(dim=True)
            highlight_number_style = background_style + Style(dim=False)
        return background_style, number_style, highlight_number_style

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        _, right, _, left = self.padding
        padding = left + right
        if self.code_width is not None:
            width = self.code_width + self._numbers_column_width + padding + 1
            return Measurement(self._numbers_column_width, width)
        lines = self.code.splitlines()
        width = (
            self._numbers_column_width +
            padding +
            (max(cell_len(line) for line in lines) if lines else 0)
        )
        if self.line_numbers:
            width += 1
        return Measurement(self._numbers_column_width, width)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        segments = Segments(self._get_syntax(console, options))
        if any(self.padding):
            yield Padding(segments, style=self._get_base_style(), pad=self.padding)
        else:
            yield segments

    def _get_syntax(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> ta.Iterable[Segment]:
        """Get the Segments for the Syntax object, excluding any vertical/horizontal padding"""

        transparent_background = self._get_base_style().transparent_background
        _pad_top, pad_right, _pad_bottom, pad_left = self.padding
        horizontal_padding = pad_left + pad_right
        code_width = (
            (
                (options.max_width - self._numbers_column_width - 1)
                if self.line_numbers
                else options.max_width
            )
            - horizontal_padding
            if self.code_width is None
            else self.code_width
        )
        code_width = max(0, code_width)

        ends_on_nl, processed_code = self._process_code(self.code)
        text = self.highlight(processed_code, self.line_range)

        if not self.line_numbers and not self.word_wrap and not self.line_range:
            if not ends_on_nl:
                text.remove_suffix('\n')
            # Simple case of just rendering text
            style = (
                self._get_base_style()
                + self._theme.get_style_for_token(pgt.Comment)
                + Style(dim=True)
                + self.background_style
            )
            if self.indent_guides and not options.ascii_only:
                text = text.with_indent_guides(self.tab_size, style=style)
                text.overflow = 'crop'
            if style.transparent_background:
                yield from console.render(
                    text, options=options.update(width=code_width),
                )
            else:
                syntax_lines = console.render_lines(
                    text,
                    options.update(width=code_width, height=None, justify='left'),
                    style=self.background_style,
                    pad=True,
                    new_lines=True,
                )
                for syntax_line in syntax_lines:
                    yield from syntax_line
            return

        start_line, end_line = self.line_range or (None, None)
        line_offset = 0
        if start_line:
            line_offset = max(0, start_line - 1)
        lines: list[Text] | Lines = text.split('\n', allow_blank=ends_on_nl)
        if self.line_range:
            if line_offset > len(lines):
                return
            lines = lines[line_offset:end_line]

        if self.indent_guides and not options.ascii_only:
            style = (
                self._get_base_style() +
                self._theme.get_style_for_token(pgt.Comment) +
                Style(dim=True) +
                self.background_style
            )
            lines = (
                Text('\n')
                .join(lines)
                .with_indent_guides(self.tab_size, style=style + Style(italic=False))
                .split('\n', allow_blank=True)
            )

        numbers_column_width = self._numbers_column_width
        render_options = options.update(width=code_width)

        highlight_line = self.highlight_lines.__contains__
        _segment = Segment
        new_line = _segment('\n')

        line_pointer = '❱ '

        (
            background_style,
            number_style,
            highlight_number_style,
        ) = self._get_number_styles(console)

        for line_no, line in enumerate(lines, self.start_line + line_offset):
            if self.word_wrap:
                wrapped_lines = console.render_lines(
                    line,
                    render_options.update(height=None, justify='left'),
                    style=background_style,
                    pad=not transparent_background,
                )
            else:
                segments = list(line.render(console, end=''))
                if options.no_wrap:
                    wrapped_lines = [segments]
                else:
                    wrapped_lines = [
                        _segment.adjust_line_length(
                            segments,
                            render_options.max_width,
                            style=background_style,
                            pad=not transparent_background,
                        ),
                    ]

            if self.line_numbers:
                wrapped_line_left_pad = _segment(
                    ' ' * numbers_column_width + ' ', background_style,
                )

                for first, wrapped_line in loop_first(wrapped_lines):
                    if first:
                        line_column = str(line_no).rjust(numbers_column_width - 2) + ' '

                        if highlight_line(line_no):
                            yield _segment(line_pointer, Style(color='red'))
                            yield _segment(line_column, highlight_number_style)

                        else:
                            yield _segment('  ', highlight_number_style)
                            yield _segment(line_column, number_style)

                    else:
                        yield wrapped_line_left_pad

                    yield from wrapped_line
                    yield new_line

            else:
                for wrapped_line in wrapped_lines:
                    yield from wrapped_line
                    yield new_line

    def _apply_stylized_ranges(self, text: Text) -> None:
        """
        Apply stylized ranges to a text instance, using the given code to determine the right portion to apply the style
        to.

        Args:
            text (Text): Text instance to apply the style to.
        """

        code = text.plain
        newlines_offsets = [
            # Let's add outer boundaries at each side of the list:
            0,
            # N.B. using "\n" here is much faster than using metacharacters such as "^" or "\Z":
            *[
                match.start() + 1
                for match in re.finditer('\n', code, flags=re.MULTILINE)
            ],
            len(code) + 1,
        ]

        for stylized_range in self._stylized_ranges:
            start = _get_code_index_for_syntax_position(
                newlines_offsets, stylized_range.start,
            )
            end = _get_code_index_for_syntax_position(
                newlines_offsets, stylized_range.end,
            )
            if start is not None and end is not None:
                if stylized_range.style_before:
                    text.stylize_before(stylized_range.style, start, end)
                else:
                    text.stylize(stylized_range.style, start, end)

    def _process_code(self, code: str) -> tuple[bool, str]:
        """
        Applies various processing to a raw code string
        (normalises it so it always ends with a line return, dedents it if necessary, etc.)

        Args:
            code (str): The raw code string to process

        Returns:
            tuple[bool, str]: the boolean indicates whether the raw code ends with a line return,
                while the string is the processed code.
        """

        ends_on_nl = code.endswith('\n')
        processed_code = code if ends_on_nl else code + '\n'
        processed_code = (
            textwrap.dedent(processed_code) if self.dedent else processed_code
        )
        processed_code = processed_code.expandtabs(self.tab_size)
        return ends_on_nl, processed_code


def _get_code_index_for_syntax_position(
        newlines_offsets: ta.Sequence[int],
        position: SyntaxPosition,
) -> int | None:
    """
    Returns the index of the code string for the given positions.

    Args:
        newlines_offsets (Sequence[int]): The offset of each newline character found in the code snippet.
        position (SyntaxPosition): The position to search for.

    Returns:
        Optional[int]: The index of the code string for this position, or `None`
            if the given position's line number is out of range (if it's the column that is out of range
            we silently clamp its value so that it reaches the end of the line)
    """

    lines_count = len(newlines_offsets)

    line_number, column_index = position
    if line_number > lines_count or len(newlines_offsets) < (line_number + 1):
        return None  # `line_number` is out of range
    line_index = line_number - 1
    line_length = newlines_offsets[line_index + 1] - newlines_offsets[line_index] - 1
    # If `column_index` is out of range: let's silently clamp it:
    column_index = min(line_length, column_index)
    return newlines_offsets[line_index] + column_index
