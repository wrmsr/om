from omcore.text import diffs
from omcore.text import styled as st

from ... import minitui as mt
from ..rendering import render_diff_document
from ..terminal import render_diff_ansi
from ..themes import ADDED_INTRALINE_BACKGROUND
from ..themes import DIFF_STYLE_THEME
from ..themes import REMOVED_INTRALINE_BACKGROUND


MODIFIED_DIFF = """\
diff --git a/foo.py b/foo.py
index 1111111..2222222 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@ def greet
 def greet(name):
-    message = f"Hello, {name}!"
+    message = f"Hello, {name}."
+    print(message)
     return message
"""


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


def _style_at(text: st.StyledText, position: int) -> st.ResolvedStyle:
    offset = 0
    for run in text.resolved_runs(DIFF_STYLE_THEME):
        if offset <= position < offset + len(run.text):
            return run.style
        offset += len(run.text)
    raise IndexError(position)


def test_plain_output_matches_rich_characterization() -> None:
    document = render_diff_document(diffs.parse_patch(MODIFIED_DIFF), width=60)

    assert st.render_plain(document) == EXPECTED_MODIFIED_PLAIN
    assert document.trailing_newline
    assert all(mt.str_width(line.text) == 60 for line in document.lines if line)


def test_equal_change_streaks_receive_intraline_highlighting() -> None:
    document = render_diff_document(diffs.parse_patch("""\
--- a/message.txt
+++ b/message.txt
@@ -1 +1 @@
-hello world
+hello there
"""), width=80)
    row = next(line for line in document.lines if 'hello world' in line.text)

    removed = row.text.index('world')
    added = row.text.index('there')
    assert _style_at(row, removed).bg == REMOVED_INTRALINE_BACKGROUND
    assert _style_at(row, added).bg == ADDED_INTRALINE_BACKGROUND


def test_uneven_change_streak_uses_hatched_alignment_padding() -> None:
    document = render_diff_document(diffs.parse_patch(MODIFIED_DIFF), width=60)

    assert any(line.text.startswith('╲' * 30) and 'print(message)' in line.text for line in document.lines)


def test_markup_shaped_source_text_is_literal() -> None:
    document = render_diff_document(diffs.parse_patch("""\
--- a/types.py
+++ b/types.py
@@ -1 +1 @@ list[str]
-value: list[int]
+value: list[str]
"""), width=80)

    assert 'list[str]' in document.plain
    assert 'value: list[int]' in document.plain
    assert '<span style=' in st.render_html(document, theme=DIFF_STYLE_THEME)


def test_special_file_bodies() -> None:
    deleted = render_diff_document(diffs.parse_patch("""\
diff --git a/old.txt b/old.txt
deleted file mode 100644
--- a/old.txt
+++ /dev/null
"""), width=60)
    binary = render_diff_document(diffs.parse_patch("""\
diff --git a/image.png b/image.png
Binary files a/image.png and b/image.png differ
"""), width=60)
    renamed = render_diff_document(diffs.parse_patch("""\
diff --git a/old.txt b/new.txt
similarity index 100%
rename from old.txt
rename to new.txt
--- a/old.txt
+++ b/new.txt
"""), width=60)

    assert 'File was removed' in deleted.plain
    assert 'File is binary' in binary.plain
    assert 'old.txt → new.txt' in renamed.plain
    assert 'File was only renamed' in renamed.plain


def test_headless_ansi_has_same_visible_text() -> None:
    patch = diffs.parse_patch(MODIFIED_DIFF)
    document = render_diff_document(patch, width=60)

    ansi = render_diff_ansi(patch, width=60)

    assert mt.ANSI_ESCAPE_PAT.sub('', ansi) == document.plain
    assert '\x1b[' in ansi
