from ..controls.histories import InputHistory
from ..controls.markdowns import MarkdownTail
from ..controls.suggestions import SuggestionItem
from ..controls.suggestions import SuggestionsPopup
from ..text.segments import segments_text


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
    from ..controls.cards import Card  # noqa: PLC0415
    from ..controls.cards import CardState  # noqa: PLC0415
    from ..events.types import MouseEvent  # noqa: PLC0415
    from ..events.types import MouseEventKind  # noqa: PLC0415
    from ..text.segments import Segment  # noqa: PLC0415

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
    from ..controls.stacks import stack_layout  # noqa: PLC0415
    from ..controls.statics import Static  # noqa: PLC0415
    from ..text.styles import EMPTY_THEME  # noqa: PLC0415

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
