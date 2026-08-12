import collections
import dataclasses as dc
import functools
import re
import typing as ta
import unicodedata

from .types import CharBuffer
from .types import CharWidths


##


ANSI_ESCAPE_SEQUENCE = re.compile(r'\x1b\[[ -@]*[A-~]')


##


class StyledChar(ta.NamedTuple):
    text: str
    width: int
    tag: str | None = None


def _ascii_control_repr(c: str) -> str | None:
    code = ord(c)
    if code < 32:
        return '^' + chr(code + 64)
    if code == 127:
        return '^?'
    return None


@functools.cache
def str_width(c: str) -> int:
    if ord(c) < 128:
        return 1
    # gh-139246 for zero-width joiner and combining characters
    if unicodedata.combining(c):
        return 0
    category = unicodedata.category(c)
    if category == 'Cf' and c != '\u00ad':
        return 0
    w = unicodedata.east_asian_width(c)
    if w in ('N', 'Na', 'H', 'A'):
        return 1
    return 2


def wlen(s: str) -> int:
    if len(s) == 1 and s != '\x1a':
        return str_width(s)
    length = sum(str_width(i) for i in s)
    # remove lengths of any escape sequences
    sequence = ANSI_ESCAPE_SEQUENCE.findall(s)
    ctrl_z_cnt = s.count('\x1a')
    return length - sum(len(i) for i in sequence) + ctrl_z_cnt


##


ZERO_WIDTH_BRACKET = re.compile(r'\x01.*?\x02')
ZERO_WIDTH_TRANS = str.maketrans({'\x01': '', '\x02': ''})


def unbracket(s: str, including_content: bool = False) -> str:
    r"""
    Return `s` with \001 and \002 characters removed.

    If `including_content` is True, content between \001 and \002 is also stripped.
    """

    if including_content:
        return ZERO_WIDTH_BRACKET.sub('', s)
    return s.translate(ZERO_WIDTH_TRANS)


##


class Span(ta.NamedTuple):
    """Span indexing that's inclusive on both ends."""

    start: int
    end: int

    @classmethod
    def from_re(cls, m: ta.Match[str], group: int | str) -> ta.Self:
        re_span = m.span(group)
        return cls(re_span[0], re_span[1] - 1)


class ColorSpan(ta.NamedTuple):
    span: Span
    tag: str


##


class ColorCodes(ta.Protocol):
    def __getitem__(self, tag: str) -> str: ...

    @property
    def reset(self) -> str: ...


class NoColorCodes:
    def __getitem__(self, tag: str) -> str:
        return ''

    @property
    def reset(self) -> str:
        return ''


class AnsiColorCodes:
    CODES: ta.ClassVar[ta.Mapping[str, str]] = {
        'prompt': '\x1b[1;35m',
    }

    def __getitem__(self, tag: str) -> str:
        return self.CODES.get(tag, '')

    @property
    def reset(self) -> str:
        return '\x1b[0m'


def color_codes() -> ColorCodes:
    # return NoColorCodes()
    return AnsiColorCodes()


##


def iter_display_chars(
    buffer: str,
    colors: list[ColorSpan] | None = None,
    start_index: int = 0,
) -> ta.Iterator[StyledChar]:
    """
    Yield visible display characters with widths and semantic color tags.

    Note: ``colors`` is consumed in place as spans are processed -- callers that split a buffer across multiple calls
    rely on this mutation to track which spans have already been handled.
    """

    if not buffer:
        return

    color_idx = 0
    if colors:
        while color_idx < len(colors) and colors[color_idx].span.end < start_index:
            color_idx += 1

    active_tag = None
    if colors and color_idx < len(colors) and colors[color_idx].span.start < start_index:
        active_tag = colors[color_idx].tag

    for i, c in enumerate(buffer, start_index):
        if colors and color_idx < len(colors) and colors[color_idx].span.start == i:
            active_tag = colors[color_idx].tag

        if control := _ascii_control_repr(c):
            text = control
            width = len(control)
        elif ord(c) < 128:
            text = c
            width = 1
        elif unicodedata.category(c).startswith('C'):
            text = rf'\u{ord(c):04x}'
            width = len(text)
        else:
            text = c
            width = str_width(c)

        yield StyledChar(text, width, active_tag)

        if colors and color_idx < len(colors) and colors[color_idx].span.end == i:
            color_idx += 1
            active_tag = None
            # Check if the next span starts at the same position
            if color_idx < len(colors) and colors[color_idx].span.start == i:
                active_tag = colors[color_idx].tag

    # Remove consumed spans so callers see the mutation
    if color_idx > 0 and colors:
        del colors[:color_idx]


