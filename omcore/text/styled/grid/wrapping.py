"""Word wrapping of styled text to a cell width."""
from ...widths import char_width
from ..documents import StyledDocument
from ..text import StyledText
from ..text import StyledTextLike


##


def _line_ranges(plain: str, width: int) -> list[tuple[int, int]]:
    widths = [char_width(c) for c in plain]

    # Alternating runs of spaces and non-spaces, as (start, end) offsets.
    tokens: list[tuple[int, int]] = []
    i = 0
    n = len(plain)
    while i < n:
        is_space = plain[i] == ' '
        j = i + 1
        while j < n and (plain[j] == ' ') == is_space:
            j += 1
        tokens.append((i, j))
        i = j

    rows: list[tuple[int, int]] = []
    row_start = 0
    row_end = 0
    row_width = 0

    def end_row(next_start: int) -> None:
        nonlocal row_start, row_end, row_width
        end = row_end
        while end > row_start and plain[end - 1] == ' ':
            end -= 1
        rows.append((row_start, end))
        row_start = row_end = next_start
        row_width = 0

    for start, end in tokens:
        token_width = sum(widths[start:end])

        if plain[start] == ' ':
            if row_width + token_width > width:
                # Whitespace at the wrap point is dropped.
                end_row(end)
            else:
                row_end = end
                row_width += token_width
            continue

        if row_width + token_width <= width:
            row_end = end
            row_width += token_width

        elif token_width <= width:
            end_row(start)
            row_end = end
            row_width = token_width

        else:
            # A word wider than the whole line: hard-break it.
            for k in range(start, end):
                if row_width + widths[k] > width and row_width > 0:
                    end_row(k)
                row_end = k + 1
                row_width += widths[k]

    if row_end > row_start or not rows:
        end_row(n)
    return rows


def wrap(text: StyledTextLike, width: int) -> list[StyledText]:
    """
    Wrap one logical line to `width` cells, returning at least one line.

    Breaks at spaces, hard-breaks words wider than the whole line, drops whitespace at wrap points, keeps interior
    whitespace, and preserves every span. A non-positive width returns the text unwrapped. Newlines are not line breaks
    here: split with `StyledDocument.of_text` first, or use `wrap_document`.
    """

    value = StyledText.of(text)
    if '\n' in value.text or '\r' in value.text:
        raise ValueError(value.text)

    if width <= 0:
        return [value]
    if not value.text:
        return [StyledText()]
    return [value.slice(start, end) for start, end in _line_ranges(value.text, width)]


def wrap_document(document: StyledDocument, width: int) -> StyledDocument:
    """Wrap every line of a document, preserving its trailing newline."""

    lines: list[StyledText] = []
    for line in document.lines:
        lines.extend(wrap(line, width))
    return StyledDocument(tuple(lines), trailing_newline=document.trailing_newline)
