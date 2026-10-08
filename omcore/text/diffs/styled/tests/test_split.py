from .... import styled as st
from ....widths import str_width
from ...parsing import parse_patch
from ...themes import ADDED_INTRALINE_BACKGROUND
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
    '  1 def greet(name):'.ljust(30) + '  1 def greet(name):'.ljust(30),
    '  2 │   message = f"Hello, {na' + '  2 │   message = f"Hello, {na',
    '╲' * 30 + '  3 │   print(message)'.ljust(30),
    '  3 │   return message'.ljust(30) + '  4 │   return message'.ljust(30),
    '▔' * 60,
    '/// diff   '.rjust(60),
    '',
])


def test_plain_output_matches_rich_characterization() -> None:
    document = render_diff_styled_doc(parse_patch(MODIFIED_DIFF), width=60, layout='split')

    assert st.render_plain(document) == EXPECTED_MODIFIED_PLAIN
    assert document.trailing_newline
    assert all(str_width(line.text) == 60 for line in document.lines if line)


def test_equal_change_streaks_receive_intraline_highlighting() -> None:
    document = render_diff_styled_doc(parse_patch("""\
--- a/message.txt
+++ b/message.txt
@@ -1 +1 @@
-hello world
+hello there
"""), width=80, layout='split')
    row = next(line for line in document.lines if 'hello world' in line.text)

    removed = row.text.index('world')
    added = row.text.index('there')
    assert style_at(row, removed).bg == REMOVED_INTRALINE_BACKGROUND
    assert style_at(row, added).bg == ADDED_INTRALINE_BACKGROUND


def test_uneven_change_streak_uses_hatched_alignment_padding() -> None:
    document = render_diff_styled_doc(parse_patch(MODIFIED_DIFF), width=60, layout='split')

    assert any(line.text.startswith('╲' * 30) and 'print(message)' in line.text for line in document.lines)
