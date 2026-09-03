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
import datetime
import functools
import itertools
import os
import sys
import threading
import time
import types
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ._utils.emoji import emoji_replace
from ._utils.nullfile import NULL_FILE
from .align import Align
from .control import Control
from .emoji import EmojiVariant
from .errors import MissingStyleError
from .errors import NoAltScreenError
from .errors import NotRenderableError
from .errors import StyleSyntaxError
from .highlighter import NullHighlighter
from .highlighter import ReprHighlighter
from .markup import render as render_markup
from .measure import Measurement
from .measure import measure_renderables
from .pager import Pager
from .pager import SystemPager
from .protocol import rich_cast
from .region import Region
from .screen import Screen
from .segment import Segment
from .styled import Styled
from .styles.colors import ColorSystem
from .styles.defaults.themes import DEFAULT_THEME
from .styles.styles import Style
from .styles.styles import StyleType
from .styles.themes import Theme
from .styles.themes import ThemeStack
from .text import Text
from .text import TextType


type HighlighterType = ta.Callable[[str | Text], Text]

JustifyMethod = ta.Literal['default', 'left', 'center', 'right', 'full']
OverflowMethod = ta.Literal['fold', 'crop', 'ellipsis', 'ignore']


##


class NoChange:
    pass


NO_CHANGE = NoChange()


#


try:
    _STDIN_FILENO = sys.__stdin__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDIN_FILENO = 0
try:
    _STDOUT_FILENO = sys.__stdout__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDOUT_FILENO = 1
try:
    _STDERR_FILENO = sys.__stderr__.fileno()  # type: ignore[union-attr]
except Exception:
    _STDERR_FILENO = 2

_STD_STREAMS = (_STDIN_FILENO, _STDOUT_FILENO, _STDERR_FILENO)
_STD_STREAMS_OUTPUT = (_STDOUT_FILENO, _STDERR_FILENO)


#


_TERM_COLORS = {
    'kitty': ColorSystem.EIGHT_BIT,
    '256color': ColorSystem.EIGHT_BIT,
    '16color': ColorSystem.STANDARD,
}


#


class ConsoleDimensions(ta.NamedTuple):
    """Size of the terminal."""

    # The width of the console in 'cells'.
    width: int

    # The height of the console in lines.
    height: int


@dc.dataclass()
class ConsoleOptions:
    """Options for __rich_console__ method."""

    # Size of console.
    size: ConsoleDimensions

    # Minimum width of renderable.
    min_width: int

    # Maximum width of renderable.
    max_width: int

    # True if the target is a terminal, otherwise False.
    is_terminal: bool

    # Encoding of terminal.
    encoding: str

    # Height of container (starts as terminal)
    max_height: int

    # Justify value override for renderable.
    justify: JustifyMethod | None = None

    # Overflow value override for renderable.
    overflow: OverflowMethod | None = None

    # Disable wrapping for text.
    no_wrap: bool | None = False

    # Highlight override for render_str.
    highlight: bool | None = None

    # Enable markup when rendering strings.
    markup: bool | None = None

    height: int | None = None

    @property
    def ascii_only(self) -> bool:
        """Check if renderables should use ascii only."""

        return not self.encoding.startswith('utf')

    def copy(self) -> ConsoleOptions:
        """
        Return a copy of the options.

        Returns:
            ConsoleOptions: a copy of self.
        """

        options: ConsoleOptions = ConsoleOptions.__new__(ConsoleOptions)
        options.__dict__ = self.__dict__.copy()
        return options

    def update(
        self,
        *,
        width: int | NoChange = NO_CHANGE,
        min_width: int | NoChange = NO_CHANGE,
        max_width: int | NoChange = NO_CHANGE,
        justify: JustifyMethod | None | NoChange = NO_CHANGE,
        overflow: OverflowMethod | None | NoChange = NO_CHANGE,
        no_wrap: bool | None | NoChange = NO_CHANGE,
        highlight: bool | None | NoChange = NO_CHANGE,
        markup: bool | None | NoChange = NO_CHANGE,
        height: int | None | NoChange = NO_CHANGE,
    ) -> ConsoleOptions:
        """Update values, return a copy."""

        options = self.copy()
        if not isinstance(width, NoChange):
            options.min_width = options.max_width = max(0, width)
        if not isinstance(min_width, NoChange):
            options.min_width = min_width
        if not isinstance(max_width, NoChange):
            options.max_width = max_width
        if not isinstance(justify, NoChange):
            options.justify = justify
        if not isinstance(overflow, NoChange):
            options.overflow = overflow
        if not isinstance(no_wrap, NoChange):
            options.no_wrap = no_wrap
        if not isinstance(highlight, NoChange):
            options.highlight = highlight
        if not isinstance(markup, NoChange):
            options.markup = markup
        if not isinstance(height, NoChange):
            if height is not None:
                options.max_height = height
            options.height = None if height is None else max(0, height)
        return options

    def update_width(self, width: int) -> ConsoleOptions:
        """
        Update just the width, return a copy.

        Args:
            width (int): New width (sets both min_width and max_width)

        Returns:
            ~ConsoleOptions: New console options instance.
        """

        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        return options

    def update_height(self, height: int) -> ConsoleOptions:
        """
        Update the height, and return a copy.

        Args:
            height (int): New height

        Returns:
            ~ConsoleOptions: New Console options instance.
        """

        options = self.copy()
        options.max_height = options.height = height
        return options

    def reset_height(self) -> ConsoleOptions:
        """
        Return a copy of the options with height set to ``None``.

        Returns:
            ~ConsoleOptions: New console options instance.
        """

        options = self.copy()
        options.height = None
        return options

    def update_dimensions(self, width: int, height: int) -> ConsoleOptions:
        """
        Update the width and height, and return a copy.

        Args:
            width (int): New width (sets both min_width and max_width).
            height (int): New height.

        Returns:
            ~ConsoleOptions: New console options instance.
        """

        options = self.copy()
        options.min_width = options.max_width = max(0, width)
        options.height = options.max_height = height
        return options


