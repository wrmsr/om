from ..documents import StyledDocument
from ..plain import render_plain
from ..styles import StylePatch
from ..text import StyledText


def test_empty_document() -> None:
    document = StyledDocument()

    assert not document
    assert document.plain == ''
    assert document.text == StyledText()


def test_document_lines_and_trailing_newline() -> None:
    document = StyledDocument.of_lines(['one', 'two'], trailing_newline=True)

    assert len(document) == 2
    assert document.plain == 'one\ntwo\n'
    assert document.text == StyledText('one\ntwo\n')


def test_document_splits_styled_text() -> None:
    text = StyledText('one\ntwo\n').styled(StylePatch(bold=True), 2, 6)

    document = StyledDocument.of_text(text)

    assert [line.plain for line in document] == ['one', 'two']
    assert document.trailing_newline
    assert document.lines[0].resolved_runs()[-1].style.bold
    assert document.lines[1].resolved_runs()[0].style.bold
    assert document.text.plain == text.plain


def test_document_preserves_leading_and_internal_empty_lines() -> None:
    document = StyledDocument.of_text('\n\na')

    assert [line.plain for line in document] == ['', '', 'a']
    assert not document.trailing_newline


def test_document_rejects_embedded_newlines() -> None:
    try:
        StyledDocument.of_lines(['a\nb'])
    except ValueError:
        pass
    else:
        raise AssertionError


def test_document_renders_plain() -> None:
    document = StyledDocument.of_lines([
        StyledText('<one>').styled(StylePatch(bold=True)),
        'two',
    ], trailing_newline=True)

    assert render_plain(document) == '<one>\ntwo\n'