def disp_str(
        buffer: str,
        colors: list[ColorSpan] | None = None,
        start_index: int = 0,
        color_codes: ColorCodes = NoColorCodes(),
) -> tuple[CharBuffer, CharWidths]:
    r"""
    Decompose the input buffer into a printable variant with applied colors.

    Returns a tuple of two lists:
    - the first list is the input buffer, character by character, with color escape codes added (while those codes
      contain multiple ASCII characters, each code is considered atomic *and is attached for the corresponding visible
      character*);
    - the second list is the visible width of each character in the input buffer.

    Note on colors:
    - The `colors` list, if provided, is partially consumed within. We're using a list and not a generator since we need
      to hold onto the current unfinished span between calls to disp_str in case of multiline strings.
    - The `colors` list is computed from the start of the input block. `buffer` is only a subset of that input block, a
      single line within. This is why we need `start_index` to inform us which position is the start of `buffer`
      actually within user input. This allows us to match color spans correctly.

    Examples:
    >>> utils.disp_str("a = 9")
    (['a', ' ', '=', ' ', '9'], [1, 1, 1, 1, 1])

    >>> line = "while 1:"
    >>> colors = list(utils.gen_colors(line))
    >>> utils.disp_str(line, colors=colors)
    (['\x1b[1;34mw', 'h', 'i', 'l', 'e\x1b[0m', ' ', '1', ':'], [1, 1, 1, 1, 1, 1, 1, 1])

    """

    styled_chars = list(iter_display_chars(buffer, colors, start_index))
    chars: CharBuffer = []
    char_widths: CharWidths = []

    for index, styled_char in enumerate(styled_chars):
        previous_tag = styled_chars[index - 1].tag if index else None
        next_tag = styled_chars[index + 1].tag if index + 1 < len(styled_chars) else None
        prefix = color_codes[styled_char.tag] if styled_char.tag and styled_char.tag != previous_tag else ''
        suffix = color_codes.reset if styled_char.tag and styled_char.tag != next_tag else ''
        chars.append(prefix + styled_char.text + suffix)
        char_widths.append(styled_char.width)

    return chars, char_widths


def prev_next_window[T](
    iterable: ta.Iterable[T],
) -> ta.Iterator[tuple[T | None, ...]]:
    """
    Generates three-tuples of (previous, current, next) items.

    On the first iteration previous is None. On the last iteration next is None. In case of exception next is None and
    the exception is re-raised on a subsequent next() call.

    Inspired by `sliding_window` from `itertools` recipes.
    """

    iterator = iter(iterable)
    try:
        first = next(iterator)
    except StopIteration:
        return
    window = collections.deque((None, first), maxlen=3)
    try:
        for x in iterator:
            window.append(x)
            yield tuple(window)
    finally:
        window.append(None)
        yield tuple(window)


@dc.dataclass(frozen=True, slots=True)
class StyleRef:
    tag: str | None = None  # From THEME().syntax, e.g. "keyword", "builtin"
    sgr: str = ''

    @classmethod
    def from_tag(cls, tag: str, sgr: str = '') -> ta.Self:
        return cls(tag=tag, sgr=sgr)

    @classmethod
    def from_sgr(cls, sgr: str) -> ta.Self:
        if not sgr:
            return cls()
        return cls(sgr=sgr)

    @property
    def is_plain(self) -> bool:
        return self.tag is None and not self.sgr
