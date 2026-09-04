from omcore.text.styled import RgbColor

from ...events.types import MouseEvent
from ...events.types import MouseEventKind
from ...screens.cells import line_from_segments
from ...text.segments import Segment
from ...text.segments import segments_text
from ...text.styles import EMPTY_THEME
from ...text.themes import DEFAULT_THEME
from ..cards import Card
from ..cards import CardState
from ..history import InputHistory
from ..markdown import MarkdownTail
from ..stacks import stack_layout
from ..static import Static
from ..suggestions import SuggestionItem
from ..suggestions import SuggestionsPopup


##


def test_history_walk():
    h = InputHistory(['a', 'b'])

    assert h.previous('draft') == 'b'
    assert h.previous('draft') == 'a'
    assert h.previous('draft') is None  # at oldest
    assert h.next('') == 'b'
    assert h.next('') == 'draft'  # back to the stashed draft
    assert h.next('') is None


def test_history_add_dedupes_and_resets():
    h = InputHistory()
    h.add('x')
    h.add('x')
    h.add('')
    assert list(h.entries) == ['x']
    assert h.previous('cur') == 'x'
    h.add('y')
    assert h.previous('z') == 'y'


def test_suggestions_cycle():
    p = SuggestionsPopup()
    hidden = p.visible
    assert not hidden
    assert p.render(20) == []
    assert p.cycle() is None

    p.set_items([SuggestionItem('/help', 'halp'), SuggestionItem('/quit')])
    shown = p.visible
    assert shown
    assert p.cycle() == SuggestionItem('/help', 'halp')
    assert p.cycle() == SuggestionItem('/quit')
    assert p.cycle() == SuggestionItem('/help', 'halp')  # wraps

    rows = p.render(20)
    assert len(rows) == 2
    assert segments_text(rows[0]).startswith('/help')

    # Re-setting the same items keeps the selection; different items reset it.
    p.set_items([SuggestionItem('/help', 'halp'), SuggestionItem('/quit')])
    assert p.selected is not None
    p.set_items([SuggestionItem('/show')])
    assert p.selected is None


def test_markdown_tail_control():
    t = MarkdownTail()
    assert t.is_empty
    t.feed('# H\n\npartial para')
    settled = t.pop_settled()
    assert len(settled) == 1  # the heading

    rows = t.render(30)
    assert [segments_text(r) for r in rows] == ['partial para']

    committed = t.render_settled(settled, 30)
    assert segments_text(committed[0]) == '# H'

    final = t.finalize()
    assert len(final) == 1
    assert t.is_empty


def test_card_lifecycle_and_render():
    decided: list = []
    card = Card(
        [('tool()', 'card.summary')],
        state=CardState.CONFIRMING,
        detail=[[Segment('args')]],
        on_confirm=decided.append,
    )

    rows = [segments_text(r) for r in card.render(40)]
    assert rows[0].startswith('[+] ? tool()')
    assert 'allow (f10)' in rows[1]

    # Click on the header toggles expansion.
    card.handle_event(MouseEvent(MouseEventKind.DOWN, 2, 0))
    rows = [segments_text(r) for r in card.render(40)]
    assert rows[0].startswith('[-]')
    assert any('args' in r for r in rows)

    card.respond(True)
    assert decided == [True]
    card.set_state(CardState.RUNNING)
    running_terminal = card.is_terminal
    assert not running_terminal
    card.set_state(CardState.COMPLETE)
    complete_terminal = card.is_terminal
    assert complete_terminal
    assert segments_text(card.render(40)[0]).startswith('[-] ✓')


def test_stack_layout_hit_regions():
    a = Static([('a1\na2', None)])
    b = Static([('b1', None)])

    layout = stack_layout([a, b], width=10, max_height=10, theme=EMPTY_THEME)
    assert layout.hit(0) == (a, 0)
    assert layout.hit(1) == (a, 1)
    assert layout.hit(2) == (b, 0)
    assert layout.hit(3) is None

    # Truncation: the local index still refers to the control's own rendering (its first row was clipped away).
    layout = stack_layout([a, b], width=10, max_height=2, theme=EMPTY_THEME)
    assert layout.hit(0) == (a, 1)
    assert layout.hit(1) == (b, 0)


def test_confirmation_card_resolves_to_soft_truecolor():
    # The default theme renders the allow/deny buttons with muted RgbColors - never ANSI named green/red.
    card = Card(
        [('tool()', 'card.summary')],
        state=CardState.CONFIRMING,
        detail=[[Segment('args')]],
        on_confirm=lambda v: None,
    )
    rows = card.render(40)
    confirm_row = next(r for r in rows if 'allow' in segments_text(r))
    line = line_from_segments(confirm_row, DEFAULT_THEME)
    button_styles = {cell.style for cell in line.cells if cell.style.bg is not None}
    assert button_styles, 'confirmation buttons must carry background styles'
    for style in button_styles:
        assert isinstance(style.bg, RgbColor), style


def test_markdown_tail_reusable_across_stream_cycles():
    # The chat app holds ONE tail for its whole life and finalizes it at every content-block boundary - a turn shaped
    # like text / tool / text / tool / text must render every text block, not just the first (the "multi-tool turn
    # renders an empty response" bug: the default backend latched closed on its first finalize).
    t = MarkdownTail()

    for i, chunk in enumerate(['first block\n', 'second block\n', 'third block\n']):
        t.feed(chunk)
        blocks = [*t.pop_settled(), *t.finalize()]
        rows = [segments_text(row) for row in t.render_settled(blocks, 40)]
        assert any(f'{("first", "second", "third")[i]} block' in r for r in rows), (i, rows)
        assert t.is_empty


def test_markdown_tail_separates_blocks_across_commits():
    # Blocks settle one commit at a time, so the blank row `render_markdown_blocks` puts between the blocks of a single
    # call has to come from the tail: every commit after a cycle's first leads with it, and so does the live tail while
    # committed blocks precede it.
    t = MarkdownTail()

    t.feed('# H\n\n')
    assert [segments_text(r) for r in t.render_settled(t.pop_settled(), 30)] == ['# H']
    assert t.render(30) == []

    t.feed('para one\n\npara two')
    assert [segments_text(r) for r in t.render_settled(t.pop_settled(), 30)] == ['', 'para one']
    assert [segments_text(r) for r in t.render(30)] == ['', 'para two']

    assert [segments_text(r) for r in t.render_settled(t.finalize(), 30)] == ['', 'para two']
    assert t.render(30) == []

    # The next cycle starts unseparated - the caller's own break stands between streams.
    t.feed('next\n')
    assert [segments_text(r) for r in t.render_settled([*t.pop_settled(), *t.finalize()], 30)] == ['next']
