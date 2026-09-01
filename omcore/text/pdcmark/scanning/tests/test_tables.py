from ...events import Alignment
from ..tables import count_table_cells
from ..tables import line_could_be_table_row
from ..tables import parse_alignment_row
from ..tables import parse_table_row


def test_align_basic():
    assert parse_alignment_row('| --- | --- |') == (Alignment.NONE, Alignment.NONE)


def test_align_left():
    assert parse_alignment_row('| :--- | :--- |') == (Alignment.LEFT, Alignment.LEFT)


def test_align_right():
    assert parse_alignment_row('| ---: | ---: |') == (Alignment.RIGHT, Alignment.RIGHT)


def test_align_center():
    assert parse_alignment_row('| :---: | :---: |') == (Alignment.CENTER, Alignment.CENTER)


def test_align_mixed():
    assert parse_alignment_row('| :- | -: | :-: | - |') == (
        Alignment.LEFT, Alignment.RIGHT, Alignment.CENTER, Alignment.NONE)


def test_align_no_pipes():
    assert parse_alignment_row('--- | ---') == (Alignment.NONE, Alignment.NONE)


def test_align_single_column():
    assert parse_alignment_row('| --- |') == (Alignment.NONE,)


def test_align_invalid_no_dashes():
    assert parse_alignment_row('| : | : |') is None


def test_align_invalid_text():
    assert parse_alignment_row('| abc | def |') is None


def test_align_indent_4_no():
    assert parse_alignment_row('    | --- |') is None


def test_row_basic():
    assert parse_table_row('| a | b |', 2) == ['a', 'b']


def test_row_no_outer_pipes():
    assert parse_table_row('a | b', 2) == ['a', 'b']


def test_row_escaped_pipe():
    assert parse_table_row(r'| a\|b | c |', 2) == ['a|b', 'c']


def test_row_pads_missing():
    assert parse_table_row('| a |', 3) == ['a', '', '']


def test_row_truncates_extra():
    assert parse_table_row('| a | b | c |', 2) == ['a', 'b']


def test_row_strips_cell_ws():
    assert parse_table_row('|  a  |  b  |', 2) == ['a', 'b']


def test_line_could_be_table_row():
    assert line_could_be_table_row('| a |')
    assert line_could_be_table_row('a | b')
    assert not line_could_be_table_row('plain text')
    assert not line_could_be_table_row(r'escaped \|')


# Indent: a delimiter row indented 4+ columns is paragraph continuation text (cf. cmark-gfm's `!indented` gate).


def test_align_indent_4_no_leading_pipe():
    assert parse_alignment_row('    --|--') is None


def test_align_tab_indent_no():
    assert parse_alignment_row('\t--|--') is None


def test_align_indent_3_ok():
    assert parse_alignment_row('   --|--') == (Alignment.NONE, Alignment.NONE)


# Escaping: only a pipe directly preceded by a backslash is escaped, consistently across the scanners.


def test_count_cells_escaped_backslash_pipe():
    assert count_table_cells(r'| a | `\|` |') == 2
    assert count_table_cells(r'| a | `\\|` |') == 2
    assert count_table_cells(r'| a | `\\\|` |') == 2
    assert count_table_cells(r'| a | \b | c |') == 3


def test_count_cells_lone_pipe_is_no_row():
    assert count_table_cells('|') == 0
    assert count_table_cells('|\t') == 0
    assert count_table_cells('||') == 0
    assert count_table_cells('| |') == 1


def test_row_escaped_backslash_pipe():
    assert parse_table_row(r'| a | `\\|` |', 2) == ['a', '`\\|`']
    assert parse_table_row(r'| a | `\\\|` |', 2) == ['a', '`\\\\|`']


def test_line_could_be_table_row_escaped_backslash_pipe():
    assert not line_could_be_table_row(r'a \\| b')
    assert line_could_be_table_row(r'a \\| b | c')