@ta.runtime_checkable
class RichCast(ta.Protocol):
    """An object that may be 'cast' to a console renderable."""

    def __rich__(self) -> ConsoleRenderable | RichCast | str: ...


@ta.runtime_checkable
class ConsoleRenderable(ta.Protocol):
    """An object that supports the console protocol."""

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult: ...


# A type that may be rendered by Console.
RenderableType: ta.TypeAlias = ConsoleRenderable | RichCast | str

# The result of calling a __rich_console__ method.
RenderResult: ta.TypeAlias = ta.Iterable[RenderableType | Segment]

_null_highlighter = NullHighlighter()


class CaptureError(Exception):
    """An error in the Capture context manager."""


class NewLine:
    """A renderable to generate new line(s)"""

    def __init__(self, count: int = 1) -> None:
        self.count = count

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> ta.Iterable[Segment]:
        yield Segment('\n' * self.count)


class ScreenUpdate:
    """Render a list of lines at a given offset."""

    def __init__(self, lines: list[list[Segment]], x: int, y: int) -> None:
        self._lines = lines
        self.x = x
        self.y = y

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        x = self.x
        move_to = Control.move_to
        for offset, line in enumerate(self._lines, self.y):
            yield move_to(x, offset)
            yield from line


class Capture:
    """
    Context manager to capture the result of printing to the console.
    See :meth:`~rich.console.Console.capture` for how to use.

    Args:
        console (Console): A console instance to capture output.
    """

    def __init__(self, console: Console) -> None:
        self._console = console
        self._result: str | None = None

    def __enter__(self) -> ta.Self:
        self._console.begin_capture()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self._result = self._console.end_capture()

    def get(self) -> str:
        """Get the result of the capture."""

        if self._result is None:
            raise CaptureError('Capture result is not available until context manager exits.')
        return self._result


class ThemeContext:
    """A context manager to use a temporary theme. See :meth:`~rich.console.Console.use_theme` for usage."""

    def __init__(self, console: Console, theme: Theme, inherit: bool = True) -> None:
        self.console = console
        self.theme = theme
        self.inherit = inherit

    def __enter__(self) -> ta.Self:
        self.console.push_theme(self.theme)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.console.pop_theme()


class PagerContext:
    """A context manager that 'pages' content. See :meth:`~rich.console.Console.pager` for usage."""

    def __init__(
        self,
        console: Console,
        pager: Pager | None = None,
        styles: bool = False,
        links: bool = False,
    ) -> None:
        self._console = console
        self.pager = SystemPager() if pager is None else pager
        self.styles = styles
        self.links = links

    def __enter__(self) -> ta.Self:
        self._console._enter_buffer()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        if exc_type is None:
            with self._console._lock:
                buffer: list[Segment] = self._console._buffer[:]
                del self._console._buffer[:]
                segments: ta.Iterable[Segment] = buffer
                if not self.styles:
                    segments = Segment.strip_styles(segments)
                elif not self.links:
                    segments = Segment.strip_links(segments)
                content = self._console._render_buffer(segments)
            self.pager.show(content)
        self._console._exit_buffer()


class ScreenContext:
    """A context manager that enables an alternative screen. See :meth:`~rich.console.Console.screen` for usage."""

    def __init__(
            self,
            console: Console,
            hide_cursor: bool,
            style: StyleType = '',
    ) -> None:
        self.console = console
        self.hide_cursor = hide_cursor
        self.screen = Screen(style=style)
        self._changed = False

    def update(
            self,
            *renderables: RenderableType,
            style: StyleType | None = None,
    ) -> None:
        """
        Update the screen.

        Args:
            renderable (RenderableType, optional): Optional renderable to replace current renderable, or None for no
                change. Defaults to None.
            style: (Style, optional): Replacement style, or None for no change. Defaults to None.
        """

        if renderables:
            self.screen.renderable = Group(*renderables) if len(renderables) > 1 else renderables[0]
        if style is not None:
            self.screen.style = style
        self.console.print(self.screen, end='')

    def __enter__(self) -> ta.Self:
        self._changed = self.console.set_alt_screen(True)
        if self._changed and self.hide_cursor:
            self.console.show_cursor(False)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        if self._changed:
            self.console.set_alt_screen(False)
            if self.hide_cursor:
                self.console.show_cursor(True)


