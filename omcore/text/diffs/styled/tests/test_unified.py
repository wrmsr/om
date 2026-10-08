from .... import styled as st
from ....widths import str_width
from ...parsing import parse_patch
from ...themes import ADDED_BACKGROUND
from ...themes import ADDED_INTRALINE_BACKGROUND
from ...themes import REMOVED_BACKGROUND
from ...themes import REMOVED_INTRALINE_BACKGROUND
from ..rendering import render_diff_styled_doc
from .utils import MODIFIED_DIFF
from .utils import style_at


EXPECTED_MODIFIED_PLAIN = '\n'.join([
    '1 file changed'.center(60),
    '+2 ━━━━━━━━╺━━━ -1'.center(60),
    '',
    '▁' * 13 + ' foo.py (2 additions, 1 removals) ' + '▁' * 13,
    '╲' * 16 + ' @@ -1,3 +1,4 @@ def greet ' + '╲' * 17,
    ' 1 1   def greet(name):'.ljust(60),
    ' 2   - │   message = f"Hello, {name}!"'.ljust(60),
    '   2 + │   message = f"Hello, {name}."'.ljust(60),
    '   3 + │   print(message)'.ljust(60),
    ' 3 4   │   return message'.ljust(60),
    '▔' * 60,
    '/// diff   '.rjust(60),
    '',
])


INTERLEAVED_DIFF = """\
--- a/x.py
+++ b/x.py
@@ -8,5 +8,5 @@
 keep = 1
-alpha = 1
+alpha = 7
-beta = 2
+beta = 9
 also = 3
 x = 4
"""


def _body(document: st.StyledDocument) -> list[st.StyledText]:
    """The rows between the hunk header and the file's closing rule."""

    start = next(i for i, line in enumerate(document.lines) if line.text.startswith('╲'))
    end = next(i for i, line in enumerate(document.lines) if line.text.startswith('▔'))
    return list(document.lines[start + 1:end])


def test_plain_output() -> None:
    document = render_diff_styled_doc(parse_patch(MODIFIED_DIFF), width=60, layout='unified')

    assert st.render_plain(document) == EXPECTED_MODIFIED_PLAIN
    assert document.trailing_newline
    assert all(str_width(line.text) == 60 for line in document.lines if line)


def test_interleaved_change_reads_as_removals_over_additions() -> None:
    document = render_diff_styled_doc(parse_patch(INTERLEAVED_DIFF), width=40, layout='unified')

    assert [line.text.rstrip() for line in _body(document)] == [
        '  8  8   keep = 1',
        '  9    - alpha = 1',
        ' 10    - beta = 2',
        '     9 + alpha = 7',
        '    10 + beta = 9',
        ' 11 11   also = 3',
        ' 12 12   x = 4',
    ]


def test_changed_lines_take_their_backgrounds_and_paired_lines_intraline_ranges() -> None:
    document = render_diff_styled_doc(parse_patch(INTERLEAVED_DIFF), width=40, layout='unified')
    body = _body(document)

    # Each removal pairs with the addition in the same place on the other side, however far apart they are drawn.
    removed = next(line for line in body if 'alpha = 1' in line.text)
    assert style_at(removed, removed.text.index('1')).bg == REMOVED_INTRALINE_BACKGROUND
    assert style_at(removed, removed.text.index('alpha')).bg == REMOVED_BACKGROUND

    added = next(line for line in body if 'alpha = 7' in line.text)
    assert style_at(added, added.text.index('7')).bg == ADDED_INTRALINE_BACKGROUND
    assert style_at(added, added.text.index('alpha')).bg == ADDED_BACKGROUND


def test_uneven_change_gets_no_intraline_ranges() -> None:
    # One line replaced by two: as in the split layout, nothing is paired.
    document = render_diff_styled_doc(parse_patch(MODIFIED_DIFF), width=60, layout='unified')

    for line in _body(document):
        assert all(
            style_at(line, i).bg not in (REMOVED_INTRALINE_BACKGROUND, ADDED_INTRALINE_BACKGROUND)
            for i in range(len(line.text))
        )


def test_lines_get_the_full_width() -> None:
    long = 'value = ' + ' + '.join(f'term_{i}' for i in range(8))
    patch = parse_patch(f"""\
--- a/long.py
+++ b/long.py
@@ -1 +1 @@
-{long}
+{long} + 1
""")

    unified = st.render_plain(render_diff_styled_doc(patch, width=120, layout='unified'))
    split = st.render_plain(render_diff_styled_doc(patch, width=120, layout='split'))

    assert f'{long} + 1' in unified
    assert long not in split
