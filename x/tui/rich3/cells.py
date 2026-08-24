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
import functools
import operator
import typing as ta

from ._data.unicode import CELL_TABLE
from ._utils.loops import loop_last
from ._utils.text import iter_words


CellSpan: ta.TypeAlias = tuple[int, int, int]


##


_span_get_cell_len = operator.itemgetter(2)

# Ranges of unicode ordinals that produce a 1-cell wide character. This is non-exhaustive, but covers most common
# Western characters.
_SINGLE_CELL_UNICODE_RANGES: list[tuple[int, int]] = [
    (0x20, 0x7E),  # Latin (excluding non-printable)
    (0xA0, 0xAC),
    (0xAE, 0x002FF),
    (0x00370, 0x00482),  # Greek / Cyrillic
    (0x02500, 0x025FC),  # Box drawing, box elements, geometric shapes
    (0x02800, 0x028FF),  # Braille
]


# A frozen set of characters that are a single cell wide
_SINGLE_CELLS = frozenset([
    character
    for _start, _end in _SINGLE_CELL_UNICODE_RANGES
    for character in map(chr, range(_start, _end + 1))
])


# When called with a string this will return True if all characters are single-cell, otherwise False
_is_single_cell_widths: ta.Callable[[str], bool] = _SINGLE_CELLS.issuperset


class CellTable(ta.NamedTuple):
    """Contains unicode data required to measure the cell widths of glyphs."""

    unicode_version: str
    widths: ta.Sequence[tuple[int, int, int]]
    narrow_to_wide: frozenset[str]


@functools.lru_cache(maxsize=4096)
def get_character_cell_size(character: str) -> int:
    """
    Get the cell size of a character.

    Args:
        character (str): A single character.

    Returns:
        int: Number of cells (0, 1 or 2) occupied by that character.
    """

    codepoint = ord(character)
    if (codepoint and codepoint < 32) or 0x07F <= codepoint < 0x0A0:
        return 0
    table = CELL_TABLE.widths

    last_entry = table[-1]
    if codepoint > last_entry[1]:
        return 1

    lower_bound = 0
    upper_bound = len(table) - 1

    while lower_bound <= upper_bound:
        index = (lower_bound + upper_bound) >> 1
        start, end, width = table[index]
        if codepoint < start:
            upper_bound = index - 1
        elif codepoint > end:
            lower_bound = index + 1
        else:
            return width
    return 1


@functools.lru_cache(4096)
def cached_cell_len(text: str) -> int:
    """
    Get the number of cells required to display text.

    This method always caches, which may use up a lot of memory. It is recommended to use `cell_len` over this method.

    Args:
        text (str): Text to display.

    Returns:
        int: Get the number of cells required to display text.
    """

    return _cell_len(text)


def cell_len(text: str) -> int:
    """
    Get the cell length of a string (length as it appears in the terminal).

    Args:
        text: String to measure.

    Returns:
        Length of string in terminal cells.
    """

    if len(text) < 512:
        return cached_cell_len(text)
    return _cell_len(text)


def _cell_len(text: str) -> int:
    """
    Get the cell length of a string (length as it appears in the terminal).

    Args:
        text: String to measure.

    Returns:
        Length of string in terminal cells.
    """

    if _is_single_cell_widths(text):
        return len(text)

    # "\u200d" is zero width joiner
    # "\ufe0f" is variation selector 16
    if '\u200d' not in text and '\ufe0f' not in text:
        # Simplest case with no unicode stuff that changes the size
        return sum(get_character_cell_size(character) for character in text)

    total_width = 0
    last_measured_character: str | None = None

    special = {'\u200d', '\ufe0f'}

    index = 0
    character_count = len(text)

    while index < character_count:
        character = text[index]
        if character in special:
            if character == '\u200d':
                index += 1
            elif last_measured_character:
                total_width += last_measured_character in CELL_TABLE.narrow_to_wide
                last_measured_character = None
        elif character_width := get_character_cell_size(character):
            last_measured_character = character
            total_width += character_width
        index += 1

    return total_width


def split_graphemes(text: str) -> tuple[list[CellSpan], int]:
    """
    Divide text into spans that define a single grapheme, and additionally return the cell length of the whole string.

    The returned spans will cover every index in the string, with no gaps. It is possible for some graphemes to have a
    cell length of zero. This can occur for nonsense strings like two zero width joiners, or for control codes that
    don't contribute to the grapheme size.

    Args:
        text: String to split.

    Returns:
        A tuple of a list of *spans* and the cell length of the entire string. A span is a list of tuples of three
            values consisting of (<START>, <END>, <CELL LENGTH>), where START and END are string indices, and CELL
            LENGTH is the cell length of the single grapheme.
    """

    codepoint_count = len(text)
    index = 0
    last_measured_character: str | None = None

    total_width = 0
    spans: list[tuple[int, int, int]] = []
    special = {'\u200d', '\ufe0f'}

    while index < codepoint_count:
        if (character := text[index]) in special:
            if not spans:
                # ZWJ or variation selector at the beginning of the string doesn't really make sense. But handle it, we
                # must.
                spans.append((index, index := index + 1, 0))
                continue

            if character == '\u200d':
                # zero width joiner
                # The condition handles the case where a ZWJ is at the end of the string, and has nothing to join
                index += 2 if index < (codepoint_count - 1) else 1
                start, _end, cell_length = spans[-1]
                spans[-1] = (start, index, cell_length)

            else:
                # variation selector 16
                index += 1

                if last_measured_character:
                    start, _end, cell_length = spans[-1]
                    if last_measured_character in CELL_TABLE.narrow_to_wide:
                        last_measured_character = None
                        cell_length += 1
                        total_width += 1
                    spans[-1] = (start, index, cell_length)

                else:
                    # No previous character to change the size of. Shouldn't occur in practice. But handle it, we must.
                    start, _end, cell_length = spans[-1]
                    spans[-1] = (start, index, cell_length)

            continue

        if character_width := get_character_cell_size(character):
            last_measured_character = character
            spans.append((index, index := index + 1, character_width))
            total_width += character_width

        # Character has zero width
        elif spans:
            # zero width characters are associated with the previous character
            start, _end, cell_length = spans[-1]
            spans[-1] = (start, index := index + 1, cell_length)

        else:
            # A zero width character with no prior spans
            spans.append((index, index := index + 1, 0))

    return (spans, total_width)


