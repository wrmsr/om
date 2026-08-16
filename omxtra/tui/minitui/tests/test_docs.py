import pytest

from ..docs.documents import Document
from ..docs.edits import TextEdit
from ..docs.edits import remap_pos
from ..docs.positions import Kind
from ..docs.positions import Pos
from ..docs.positions import Span
from ..docs.searches import find_matches
from ..docs.searches import next_match


##


def test_document_replace_and_inverse():
    d = Document('hello\nworld')

    applied = d.replace(Pos(0, 5), Pos(1, 0), ' ')
    assert d.text() == 'hello world'
    assert applied.inverse == TextEdit(Pos(0, 5), Pos(0, 6), '\n')

    d.apply(applied.inverse)
    assert d.text() == 'hello\nworld'


def test_document_multiline_insert_and_delete():
    d = Document('ab')

    d.insert(Pos(0, 1), 'x\ny')
    assert d.lines() == ('ax', 'yb')

    applied = d.delete(Pos(0, 1), Pos(1, 1))
    assert d.text() == 'ab'
    assert applied.inverse.text == 'x\ny'

    d.apply(applied.inverse)
    assert d.lines() == ('ax', 'yb')


def test_document_never_empty_and_listeners():
    d = Document('abc')
    seen = []
    d.add_listener(lambda doc, applied: seen.append(applied.edit))

    d.set_text('')
    assert d.lines() == ('',)
    assert d.line_count() == 1
    assert len(seen) == 1
    assert d.version == 1


def test_document_validates_positions():
    d = Document('ab')
    with pytest.raises(Exception):  # noqa: B017, PT011
        d.insert(Pos(0, 3), 'x')
    with pytest.raises(Exception):  # noqa: B017, PT011
        d.insert(Pos(1, 0), 'x')


def test_remap_pos_same_line():
    edit = TextEdit(Pos(0, 2), Pos(0, 4), 'xyz')  # 2 chars -> 3 chars

    assert remap_pos(Pos(0, 1), edit) == Pos(0, 1)
    assert remap_pos(Pos(0, 3), edit) == Pos(0, 2)   # inside -> clamps to start
    assert remap_pos(Pos(0, 4), edit) == Pos(0, 5)   # at old end -> shifts by delta
    assert remap_pos(Pos(0, 9), edit) == Pos(0, 10)
    assert remap_pos(Pos(3, 1), edit) == Pos(3, 1)   # other rows untouched


def test_remap_pos_multiline():
    # Delete a newline: rows below shift up.
    edit = TextEdit(Pos(0, 5), Pos(1, 0), '')
    assert remap_pos(Pos(1, 3), edit) == Pos(0, 8)
    assert remap_pos(Pos(2, 3), edit) == Pos(1, 3)

    # Insert two lines.
    edit = TextEdit(Pos(0, 0), Pos(0, 0), 'a\nb\n')
    assert remap_pos(Pos(0, 2), edit) == Pos(2, 2)
    assert remap_pos(Pos(1, 0), edit) == Pos(3, 0)


def test_remap_pos_insert_bias():
    edit = TextEdit(Pos(0, 2), Pos(0, 2), 'xx')
    # Default: an insertion at the position pushes it forward (cursor typing).
    assert remap_pos(Pos(0, 2), edit) == Pos(0, 4)
    # before_bias: it stays put (span starts, anchors).
    assert remap_pos(Pos(0, 2), edit, before_bias=True) == Pos(0, 2)


def test_search_smartcase():
    d = Document('Foo foo\nFOO')

    assert len(find_matches(d, 'foo')) == 3  # all-lowercase: insensitive
    assert len(find_matches(d, 'Foo')) == 1  # uppercase present: exact
    assert find_matches(d, 'foo', no_smartcase=True) == [Span(Kind.EXCLUSIVE, Pos(0, 4), Pos(0, 7))]
    assert find_matches(d, '') == []


def test_next_match_wraps():
    d = Document('a a a')
    matches = find_matches(d, 'a')
    assert [s.start for s in matches] == [Pos(0, 0), Pos(0, 2), Pos(0, 4)]

    def start_of(pos, **kwargs):
        m = next_match(matches, pos, **kwargs)
        assert m is not None
        return m.start

    assert start_of(Pos(0, 0)) == Pos(0, 2)
    assert start_of(Pos(0, 4)) == Pos(0, 0)  # wraps
    assert start_of(Pos(0, 2), reverse=True) == Pos(0, 0)
    assert start_of(Pos(0, 0), reverse=True) == Pos(0, 4)  # wraps
    assert next_match([], Pos(0, 0)) is None
