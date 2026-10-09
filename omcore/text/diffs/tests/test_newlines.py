import pytest

from ..newlines import split_newlines
from ..parsing import parse_patch


##


@pytest.mark.parametrize('text', ['', '\n', 'a', 'a\n', 'a\nb', 'a\nb\n', 'a\r\nb\r\n', '\n\n', 'a\n\n'])
def test_splits_ordinary_text_as_splitlines_does(text):
    assert split_newlines(text) == text.splitlines()
    assert split_newlines(text, keepends=True) == text.splitlines(keepends=True)


def test_splits_at_newlines_only():
    text = 'a\x0cb\nc\x0bd\u2028e\nf'

    assert split_newlines(text) == ['a\x0cb', 'c\x0bd\u2028e', 'f']
    assert ''.join(split_newlines(text, keepends=True)) == text

    # Only a carriage return ending a line goes with the newline - one within a line is part of it.
    assert split_newlines('a\rb\r\nc\r') == ['a\rb', 'c']


def test_a_patch_line_may_hold_a_form_feed():
    patch = parse_patch("""\
--- a/f.c
+++ b/f.c
@@ -1,2 +1,2 @@
 page\x0cbreak
-old
+new
""")

    [hunk] = patch.files[0].hunks
    assert [line.text for line in hunk.lines] == ['page\x0cbreak', 'old', 'new']
