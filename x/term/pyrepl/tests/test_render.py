from ..render import LineUpdate
from ..render import RenderCell
from ..render import RenderedScreen
from ..render import RenderLine
from ..render import ScreenOverlay
from ..render import diff_render_lines
from ..render import render_cells
from ..render import requires_cursor_resync
from ..utils import StyleRef


##


class TestRenderLine:
    def test_from_rendered_text_parses_style_state(self):
        line = RenderLine.from_rendered_text('\x1b[31ma\x1b[0mb')

        assert line.width == 2
        assert [cell.text for cell in line.cells] == ['a', 'b']
        assert [cell.style.sgr for cell in line.cells] == ['\x1b[31m', '']
        assert [cell.controls for cell in line.cells] == [(), ()]

    def test_from_rendered_text_round_trips_trailing_reset(self):
        line = RenderLine.from_rendered_text('\x1b[31ma\x1b[0m')

        assert [cell.text for cell in line.cells] == ['a']
        assert [cell.style.sgr for cell in line.cells] == ['\x1b[31m']
        assert line.text == '\x1b[31ma\x1b[0m'

    def test_from_parts_accepts_style_refs(self):
        line = RenderLine.from_parts(
            ['d', 'e', 'f', ' '],
            [1, 1, 1, 1],
            [StyleRef.from_sgr('\x1b[1;34m')] * 3 + [None],
        )

        assert [cell.text for cell in line.cells] == ['d', 'e', 'f', ' ']
        assert [cell.style.sgr for cell in line.cells] == ['\x1b[1;34m', '\x1b[1;34m', '\x1b[1;34m', '']
        assert line.text == '\x1b[1;34mdef\x1b[0m '

    def test_from_parts_without_styles(self):
        line = RenderLine.from_parts(['a', 'b'], [1, 1])

        assert line.text == 'ab'
        assert line.width == 2

    def test_from_rendered_text_empty_string(self):
        line = RenderLine.from_rendered_text('')

        assert line.cells == ()
        assert line.text == ''
        assert line.width == 0

    def test_from_rendered_text_with_non_sgr_controls(self):
        # \x1b[H is a cursor-home control (not SGR since it doesn't end with 'm')
        line = RenderLine.from_rendered_text('\x1b[Hx')

        assert len(line.cells) == 2
        assert line.cells[0].controls == ('\x1b[H',)
        assert line.cells[0].text == ''
        assert line.cells[1].text == 'x'

    def test_from_rendered_text_trailing_non_sgr_control(self):
        line = RenderLine.from_rendered_text('a\x1b[K')

        assert len(line.cells) == 2
        assert line.cells[0].text == 'a'
        assert line.cells[1].controls == ('\x1b[K',)
        assert line.cells[1].text == ''

    def test_from_rendered_text_non_sgr_before_text(self):
        # Non-SGR control immediately before text should produce a control cell then text cells.
        line = RenderLine.from_rendered_text('\x1b[Kab')

        texts = [c.text for c in line.cells]
        assert texts == ['', 'a', 'b']
        assert line.cells[0].controls == ('\x1b[K',)


class TestLineDiff:
    def test_diff_render_lines_ignores_unchanged_ansi_prefix(self):
        old = RenderLine.from_rendered_text('\x1b[31ma\x1b[0mb')
        new = RenderLine.from_rendered_text('\x1b[31ma\x1b[0mc')

        diff = diff_render_lines(old, new)

        assert diff is not None
        assert diff.start_x == 1
        assert diff.old_text == 'b'
        assert diff.new_text == 'c'

    def test_diff_render_lines_detects_single_cell_insertion(self):
        old = RenderLine.from_rendered_text('ab')
        new = RenderLine.from_rendered_text('acb')

        diff = diff_render_lines(old, new)

        assert diff is not None
        assert diff.start_x == 1
        assert diff.old_text == ''
        assert diff.new_text == 'c'

    def test_colored_append_only_emits_new_character_and_reset(self):
        old = RenderLine.from_rendered_text('\x1b[1mabc\x1b[0m')
        new = RenderLine.from_rendered_text('\x1b[1mabcd\x1b[0m')

        diff = diff_render_lines(old, new)

        assert diff is not None
        assert diff.start_x == 3
        assert render_cells(diff.new_cells) == '\x1b[1md\x1b[0m'

    def test_keyword_space_inserts_only_space_after_reset(self):
        old = RenderLine.from_parts(
            ['d', 'e', 'f'],
            [1, 1, 1],
            ['keyword', 'keyword', 'keyword'],
        )
        new = RenderLine.from_parts(
            ['d', 'e', 'f', ' '],
            [1, 1, 1, 1],
            ['keyword', 'keyword', 'keyword', None],
        )

        diff = diff_render_lines(old, new)

        assert diff is not None
        assert diff.start_x == 3
        assert render_cells(diff.new_cells) == ' '

    def test_diff_render_lines_returns_none_for_identical(self):
        line = RenderLine.from_rendered_text('abc')
        assert diff_render_lines(line, line) is None

    def test_diff_render_lines_breaks_on_controls_in_prefix(self):
        old = RenderLine.from_cells([
            RenderCell('a', 1),
            RenderCell('', 0, controls=('\x1b[K',)),
            RenderCell('b', 1),
        ])
        new = RenderLine.from_cells([
            RenderCell('a', 1),
            RenderCell('', 0, controls=('\x1b[K',)),
            RenderCell('c', 1),
        ])

        diff = diff_render_lines(old, new)

        assert diff is not None
        # Prefix scan stops at control cell, so diff starts at cell 1
        assert diff.start_cell == 1
        assert diff.start_x == 1

    def test_diff_render_lines_extends_past_combining_chars(self):
        # \u0301 is a combining acute accent (zero-width)
        old = RenderLine.from_parts(['a', 'b', '\u0301'], [1, 1, 0])
        new = RenderLine.from_parts(['a', 'c', '\u0301'], [1, 1, 0])

        diff = diff_render_lines(old, new)

        assert diff is not None
        # The combining char is included since it's zero-width
        assert len(diff.new_cells) == 2

    def test_diff_old_and_new_changed_width(self):
        old = RenderLine.from_rendered_text('ab')
        new = RenderLine.from_rendered_text('acd')

        diff = diff_render_lines(old, new)

        assert diff is not None
        assert diff.old_changed_width == 1
        assert diff.new_changed_width == 2

    def test_rendered_screen_round_trips_screen_lines(self):
        screen = RenderedScreen.from_screen_lines(
            ['a', '\x1b[31mb\x1b[0m'],
            (0, 1),
        )

        assert screen.screen_lines == ('a', '\x1b[31mb\x1b[0m')


