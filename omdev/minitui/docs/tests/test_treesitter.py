import importlib.util

import pytest

from omcore.text import styled as st

from ...controls.textarea import TextArea
from ...events.keys import Key
from ...events.types import KeyEvent
from ...events.types import PasteEvent
from ..documents import Document
from ..positions import Pos
from ..treesitter import get_tree_sitter_highlighter


##


def make_highlighter():
    if importlib.util.find_spec('tree_sitter') is None or importlib.util.find_spec('tree_sitter_python') is None:
        pytest.skip('tree-sitter / python grammar not installed')
    h = get_tree_sitter_highlighter('py')
    assert h is not None
    return h


def names_of(lines):
    return {
        ref.name
        for line in lines
        for run in line.runs()
        for ref in run.styles
        if isinstance(ref, st.StyleName)
    }


def segment_styles_of(rows):
    return {seg.style for row in rows for seg in row}


def test_basic_highlight():
    h = make_highlighter()
    lines = h.highlight(['def foo(x):', '    return "s"  # c'])
    assert len(lines) == 2
    assert [line.text for line in lines] == ['def foo(x):', '    return "s"  # c']
    names = names_of(lines)
    assert 'code.keyword' in names
    assert 'code.def' in names
    assert 'code.string' in names
    assert 'code.comment' in names


def test_incremental_reparse_engages_and_matches_full():
    h = make_highlighter()
    doc = Document('def foo():\n    return 1')
    h.highlight(doc.lines())
    assert h.parse_counts == (1, 0)

    # Edit through the document, feeding the highlighter, exactly as TextArea wires it.
    doc.add_listener(lambda d, applied: h.note_edit(applied.edit))
    doc.insert(Pos(1, 11), '23  # hi')

    lines = h.highlight(doc.lines())
    full, incremental = h.parse_counts
    assert (full, incremental) == (1, 1)  # the second parse was incremental

    # And the result matches a from-scratch highlighter exactly.
    h2 = make_highlighter()
    assert list(lines) == list(h2.highlight(doc.lines()))


def test_missed_edit_falls_back_to_full_parse():
    h = make_highlighter()
    doc = Document('x = 1')
    h.highlight(doc.lines())
    doc.set_text('y = 2')  # NOT fed via note_edit

    lines = h.highlight(doc.lines())
    assert h.parse_counts == (2, 0)  # mismatch detected -> full parse, still correct
    assert lines[0].text == 'y = 2'


def test_multiline_and_unicode_edit():
    h = make_highlighter()
    doc = Document('s = "héllo"\nn = 1')
    doc.add_listener(lambda d, applied: h.note_edit(applied.edit))
    h.highlight(doc.lines())

    doc.replace(Pos(0, 4), Pos(1, 5), '"wörld"\ndef f():\n    pass')
    lines = h.highlight(doc.lines())
    assert h.parse_counts[1] == 1

    h2 = make_highlighter()
    assert list(lines) == list(h2.highlight(doc.lines()))


def test_textarea_integration_incremental():
    h = make_highlighter()
    ta_ = TextArea(highlighter=h)
    ta_.handle_event(PasteEvent('def foo():\n    return 1'))
    ta_.render(40)
    baseline_full = h.parse_counts[0]

    # Typing costs incremental parses, never full ones.
    for c in ('x', 'y'):
        ta_.handle_event(KeyEvent(Key(c), text=c))
        ta_.render(40)

    full, incremental = h.parse_counts
    assert full == baseline_full
    assert incremental >= 2

    assert 'code.keyword' in segment_styles_of(ta_.render(40))
