import io

import pytest

from omcore import inject as inj
from omcore import lang
from omcore.term import styled as tst
from omdev import minitui as mt

from ....core import ui
from ..config import Config
from ..rendering import TerminalTextDisplayer
from ..rendering import TerminalTextRenderer
from ..rendering import TextRowsRenderer
from .headless import bind_headless_tui
from .headless import headless_tui


def test_text_rows_resolve_semantic_styles():
    rows = TextRowsRenderer().render_rows(80, ui.JsonText({'answer': 42}))

    assert mt.segments_text(rows[0]) == '{"answer": 42}'
    assert next(segment.style for segment in rows[0] if segment.text == '"answer"') == mt.Style(
        fg=mt.TEXT_PRIMARY,
    )
    assert next(segment.style for segment in rows[0] if segment.text == '42') == mt.Style(
        fg=mt.TEXT_WARNING,
    )


def test_text_rows_compose_newline_before_block():
    rows = TextRowsRenderer().render_rows(80, 'before\n', ui.MarkdownText('after'))

    assert [mt.segments_text(row) for row in rows] == ['before', 'after']


def test_terminal_text_renderer_inline_plain_and_ansi():
    text = ui.Text.of('danger').style(color='red', bold=True)

    assert TerminalTextRenderer(color_depth=None).render(text) == 'danger'
    assert TerminalTextRenderer(color_depth=tst.ColorDepth.MONO).render(text) == '\x1b[0;1mdanger\x1b[0m'
    assert TerminalTextRenderer(color_depth=tst.ColorDepth.TRUE).render(text) == (
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


##


_DIFF = ui.DiffText(old='a\nkeep\n', new='b\nkeep\n', path='f.py')


def _shares_a_row(rendered: str) -> bool:
    return any(' a ' in line and ' b ' in line for line in rendered.splitlines())


def test_diff_layout_option_reaches_terminal_rendering():
    def render(layout):
        options = ui.TextRenderingOptions(diff_layout=layout)
        return TerminalTextRenderer(options, width=60, color_depth=None).render(_DIFF)

    assert _shares_a_row(render('split'))
    assert not _shares_a_row(render('unified'))

    # Left to itself the diff renderer chooses by width, and 60 columns is too narrow to split.
    assert render(None) == render('unified')


def test_terminal_text_displayer_builds_its_renderer_with_the_options():
    out = io.StringIO()
    displayer = TerminalTextDisplayer(file=out, options=ui.TextRenderingOptions(diff_layout='split'))

    lang.sync_await(displayer.display_text(_DIFF))

    assert _shares_a_row(out.getvalue())


@pytest.mark.asyncs('asyncio')
async def test_bound_options_reach_the_frontends():
    async with headless_tui(inj.override(
            bind_headless_tui(Config(
                model='scripted',
                in_memory=True,
            )),
            inj.bind(ui.TextRenderingOptions(diff_layout='split')),
    )) as tui:
        rows_renderer = await tui.injector[TextRowsRenderer]

    rendered = '\n'.join(mt.segments_text(row) for row in rows_renderer.render_rows(60, _DIFF))
    assert _shares_a_row(rendered)