class Group:
    """
    Takes a group of renderables and returns a renderable object that renders the group.

    Args:
        renderables (Iterable[RenderableType]): An iterable of renderable objects.
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def __init__(self, *renderables: RenderableType, fit: bool = True) -> None:
        self._renderables = renderables
        self.fit = fit
        self._render: list[RenderableType] | None = None

    @property
    def renderables(self) -> list[RenderableType]:
        if self._render is None:
            self._render = list(self._renderables)
        return self._render

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        if self.fit:
            return measure_renderables(console, options, self.renderables)
        else:
            return Measurement(options.max_width, options.max_width)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from self.renderables


def group(fit: bool = True) -> ta.Callable[..., ta.Callable[..., Group]]:
    """
    A decorator that turns an iterable of renderables in to a group.

    Args:
        fit (bool, optional): Fit dimension of group to contents, or fill available space. Defaults to True.
    """

    def decorator(
        method: ta.Callable[..., ta.Iterable[RenderableType]],
    ) -> ta.Callable[..., Group]:
        """Convert a method that returns an iterable of renderables in to a Group."""

        @functools.wraps(method)
        def _replace(*args: ta.Any, **kwargs: ta.Any) -> Group:
            renderables = method(*args, **kwargs)
            return Group(*renderables, fit=fit)

        return _replace

    return decorator


COLOR_SYSTEMS = {
    'standard': ColorSystem.STANDARD,
    '256': ColorSystem.EIGHT_BIT,
    'truecolor': ColorSystem.TRUECOLOR,
    'windows': ColorSystem.WINDOWS,
}

_COLOR_SYSTEMS_NAMES = {system: name for name, system in COLOR_SYSTEMS.items()}


@dc.dataclass()
class ConsoleThreadLocals(threading.local):
    """Thread local values for Console context."""

    theme_stack: ThemeStack
    buffer: list[Segment] = dc.field(default_factory=list)
    buffer_index: int = 0


class RenderHook(lang.Abstract):
    """Provides hooks in to the render process."""

    @abc.abstractmethod
    def process_renderables(
        self, renderables: list[ConsoleRenderable],
    ) -> list[ConsoleRenderable]:
        """
        Called with a list of objects to render.

        This method can return a new list of renderables, or modify and return the same list.

        Args:
            renderables (list[ConsoleRenderable]): A number of renderable objects.

        Returns:
            list[ConsoleRenderable]: A replacement list of renderables.
        """


class Console:
    """
    A high level console interface.

    Args:
        color_system (str, optional): The color system supported by your terminal,
            either ``"standard"``, ``"256"`` or ``"truecolor"``. Leave as ``"auto"`` to autodetect.
        force_terminal (Optional[bool], optional): Enable/disable terminal control codes, or None to auto-detect
            terminal. Defaults to None.
        force_interactive (Optional[bool], optional): Enable/disable interactive mode, or None to auto detect. Defaults
            to None.
        soft_wrap (Optional[bool], optional): Set soft wrap default on print method. Defaults to False.
        theme (Theme, optional): An optional style theme object, or ``None`` for default theme.
        stderr (bool, optional): Use stderr rather than stdout if ``file`` is not specified. Defaults to False.
        file (IO, optional): A file object where the console should write to. Defaults to stdout.
        quiet (bool, Optional): Boolean to suppress all output. Defaults to False.
        width (int, optional): The width of the terminal. Leave as default to auto-detect width.
        height (int, optional): The height of the terminal. Leave as default to auto-detect height.
        style (StyleType, optional): Style to apply to all output, or None for no style. Defaults to None.
        no_color (Optional[bool], optional): Enabled no color mode, or None to auto detect. Defaults to None.
        tab_size (int, optional): Number of spaces used to replace a tab character. Defaults to 8.
        record (bool, optional): Boolean to enable recording of terminal output,
            required to call :meth:`export_html`, :meth:`export_svg`, and :meth:`export_text`. Defaults to False.
        markup (bool, optional): Boolean to enable :ref:`console_markup`. Defaults to True.
        emoji (bool, optional): Enable emoji code. Defaults to True.
        emoji_variant (str, optional): Optional emoji variant, either "text" or "emoji". Defaults to None.
        highlight (bool, optional): Enable automatic highlighting. Defaults to True.
        highlighter (HighlighterType, optional): Default highlighter.
        safe_box (bool, optional): Restrict box options that don't render on legacy Windows.
        get_datetime (Callable[[], datetime.datetime], optional): Callable that gets the current time as a
            datetime.datetime object (used by Console.log), or None for datetime.now.
        get_time (Callable[[], time], optional): Callable that gets the current time in seconds, default uses
            time.monotonic.
    """

    _environ: ta.Mapping[str, str] = os.environ

    def __init__(
        self,
        *,
        color_system: ta.Literal['auto', 'standard', '256', 'truecolor', 'windows'] | None = 'auto',
        force_terminal: bool | None = None,
        force_interactive: bool | None = None,
        soft_wrap: bool = False,
        theme: Theme | None = None,
        stderr: bool = False,
        file: ta.IO[str] | None = None,
        quiet: bool = False,
        width: int | None = None,
        height: int | None = None,
        style: StyleType | None = None,
        no_color: bool | None = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        emoji_variant: EmojiVariant | None = None,
        highlight: bool = True,
        highlighter: HighlighterType | None = ReprHighlighter(),
        safe_box: bool = True,
        get_datetime: ta.Callable[[], datetime.datetime] | None = None,
        get_time: ta.Callable[[], float] | None = None,
        _environ: ta.Mapping[str, str] | None = None,
    ):
        # Copy of os.environ allows us to replace it for testing
        if _environ is not None:
            self._environ = _environ

        self.tab_size = tab_size
        self.record = record
        self._markup = markup
        self._emoji = emoji
        self._emoji_variant: EmojiVariant | None = emoji_variant
        self._highlight = highlight

        if width is None:
            columns = self._environ.get('COLUMNS')
            if columns is not None and columns.isdigit():
                width = int(columns)
        if height is None:
            lines = self._environ.get('LINES')
            if lines is not None and lines.isdigit():
                height = int(lines)

        self.soft_wrap = soft_wrap
        self._width = width
        self._height = height


        self._force_terminal = None
        if force_terminal is not None:
            self._force_terminal = force_terminal

        self._file = file
        self.quiet = quiet
        self.stderr = stderr

        if color_system is None:
            self._color_system: ColorSystem | None = None
        elif color_system == 'auto':
            self._color_system = self._detect_color_system()
        else:
            self._color_system = COLOR_SYSTEMS[color_system]

        self._lock = threading.RLock()
        self.highlighter: HighlighterType = highlighter or _null_highlighter
        self.safe_box = safe_box
        self.get_datetime = get_datetime or datetime.datetime.now
        self.get_time = get_time or time.monotonic
        self.style = style
        self.no_color = (
            no_color
            if no_color is not None
            else self._environ.get('NO_COLOR', '') != ''
        )
        if force_interactive is None:
            tty_interactive = self._environ.get('TTY_INTERACTIVE', None)
            if tty_interactive is not None:
                if tty_interactive == '0':
                    force_interactive = False
                elif tty_interactive == '1':
                    force_interactive = True

        self.is_interactive = (
            (self.is_terminal and not self.is_dumb_terminal)
            if force_interactive is None
            else force_interactive
        )

        self._record_buffer_lock = threading.RLock()
        self._thread_locals = ConsoleThreadLocals(
            theme_stack=ThemeStack(DEFAULT_THEME if theme is None else theme),
        )
        self._record_buffer: list[Segment] = []
        self._render_hooks: list[RenderHook] = []
        self._is_alt_screen = False

    def __repr__(self) -> str:
        return f'<console width={self.width} {self._color_system!s}>'

    @property
    def file(self) -> ta.IO[str]:
        """Get the file object to write to."""

        file = self._file or (sys.stderr if self.stderr else sys.stdout)
        file = getattr(file, 'rich_proxied_file', file)
        if file is None:
            file = NULL_FILE
        return file

    @file.setter
    def file(self, new_file: ta.IO[str]) -> None:
        """Set a new file object."""

        self._file = new_file

    @property
    def _buffer(self) -> list[Segment]:
        """Get a thread local buffer."""

        return self._thread_locals.buffer

    @property
    def _buffer_index(self) -> int:
        """Get a thread local buffer."""

        return self._thread_locals.buffer_index

    @_buffer_index.setter
    def _buffer_index(self, value: int) -> None:
        self._thread_locals.buffer_index = value

    @property
    def _theme_stack(self) -> ThemeStack:
        """Get the thread local theme stack."""

        return self._thread_locals.theme_stack

    def _detect_color_system(self) -> ColorSystem | None:
        """Detect color system from env vars."""

        if not self.is_terminal or self.is_dumb_terminal:
            return None
        color_term = self._environ.get('COLORTERM', '').strip().lower()
        if color_term in ('truecolor', '24bit'):
            return ColorSystem.TRUECOLOR
        term = self._environ.get('TERM', '').strip().lower()
        _term_name, _hyphen, colors = term.rpartition('-')
        color_system = _TERM_COLORS.get(colors, ColorSystem.STANDARD)
        return color_system

    def _enter_buffer(self) -> None:
        """Enter in to a buffer context, and buffer all output."""

        self._buffer_index += 1

    def _exit_buffer(self) -> None:
        """Leave buffer context, and render content if required."""

        self._buffer_index -= 1
        self._check_buffer()

    def push_render_hook(self, hook: RenderHook) -> None:
        """
        Add a new render hook to the stack.

        Args:
            hook (RenderHook): Render hook instance.
        """

        with self._lock:
            self._render_hooks.append(hook)

    def pop_render_hook(self) -> None:
        """Pop the last renderhook from the stack."""

        with self._lock:
            self._render_hooks.pop()

    def __enter__(self) -> ta.Self:
        """Own context manager to enter buffer context."""

        self._enter_buffer()
        return self

    def __exit__(self, exc_type: ta.Any, exc_value: ta.Any, traceback: ta.Any) -> None:
        """Exit buffer context."""

        self._exit_buffer()

    def begin_capture(self) -> None:
        """Begin capturing console output. Call :meth:`end_capture` to exit capture mode and return output."""

        self._enter_buffer()

    def end_capture(self) -> str:
        """
        End capture mode and return captured string.

        Returns:
            str: Console output.
        """

        render_result = self._render_buffer(self._buffer)
        del self._buffer[:]
        self._exit_buffer()
        return render_result

    def push_theme(self, theme: Theme, *, inherit: bool = True) -> None:
        """
        Push a new theme on to the top of the stack, replacing the styles from the previous theme. Generally speaking,
        you should call :meth:`~rich.console.Console.use_theme` to get a context manager, rather than calling this
        method directly.

        Args:
            theme (Theme): A theme instance.
            inherit (bool, optional): Inherit existing styles. Defaults to True.
        """

        self._theme_stack.push_theme(theme, inherit=inherit)

    def pop_theme(self) -> None:
        """Remove theme from top of stack, restoring previous theme."""

        self._theme_stack.pop_theme()

    def use_theme(self, theme: Theme, *, inherit: bool = True) -> ThemeContext:
        """
        Use a different theme for the duration of the context manager.

        Args:
            theme (Theme): Theme instance to user.
            inherit (bool, optional): Inherit existing console styles. Defaults to True.

        Returns:
            ThemeContext: [description]
        """

        return ThemeContext(self, theme, inherit)

    @property
    def color_system(self) -> str | None:
        """
        Get color system string.

        Returns:
            Optional[str]: "standard", "256" or "truecolor".
        """

        if self._color_system is not None:
            return _COLOR_SYSTEMS_NAMES[self._color_system]
        else:
            return None

    @property
    def encoding(self) -> str:
        """
        Get the encoding of the console file, e.g. ``"utf-8"``.

        Returns:
            str: A standard encoding string.
        """

        return (getattr(self.file, 'encoding', 'utf-8') or 'utf-8').lower()

    @property
    def is_terminal(self) -> bool:
        """
        Check if the console is writing to a terminal.

        Returns:
            bool: True if the console writing to a device capable of understanding escape sequences, otherwise False.
        """

        # If dev has explicitly set this value, return it
        if self._force_terminal is not None:
            return self._force_terminal

        # Fudge for Idle
        if hasattr(sys.stdin, '__module__') and sys.stdin.__module__.startswith('idlelib'):
            # Return False for Idle which claims to be a tty but can't handle ansi codes
            return False

        environ = self._environ

        tty_compatible = environ.get('TTY_COMPATIBLE', '')
        # 0 indicates device is not tty compatible
        if tty_compatible == '0':
            return False
        # 1 indicates device is tty compatible
        if tty_compatible == '1':
            return True

        # https://force-color.org/
        force_color = environ.get('FORCE_COLOR')
        if force_color is not None:
            return force_color != ''

        # Any other value defaults to auto detect
        isatty: ta.Callable[[], bool] | None = getattr(self.file, 'isatty', None)
        try:
            return False if isatty is None else isatty()
        except ValueError:
            # In some situations (at the end of a pytest run for example) isatty() can raise ValueError: I/O operation
            # on closed file. Return False because we aren't in a terminal anymore
            return False

    @property
    def is_dumb_terminal(self) -> bool:
        """
        Detect dumb terminal.

        Returns:
            bool: True if writing to a dumb terminal, otherwise False.
        """

        _term = self._environ.get('TERM', '')
        is_dumb = _term.lower() in ('dumb', 'unknown')
        return self.is_terminal and is_dumb

    @property
    def options(self) -> ConsoleOptions:
        """Get default console options."""

        size = self.size
        return ConsoleOptions(
            max_height=size.height,
            size=size,
            min_width=1,
            max_width=size.width,
            encoding=self.encoding,
            is_terminal=self.is_terminal,
        )

    @property
    def size(self) -> ConsoleDimensions:
        """
        Get the size of the console.

        Returns:
            ConsoleDimensions: A named tuple containing the dimensions.
        """

        if self._width is not None and self._height is not None:
            return ConsoleDimensions(self._width, self._height)

        if self.is_dumb_terminal:
            return ConsoleDimensions(80, 25)

        width: int | None = None
        height: int | None = None

        streams = _STD_STREAMS
        for file_descriptor in streams:
            try:
                width, height = os.get_terminal_size(file_descriptor)
            except (AttributeError, ValueError, OSError):  # Probably not a terminal
                pass
            else:
                break

        columns = self._environ.get('COLUMNS')
        if columns is not None and columns.isdigit():
            width = int(columns)
        lines = self._environ.get('LINES')
        if lines is not None and lines.isdigit():
            height = int(lines)

        # get_terminal_size can report 0, 0 if run from pseudo-terminal
        width = width or 80
        height = height or 25
        return ConsoleDimensions(
            width - 0 if self._width is None else self._width,
            height if self._height is None else self._height,
        )

    @size.setter
    def size(self, new_size: tuple[int, int]) -> None:
        """
        Set a new size for the terminal.

        Args:
            new_size (tuple[int, int]): New width and height.
        """

        width, height = new_size
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        """
        Get the width of the console.

        Returns:
            int: The width (in characters) of the console.
        """

        return self.size.width

    @width.setter
    def width(self, width: int) -> None:
        """
        Set width.

        Args:
            width (int): New width.
        """

        self._width = width

    @property
    def height(self) -> int:
        """
        Get the height of the console.

        Returns:
            int: The height (in lines) of the console.
        """

        return self.size.height

    @height.setter
    def height(self, height: int) -> None:
        """
        Set height.

        Args:
            height (int): new height.
        """

        self._height = height

    def bell(self) -> None:
        """Play a 'bell' sound (if supported by the terminal)."""

        self.control(Control.bell())

    def capture(self) -> Capture:
        """
        A context manager to *capture* the result of print() or log() in a string, rather than writing it to the
        console.

        Example:
            >>> from rich.console import Console
            >>> console = Console()
            >>> with console.capture() as capture:
            ...     console.print("[bold magenta]Hello World[/]")
            >>> print(capture.get())

        Returns:
            Capture: Context manager with disables writing to the terminal.
        """

        capture = Capture(self)
        return capture

    def pager(
        self, pager: Pager | None = None, styles: bool = False, links: bool = False,
    ) -> PagerContext:
        """
        A context manager to display anything printed within a "pager". The pager application
        is defined by the system and will typically support at least pressing a key to scroll.

        Args:
            pager (Pager, optional): A pager object, or None to use :class:`~rich.pager.SystemPager`. Defaults to None.
            styles (bool, optional): Show styles in pager. Defaults to False.
            links (bool, optional): Show links in pager. Defaults to False.

        Example:
            >>> from rich.console import Console
            >>> from rich.__main__ import make_test_card
            >>> console = Console()
            >>> with console.pager():
                    console.print(make_test_card())

        Returns:
            PagerContext: A context manager.
        """

        return PagerContext(self, pager=pager, styles=styles, links=links)

    def line(self, count: int = 1) -> None:
        """
        Write new line(s).

        Args:
            count (int, optional): Number of new lines. Defaults to 1.
        """

        check.arg(count >= 0, 'count must be >= 0')
        self.print(NewLine(count))

    def clear(self, home: bool = True) -> None:
        """
        Clear the screen.

        Args:
            home (bool, optional): Also move the cursor to 'home' position. Defaults to True.
        """

        if home:
            self.control(Control.clear(), Control.home())
        else:
            self.control(Control.clear())

    def show_cursor(self, show: bool = True) -> bool:
        """
        Show or hide the cursor.

        Args:
            show (bool, optional): Set visibility of the cursor.
        """

        if self.is_terminal:
            self.control(Control.show_cursor(show))
            return True
        return False

    def set_alt_screen(self, enable: bool = True) -> bool:
        """
        Enables alternative screen mode.

        Note, if you enable this mode, you should ensure that is disabled before the application exits. See
        :meth:`~rich.Console.screen` for a context manager that handles this for you.

        Args:
            enable (bool, optional): Enable (True) or disable (False) alternate screen. Defaults to True.

        Returns:
            bool: True if the control codes were written.
        """

        changed = False
        if self.is_terminal:
            self.control(Control.alt_screen(enable))
            changed = True
            self._is_alt_screen = enable
        return changed

    @property
    def is_alt_screen(self) -> bool:
        """
        Check if the alt screen was enabled.

        Returns:
            bool: True if the alt screen was enabled, otherwise False.
        """

        return self._is_alt_screen

    def set_window_title(self, title: str) -> bool:
        """
        Set the title of the console terminal window.

        Warning: There is no means within Rich of "resetting" the window title to its previous value, meaning the title
        you set will persist even after your application exits.

        ``fish`` shell resets the window title before and after each command by default, negating this issue. Windows
        Terminal and command prompt will also reset the title for you. Most other shells and terminals, however, do not
        do this.

        Some terminals may require configuration changes before you can set the title. Some terminals may not support
        setting the title at all.

        Other software (including the terminal itself, the shell, custom prompts, plugins, etc.) may also set the
        terminal window title. This could result in whatever value you write using this method being overwritten.

        Args:
            title (str): The new title of the terminal window.

        Returns:
            bool: True if the control code to change the terminal title was
                written, otherwise False. Note that a return value of True
                does not guarantee that the window title has actually changed,
                since the feature may be unsupported/disabled in some terminals.
        """

        if self.is_terminal:
            self.control(Control.title(title))
            return True
        return False

    def screen(
            self,
            hide_cursor: bool = True,
            style: StyleType | None = None,
    ) -> ScreenContext:
        """
        Context manager to enable and disable 'alternative screen' mode.

        Args:
            hide_cursor (bool, optional): Also hide the cursor. Defaults to False.
            style (Style, optional): Optional style for screen. Defaults to None.

        Returns:
            ~ScreenContext: Context which enables alternate screen on enter, and disables it on exit.
        """

        return ScreenContext(self, hide_cursor=hide_cursor, style=style or '')

    def measure(
        self, renderable: RenderableType, *, options: ConsoleOptions | None = None,
    ) -> Measurement:
        """
        Measure a renderable. Returns a :class:`~rich.measure.Measurement` object which contains information regarding
        the number of characters required to print the renderable.

        Args:
            renderable (RenderableType): Any renderable or string.
            options (Optional[ConsoleOptions], optional): Options to use when measuring, or None
                to use default options. Defaults to None.

        Returns:
            Measurement: A measurement of the renderable.
        """

        measurement = Measurement.get(self, options or self.options, renderable)
        return measurement

    def render(
            self,
            renderable: RenderableType,
            options: ConsoleOptions | None = None,
    ) -> ta.Iterable[Segment]:
        """
        Render an object in to an iterable of `Segment` instances.

        This method contains the logic for rendering objects with the console protocol. You are unlikely to need to use
        it directly, unless you are extending the library.

        Args:
            renderable (RenderableType): An object supporting the console protocol, or
                an object that may be converted to a string.
            options (ConsoleOptions, optional): An options object, or None to use self.options. Defaults to None.

        Returns:
            Iterable[Segment]: An iterable of segments that may be rendered.
        """

        _options = options or self.options
        if _options.max_width < 1:
            # No space to render anything. This prevents potential recursion errors.
            return
        render_iterable: RenderResult

        renderable = rich_cast(renderable)
        if hasattr(renderable, '__rich_console__') and not isinstance(renderable, type):
            render_iterable = renderable.__rich_console__(self, _options)
        elif isinstance(renderable, str):
            text_renderable = self.render_str(
                renderable,
                highlight=_options.highlight,
                markup=_options.markup,
            )
            render_iterable = text_renderable.__rich_console__(self, _options)
        else:
            raise NotRenderableError(
                f'Unable to render {renderable!r}; '
                'A str, Segment or object with __rich_console__ method is required',
            )

        try:
            iter_render = iter(render_iterable)
        except TypeError:
            raise NotRenderableError(
                f'object {render_iterable!r} is not renderable',
            )
        _segment = Segment
        _options = _options.reset_height()
        for render_output in iter_render:
            if isinstance(render_output, _segment):
                yield render_output
            else:
                yield from self.render(render_output, _options)

    def render_lines(
        self,
        renderable: RenderableType,
        options: ConsoleOptions | None = None,
        *,
        style: Style | None = None,
        pad: bool = True,
        new_lines: bool = False,
    ) -> list[list[Segment]]:
        """
        Render objects in to a list of lines.

        The output of render_lines is useful when further formatting of rendered console text is required, such as the
        Panel class which draws a border around any renderable object.

        Args:
            renderable (RenderableType): Any object renderable in the console.
            options (Optional[ConsoleOptions], optional): Console options, or None to use self.options. Default to
                ``None``.
            style (Style, optional): Optional style to apply to renderables. Defaults to ``None``.
            pad (bool, optional): Pad lines shorter than render width. Defaults to ``True``.
            new_lines (bool, optional): Include "\n" characters at end of lines.

        Returns:
            list[list[Segment]]: A list of lines, where a line is a list of Segment objects.
        """

        with self._lock:
            render_options = options or self.options
            _rendered = self.render(renderable, render_options)
            if style:
                _rendered = Segment.apply_style(_rendered, style)

            render_height = render_options.height
            if render_height is not None:
                render_height = max(0, render_height)

            lines = list(
                itertools.islice(
                    Segment.split_and_crop_lines(
                        _rendered,
                        render_options.max_width,
                        include_new_lines=new_lines,
                        pad=pad,
                        style=style,
                    ),
                    None,
                    render_height,
                ),
            )

            if render_options.height is not None:
                extra_lines = render_options.height - len(lines)
                if extra_lines > 0:
                    pad_line = [
                        (
                            [
                                Segment(' ' * render_options.max_width, style),
                                Segment('\n'),
                            ]
                            if new_lines else
                            [
                                Segment(' ' * render_options.max_width, style),
                            ]
                        ),
                    ]
                    lines.extend(pad_line * extra_lines)

            return lines

    def render_str(
        self,
        text: str,
        *,
        style: str | Style = '',
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        highlighter: HighlighterType | None = None,
    ) -> Text:
        """
        Convert a string to a Text instance. This is called automatically if
        you print or log a string.

        Args:
            text (str): Text to render.
            style (Union[str, Style], optional): Style to apply to rendered text.
            justify (str, optional): Justify method: "default", "left", "center", "full", or "right". Defaults to
                ``None``.
            overflow (str, optional): Overflow method: "crop", "fold", or "ellipsis". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji, or ``None`` to use Console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use Console default.
            highlight (Optional[bool], optional): Enable highlighting, or ``None`` to use Console default.
            highlighter (HighlighterType, optional): Optional highlighter to apply.

        Returns:
            ConsoleRenderable: Renderable object.
        """

        emoji_enabled = emoji or (emoji is None and self._emoji)
        markup_enabled = markup or (markup is None and self._markup)
        highlight_enabled = highlight or (highlight is None and self._highlight)

        if markup_enabled:
            rich_text = render_markup(
                text,
                style=style,
                emoji=emoji_enabled,
                emoji_variant=self._emoji_variant,
            )
            rich_text.justify = justify
            rich_text.overflow = overflow
        else:
            rich_text = Text(
                (
                    emoji_replace(text, default_variant=self._emoji_variant)
                    if emoji_enabled else
                    text
                ),
                justify=justify,
                overflow=overflow,
                style=style,
            )

        _highlighter = (highlighter or self.highlighter) if highlight_enabled else None
        if _highlighter is not None:
            highlight_text = _highlighter(str(rich_text))
            highlight_text.copy_styles(rich_text)
            return highlight_text

        return rich_text

    def get_style(
            self,
            name: str | Style,
            *,
            default: Style | str | None = None,
    ) -> Style:
        """
        Get a Style instance by its theme name or parse a definition.

        Args:
            name (str): The name of a style or a style definition.

        Returns:
            Style: A Style object.

        Raises:
            MissingStyle: If no style could be parsed from name.
        """

        if isinstance(name, Style):
            return name

        try:
            style = self._theme_stack.get(name)
            if style is None:
                style = Style.parse(name)
            return style.copy() if style.link else style
        except StyleSyntaxError as error:
            if default is not None:
                return self.get_style(default)
            raise MissingStyleError(f'Failed to get style {name!r}; {error}') from None

    def _collect_renderables(
            self,
            objects: ta.Iterable[ta.Any],
            sep: str,
            end: str,
            *,
            justify: JustifyMethod | None = None,
            emoji: bool | None = None,
            markup: bool | None = None,
            highlight: bool | None = None,
    ) -> list[ConsoleRenderable]:
        """
        Combine a number of renderables and text into one renderable.

        Args:
            objects (Iterable[Any]): Anything that Rich can render.
            sep (str): String to write between print data.
            end (str): String to write at end of print data.
            justify (str, optional): One of "left", "right", "center", or "full". Defaults to ``None``.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.

        Returns:
            list[ConsoleRenderable]: A list of things to render.
        """

        renderables: list[ConsoleRenderable] = []
        _append = renderables.append
        text: list[Text] = []
        append_text = text.append

        append = _append
        if justify in ('left', 'center', 'right'):

            def align_append(renderable: RenderableType) -> None:
                _append(Align(renderable, justify))

            append = align_append

        _highlighter: HighlighterType = _null_highlighter
        if highlight or (highlight is None and self._highlight):
            _highlighter = self.highlighter

        def check_text() -> None:
            if text:
                sep_text = Text(sep, justify=justify, end=end)
                append(sep_text.join(text))
                text.clear()

        for renderable in objects:
            renderable = rich_cast(renderable)
            if isinstance(renderable, str):
                append_text(
                    self.render_str(
                        renderable,
                        emoji=emoji,
                        markup=markup,
                        highlight=highlight,
                        highlighter=_highlighter,
                    ),
                )
            elif isinstance(renderable, Text):
                append_text(renderable)
            elif isinstance(renderable, ConsoleRenderable):
                check_text()
                append(renderable)
            else:
                append_text(_highlighter(str(renderable)))

        check_text()

        if self.style is not None:
            style = self.get_style(self.style)
            renderables = [Styled(renderable, style) for renderable in renderables]

        return renderables

    def control(self, *control: Control) -> None:
        """
        Insert non-printing control codes.

        Args:
            control_codes (str): Control codes, such as those that may move the cursor.
        """

        if not self.is_dumb_terminal:
            with self:
                self._buffer.extend(_control.segment for _control in control)

    def out(
        self,
        *objects: ta.Any,
        sep: str = ' ',
        end: str = '\n',
        style: str | Style | None = None,
        highlight: bool | None = None,
    ) -> None:
        """
        Output to the terminal. This is a low-level way of writing to the terminal which unlike
        :meth:`~rich.console.Console.print` won't pretty print, wrap text, or apply markup, but will optionally apply
        highlighting and a basic style.

        Args:
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.
                Defaults to ``None``.
        """

        raw_output: str = sep.join(str(_object) for _object in objects)
        self.print(
            raw_output,
            style=style,
            highlight=highlight,
            emoji=False,
            markup=False,
            no_wrap=True,
            overflow='ignore',
            crop=False,
            end=end,
        )

    def print(
        self,
        *objects: ta.Any,
        sep: str = ' ',
        end: str = '\n',
        style: str | Style | None = None,
        justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = None,
        emoji: bool | None = None,
        markup: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        crop: bool = True,
        soft_wrap: bool | None = None,
        new_line_start: bool = False,
    ) -> None:
        """
        Print to the console.

        Args:
            objects (positional args): Objects to log to the terminal.
            sep (str, optional): String to write between print data. Defaults to " ".
            end (str, optional): String to write at end of print data. Defaults to "\\\\n".
            style (Union[str, Style], optional): A style to apply to output. Defaults to None.
            justify (str, optional): Justify method: "default", "left", "right", "center", or "full". Defaults to
                ``None``.
            overflow (str, optional): Overflow method: "ignore", "crop", "fold", or "ellipsis". Defaults to None.
            no_wrap (Optional[bool], optional): Disable word wrapping. Defaults to None.
            emoji (Optional[bool], optional): Enable emoji code, or ``None`` to use console default. Defaults to
                ``None``.
            markup (Optional[bool], optional): Enable markup, or ``None`` to use console default. Defaults to ``None``.
            highlight (Optional[bool], optional): Enable automatic highlighting, or ``None`` to use console default.
                Defaults to ``None``.
            width (Optional[int], optional): Width of output, or ``None`` to auto-detect. Defaults to ``None``.
            crop (Optional[bool], optional): Crop output to width of terminal. Defaults to True.
            soft_wrap (bool, optional): Enable soft wrap mode which disables word wrapping and cropping of text or
                ``None`` for Console default. Defaults to ``None``.
            new_line_start (bool, False): Insert a new line at the start if the output contains more than one line.
                Defaults to ``False``.
        """

        if not objects:
            if end == '\n':
                objects = (NewLine(),)
            else:
                objects = ('',)

        if soft_wrap is None:
            soft_wrap = self.soft_wrap
        if soft_wrap:
            if no_wrap is None:
                no_wrap = True
            if overflow is None:
                overflow = 'ignore'
            crop = False

        render_hooks = self._render_hooks[:]

        with self:
            renderables = self._collect_renderables(
                objects,
                sep,
                end,
                justify=justify,
                emoji=emoji,
                markup=markup,
                highlight=highlight,
            )

            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)

            render_options = self.options.update(
                justify=justify,
                overflow=overflow,
                width=min(width, self.width) if width is not None else NO_CHANGE,
                height=height,
                no_wrap=no_wrap,
                markup=markup,
                highlight=highlight,
            )

            new_segments: list[Segment] = []
            extend = new_segments.extend
            render = self.render
            if style is None:
                for renderable in renderables:
                    extend(render(renderable, render_options))
            else:
                render_style = self.get_style(style)
                new_line = Segment.line()
                for renderable in renderables:
                    for line, add_new_line in Segment.split_lines_terminator(
                        render(renderable, render_options),
                    ):
                        extend(Segment.apply_style(line, render_style))
                        if add_new_line:
                            new_segments.append(new_line)

            if new_line_start:
                if (
                    len(''.join(segment.text for segment in new_segments).splitlines())
                    > 1
                ):
                    new_segments.insert(0, Segment.line())
            if crop:
                buffer_extend = self._buffer.extend
                for line in Segment.split_and_crop_lines(
                    new_segments, self.width, pad=False,
                ):
                    buffer_extend(line)
            else:
                self._buffer.extend(new_segments)

    def update_screen(
        self,
        renderable: RenderableType,
        *,
        region: Region | None = None,
        options: ConsoleOptions | None = None,
    ) -> None:
        """
        Update the screen at a given offset.

        Args:
            renderable (RenderableType): A Rich renderable.
            region (Region, optional): Region of screen to update, or None for entire screen. Defaults to None.
            x (int, optional): x offset. Defaults to 0.
            y (int, optional): y offset. Defaults to 0.

        Raises:
            NoAltScreen: If the Console isn't in alt screen mode.
        """

        if not self.is_alt_screen:
            raise NoAltScreenError('Alt screen must be enabled to call update_screen')
        render_options = options or self.options
        if region is None:
            x = y = 0
            render_options = render_options.update_dimensions(
                render_options.max_width, render_options.height or self.height,
            )
        else:
            x, y, width, height = region
            render_options = render_options.update_dimensions(width, height)

        lines = self.render_lines(renderable, options=render_options)
        self.update_screen_lines(lines, x, y)

    def update_screen_lines(
            self,
            lines: list[list[Segment]],
            x: int = 0,
            y: int = 0,
    ) -> None:
        """
        Update lines of the screen at a given offset.

        Args:
            lines (list[list[Segment]]): Rendered lines (as produced by :meth:`~rich.Console.render_lines`).
            x (int, optional): x offset (column no). Defaults to 0.
            y (int, optional): y offset (column no). Defaults to 0.

        Raises:
            NoAltScreen: If the Console isn't in alt screen mode.
        """

        if not self.is_alt_screen:
            raise NoAltScreenError('Alt screen must be enabled to call update_screen')
        screen_update = ScreenUpdate(lines, x, y)
        segments = self.render(screen_update)
        self._buffer.extend(segments)
        self._check_buffer()

    def on_broken_pipe(self) -> None:
        """
        This function is called when a `BrokenPipeError` is raised.

        This can occur when piping Textual output in Linux and macOS. The default implementation is to exit the app, but
        you could implement this method in a subclass to change the behavior.

        See https://docs.python.org/3/library/signal.html#note-on-sigpipe for details.
        """

        self.quiet = True
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        raise SystemExit(1)

    def _check_buffer(self) -> None:
        """
        Check if the buffer may be rendered. Render it if it can (e.g. Console.quiet is False) Rendering is supported on
        Unix environments. This method will also record what it renders if recording is enabled via Console.record.
        """

        if self.quiet:
            del self._buffer[:]
            return

        try:
            self._write_buffer()
        except BrokenPipeError:
            self.on_broken_pipe()

    def _write_buffer(self) -> None:
        """Write the buffer to the output file."""

        with self._lock:
            if self.record and not self._buffer_index:
                with self._record_buffer_lock:
                    self._record_buffer.extend(self._buffer[:])

            if self._buffer_index == 0:
                text = self._render_buffer(self._buffer[:])
                try:
                    self.file.write(text)
                except UnicodeEncodeError as error:
                    error.reason = (
                        f'{error.reason}\n'
                        f'*** You may need to add PYTHONIOENCODING=utf-8 to your environment ***'
                    )
                    raise

                self.file.flush()
                del self._buffer[:]

    def _render_buffer(self, buffer: ta.Iterable[Segment]) -> str:
        """Render buffered output, and clear buffer."""

        output: list[str] = []
        append = output.append
        color_system = self._color_system
        not_terminal = not self.is_terminal
        if self.no_color and color_system:
            buffer = Segment.remove_color(buffer)
        for text, style, control in buffer:
            if style:
                append(
                    style.render(
                        text,
                        color_system=color_system,
                    ),
                )
            elif not (not_terminal and control):
                append(text)

        rendered = ''.join(output)
        return rendered

    def input(
        self,
        prompt: TextType = '',
        *,
        markup: bool = True,
        emoji: bool = True,
        password: bool = False,
        stream: ta.TextIO | None = None,
    ) -> str:
        """
        Displays a prompt and waits for input from the user. The prompt may contain color / style.

        It works in the same way as Python's builtin :func:`input` function and provides elaborate line editing and
        history features if Python's builtin :mod:`readline` module is previously loaded.

        Args:
            prompt (Union[str, Text]): Text to render in the prompt.
            markup (bool, optional): Enable console markup (requires a str prompt). Defaults to True.
            emoji (bool, optional): Enable emoji (requires a str prompt). Defaults to True.
            password: (bool, optional): Hide typed text. Defaults to False.
            stream: (TextIO, optional): Optional file to read input from (rather than stdin). Defaults to None.

        Returns:
            str: Text read from stdin.
        """

        if prompt:
            self.print(prompt, markup=markup, emoji=emoji, end='')
        if password:
            import getpass as _getpass_mod

            result = _getpass_mod.getpass('', stream=stream)
        elif stream:
            result = stream.readline()
        else:
            result = input()
        return result