class TestRenderedScreen:
    def test_empty(self):
        screen = RenderedScreen.empty()

        assert screen.lines == ()
        assert screen.cursor == (0, 0)
        assert screen.overlays == ()
        assert screen.composed_lines == ()

    def test_with_overlay(self):
        screen = RenderedScreen.from_screen_lines(['aaa', 'bbb'], (0, 0))
        overlay_line = RenderLine.from_rendered_text('xxx')
        result = screen.with_overlay(1, [overlay_line])

        assert len(result.overlays) == 1
        assert result.composed_lines[0].text == 'aaa'
        assert result.composed_lines[1].text == 'xxx'

    def test_compose_replace_overlay(self):
        base = RenderedScreen.from_screen_lines(['aa', 'bb', 'cc'], (0, 0))
        overlay_line = RenderLine.from_rendered_text('XX')
        screen = RenderedScreen(
            base.lines,
            (0, 0),
            (ScreenOverlay(y=1, lines=(overlay_line,)),),
        )

        assert screen.composed_lines[0].text == 'aa'
        assert screen.composed_lines[1].text == 'XX'
        assert screen.composed_lines[2].text == 'cc'

    def test_compose_insert_overlay(self):
        base = RenderedScreen.from_screen_lines(['aa', 'bb'], (0, 0))
        overlay_line = RenderLine.from_rendered_text('INS')
        screen = RenderedScreen(
            base.lines,
            (0, 0),
            (ScreenOverlay(y=1, lines=(overlay_line,), insert=True),),
        )

        assert len(screen.composed_lines) == 3
        assert screen.composed_lines[0].text == 'aa'
        assert screen.composed_lines[1].text == 'INS'
        assert screen.composed_lines[2].text == 'bb'

    def test_compose_replace_extends_beyond_lines(self):
        base = RenderedScreen.from_screen_lines(['aa'], (0, 0))
        overlay_line = RenderLine.from_rendered_text('XX')
        screen = RenderedScreen(
            base.lines,
            (0, 0),
            (ScreenOverlay(y=1, lines=(overlay_line,)),),
        )

        assert len(screen.composed_lines) == 2
        assert screen.composed_lines[1].text == 'XX'


class TestRenderCell:
    def test_terminal_text(self):
        cell = RenderCell('x', 1, style=StyleRef.from_sgr('\x1b[32m'))
        assert cell.terminal_text == '\x1b[32mx\x1b[0m'

    def test_terminal_text_plain(self):
        cell = RenderCell('y', 1)
        assert cell.terminal_text == 'y'


class TestRenderCells:
    def test_render_cells_with_controls(self):
        cells = [
            RenderCell('', 0, controls=('\x1b[K',)),
            RenderCell('a', 1),
        ]
        result = render_cells(cells)
        assert result == '\x1b[Ka'

    def test_render_cells_skips_empty_text(self):
        cells = [
            RenderCell('', 0),
            RenderCell('a', 1),
        ]
        result = render_cells(cells)
        assert result == 'a'

    def test_render_cells_with_visual_style(self):
        cells = [RenderCell('a', 1)]
        result = render_cells(cells, visual_style='\x1b[7m')
        assert result == '\x1b[7ma\x1b[0m'


class TestLineUpdate:
    def test_post_init_renders_text(self):
        cells = (RenderCell('a', 1), RenderCell('b', 1))
        update = LineUpdate(
            kind='insert_char',
            y=0,
            start_cell=0,
            start_x=0,
            cells=cells,
        )
        assert update.text == 'ab'


class TestRequiresCursorResync:
    def test_no_controls(self):
        cells = [RenderCell('a', 1)]
        assert not requires_cursor_resync(cells)

    def test_sgr_only_does_not_require_resync(self):
        cells = [RenderCell('', 0, controls=('\x1b[31m',))]
        assert not requires_cursor_resync(cells)

    def test_non_sgr_requires_resync(self):
        cells = [RenderCell('', 0, controls=('\x1b[H',))]
        assert requires_cursor_resync(cells)
