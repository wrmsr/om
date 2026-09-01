"""GFM table edge semantics at the block-machine level (see also `scanning/tests/test_tables.py` for the scanners)."""
from ...options import GFM
from ...parsing import parse
from ...rendering.html import render_html


def _html(src: str) -> str:
    return render_html(parse(src, GFM))


_HEAD = '<table>\n<thead>\n<tr>\n<th>a</th>\n<th>b</th>\n</tr>\n</thead>\n'


def test_lone_pipe_line_ends_table():
    out = _html('| a | b |\n|---|---|\n| 1 | 2 |\n|\n| x | y |\n')
    assert out == (
        _HEAD +
        '<tbody>\n<tr>\n<td>1</td>\n<td>2</td>\n</tr>\n</tbody>\n</table>\n'
        '<p>|\n| x | y |</p>\n'
    )


def test_lone_pipe_after_head_leaves_empty_body():
    out = _html('| a | b |\n|---|---|\n|\n')
    assert out == _HEAD + '<tbody></tbody>\n</table>\n<p>|</p>\n'


def test_escaped_backslash_pipe_in_code_span():
    # `\\|` is a literal backslash followed by an escaped pipe - not a cell separator.
    out = _html('| a | `\\\\|` |\n|--|--|\n| b | `\\\\\\|` |\n')
    assert '<th><code>\\|</code></th>' in out
    assert '<td><code>\\\\|</code></td>' in out


def test_escaped_pipe_in_link_destination_and_title():
    out = _html('| [t](first\\\\|second "x\\\\|y") |\n|--|\n')
    assert '<a href="first%7Csecond" title="x|y">t</a>' in out


def test_indented_delimiter_row_does_not_promote_table():
    assert '<table>' not in _html('para\n    a | b\n    --|--\n    c | d\n')


def test_indented_body_rows_still_continue_table():
    out = _html('| a | b |\n|---|---|\n      | 1 | 2 |\n')
    assert '<td>1</td>' in out
