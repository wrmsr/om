import io

from omcore import lang
from omdev.tui import minitui as mt

from ....core import ui
from ..rendering import TerminalTextDisplayer
from ..rendering import TerminalTextRenderer
from ..rendering import render_text_rows


def test_render_text_rows_resolves_semantic_styles():
    rendering = ui.StyledTextRenderer().render(ui.JsonText({'answer': 42}))
    rows = render_text_rows(rendering, 80)

    assert mt.segments_text(rows[0]) == '{"answer": 42}'
    assert next(segment.style for segment in rows[0] if segment.text == '"answer"') == mt.Style(
        fg=mt.TEXT_PRIMARY,
    )
    assert next(segment.style for segment in rows[0] if segment.text == '42') == mt.Style(
        fg=mt.TEXT_WARNING,
    )


def test_render_text_rows_composes_newline_before_block():
    rendering = ui.StyledTextRenderer().render('before\n', ui.MarkdownText('after'))

    rows = render_text_rows(rendering, 80)

    assert [mt.segments_text(row) for row in rows] == ['before', 'after']


def test_terminal_text_renderer_inline_plain_and_ansi():
    text = ui.Text.of('danger').style(color='red', bold=True)

    assert TerminalTextRenderer(color_depth=None).render(text) == 'danger'
    assert TerminalTextRenderer(color_depth=mt.ColorDepth.MONO).render(text) == '\x1b[0;1mdanger\x1b[0m'
    assert TerminalTextRenderer(color_depth=mt.ColorDepth.TRUE).render(text) == (
        '\x1b[0;1;38;2;209;126;146mdanger\x1b[0m'
    )


def test_terminal_text_renderer_markdown_and_diff_blocks():
    rendered = TerminalTextRenderer(width=60, color_depth=None).render(
        'before',
        ui.MarkdownText('# Heading'),
        ui.DiffText(
            old='a\nb\nc\n',
            new='a\nB\nc\n',
            path='f.py',
        ),
        'after',
    )

    assert rendered.startswith('before\n# Heading\n')
    assert 'f.py (1 additions, 1 removals)' in rendered
    assert 'b' in rendered
    assert 'B' in rendered
    assert rendered.endswith('after')
    assert '\x1b' not in rendered


def test_terminal_text_displayer_is_plain_for_a_non_tty_file():
    out = io.StringIO()
    displayer = TerminalTextDisplayer(file=out)

    lang.sync_await(displayer.display_text('hi ', ui.JsonText({'a': 1})))

    assert out.getvalue() == 'hi {"a": 1}'