def _split_text(
        text: str,
        cell_position: int,
) -> tuple[str, str]:
    """
    Split text by cell position.

    If the cell position falls within a double width character, it is converted to two spaces.

    Args:
        text: Text to split.
        cell_position Offset in cells.

    Returns:
        Tuple to two split strings.
    """

    if cell_position <= 0:
        return '', text

    spans, cell_length = split_graphemes(text)

    # Guess initial offset
    offset = int((cell_position / cell_length) * len(spans))
    left_size = sum(map(_span_get_cell_len, spans[:offset]))

    while True:
        if left_size == cell_position:
            if offset >= len(spans):
                return text, ''
            split_index = spans[offset][0]
            return text[:split_index], text[split_index:]
        if left_size < cell_position:
            start, end, cell_size = spans[offset]
            if left_size + cell_size > cell_position:
                return text[:start] + ' ', ' ' + text[end:]
            offset += 1
            left_size += cell_size
        else:  # left_size > cell_position
            start, end, cell_size = spans[offset - 1]
            if left_size - cell_size < cell_position:
                return text[:start] + ' ', ' ' + text[end:]
            offset -= 1
            left_size -= cell_size


def split_text(
        text: str,
        cell_position: int,
) -> tuple[str, str]:
    """
    Split text by cell position.

    If the cell position falls within a double width character, it is converted to two spaces.

    Args:
        text: Text to split.
        cell_position Offset in cells.

    Returns:
        Tuple to two split strings.
    """

    if _is_single_cell_widths(text):
        return text[:cell_position], text[cell_position:]
    return _split_text(text, cell_position)


def set_cell_size(text: str, total: int) -> str:
    """
    Adjust a string by cropping or padding with spaces such that it fits within the given number of cells.

    Args:
        text: String to adjust.
        total: Desired size in cells.

    Returns:
        A string with cell size equal to total.
    """

    if _is_single_cell_widths(text):
        size = len(text)
        if size < total:
            return text + ' ' * (total - size)
        return text[:total]

    if total <= 0:
        return ''

    cell_size = cell_len(text)
    if cell_size == total:
        return text
    if cell_size < total:
        return text + ' ' * (total - cell_size)

    text, _ = _split_text(text, total)
    return text


def chop_cells(text: str, width: int) -> list[str]:
    """
    Split text into lines such that each line fits within the available (cell) width.

    Args:
        text: The text to fold such that it fits in the given width.
        width: The width available (number of cells).

    Returns:
        A list of strings such that each string in the list has cell width
        less than or equal to the available width.
    """

    if _is_single_cell_widths(text):
        return [text[index : index + width] for index in range(0, len(text), width)]

    spans, _ = split_graphemes(text)
    line_size = 0  # Size of line in cells
    lines: list[str] = []
    line_offset = 0  # Offset (in codepoints) of start of line

    for start, end, cell_size in spans:
        if line_size + cell_size > width:
            lines.append(text[line_offset:start])
            line_offset = start
            line_size = 0

        line_size += cell_size

    if line_size:
        lines.append(text[line_offset:])

    return lines


def divide_line(text: str, width: int, fold: bool = True) -> list[int]:
    """
    Given a string of text, and a width (measured in cells), return a list of cell offsets which the string should be
    split at in order for it to fit within the given width.

    Args:
        text: The text to examine.
        width: The available cell width.
        fold: If True, words longer than `width` will be folded onto a new line.

    Returns:
        A list of indices to break the line at.
    """

    break_positions: list[int] = []  # offsets to insert the breaks at
    append = break_positions.append
    cell_offset = 0
    _cell_len = cell_len

    for start, _end, word in iter_words(text):
        word_length = _cell_len(word.rstrip())
        remaining_space = width - cell_offset
        word_fits_remaining_space = remaining_space >= word_length

        if word_fits_remaining_space:
            # Simplest case - the word fits within the remaining width for this line.
            cell_offset += _cell_len(word)
        # Not enough space remaining for this word on the current line.
        elif word_length > width:
            # The word doesn't fit on any line, so we can't simply place it on the next line...
            if fold:
                # Fold the word across multiple lines.
                folded_word = chop_cells(word, width=width)
                for last, line in loop_last(folded_word):
                    if start:
                        append(start)
                    if last:
                        cell_offset = _cell_len(line)
                    else:
                        start += len(line)
            else:
                # Folding isn't allowed, so crop the word.
                if start:
                    append(start)
                cell_offset = _cell_len(word)
        elif cell_offset and start:
            # The word doesn't fit within the remaining space on the current line, but it *can* fit on to the next
            # (empty) line.
            append(start)
            cell_offset = _cell_len(word)

    return break_positions
