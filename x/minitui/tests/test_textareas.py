from ..controls.textareas import TextArea
from ..events.keys import Key
from ..events.keys import key_text
from ..events.types import KeyEvent
from ..events.types import PasteEvent
from ..text.segments import segments_text
from ..vim.modes import Mode
from ..vim.status import SEARCH_MATCH_TAG


##


def press(ta_, *keys):
    for k in keys:
        key = Key(k) if isinstance(k, str) else k
        ta_.handle_event(KeyEvent(key, text=key_text(key)))


def type_text(ta_, text):
    for c in text:
        press(ta_, c if c != ' ' else 'space')


def rows(ta_, width=20):
    return [segments_text(row) for row in ta_.render(width)]


def test_typing_and_prompt():
    ta_ = TextArea(prompt='> ')
    assert ta_.engine.mode is Mode.INSERT

    type_text(ta_, 'hi there')
    assert rows(ta_) == ['> hi there']
    assert ta_.cursor(20) == (10, 0)


def test_insert_enter_newlines():
    ta_ = TextArea(prompt='> ')
    type_text(ta_, 'ab')
    press(ta_, 'enter')
    type_text(ta_, 'cd')
    assert ta_.doc.text() == 'ab\ncd'
    assert rows(ta_) == ['> ab', '  cd']
    assert ta_.cursor(20) == (4, 1)


def test_normal_enter_submits():
    submitted: list = []
    ta_ = TextArea(on_submit=submitted.append)
    type_text(ta_, 'hello')
    press(ta_, 'escape', 'enter')
    assert submitted == ['hello']
    assert ta_.doc.text() == ''
    assert ta_.engine.mode is Mode.INSERT  # ready for the next message


def test_modified_enter_submits_from_insert():
    submitted: list = []
    ta_ = TextArea(on_submit=submitted.append)
    type_text(ta_, 'one')
    press(ta_, Key('enter', ctrl=True))
    type_text(ta_, 'two')
    press(ta_, Key('enter', alt=True))
    assert submitted == ['one', 'two']


def test_empty_submit_is_dropped():
    submitted: list = []
    ta_ = TextArea(on_submit=submitted.append)
    press(ta_, Key('enter', ctrl=True))
    assert submitted == []


def test_growth_and_scroll():
    ta_ = TextArea(max_height=3)
    for i in range(5):
        type_text(ta_, f'line{i}')
        if i < 4:
            press(ta_, 'enter')

    # 5 lines, 3 visible, cursor at the bottom: viewport follows.
    assert rows(ta_) == ['line2', 'line3', 'line4']
    assert ta_.cursor(20) == (5, 2)

    # gg scrolls back to the top.
    press(ta_, 'escape', 'g', 'g')
    assert rows(ta_) == ['line0', 'line1', 'line2']
    assert ta_.cursor(20) == (0, 0)


def test_paste_stays_accessible():
    ta_ = TextArea(max_height=2)
    ta_.handle_event(PasteEvent('\n'.join(f'p{i}' for i in range(10))))
    assert len(rows(ta_)) == 2
    press(ta_, 'escape', 'g', 'g')
    assert rows(ta_)[0] == 'p0'


def test_hard_wrap_and_cursor():
    ta_ = TextArea(prompt='> ')
    type_text(ta_, 'abcdefgh')
    # width 6, prompt 2 -> text width 4: 'abcd' / 'efgh'
    assert rows(ta_, 6) == ['> abcd', '  efgh']
    assert ta_.cursor(6) == (6, 1)  # insert-mode cursor at eol slot


def test_search_decorations_render():
    ta_ = TextArea()
    ta_.handle_event(PasteEvent('foo bar foo'))
    press(ta_, 'escape')
    type_text(ta_, '/foo')

    styles = {seg.style for row in ta_.render(20) for seg in row}
    assert SEARCH_MATCH_TAG in styles

    press(ta_, 'enter')
    assert ta_.engine.mode is Mode.NORMAL


def test_vim_editing_through_events():
    ta_ = TextArea()
    ta_.handle_event(PasteEvent('foo bar baz'))
    press(ta_, 'escape')
    # dw at start deletes first word
    press(ta_, 'g', 'g', 'd', 'w')
    assert ta_.doc.text() == 'bar baz'
    # u undoes, ctrl+r redoes
    press(ta_, 'u')
    assert ta_.doc.text() == 'foo bar baz'
    press(ta_, Key('r', ctrl=True))
    assert ta_.doc.text() == 'bar baz'


def test_arrows_in_insert():
    ta_ = TextArea()
    type_text(ta_, 'ab')
    press(ta_, 'left')
    type_text(ta_, 'X')
    assert ta_.doc.text() == 'aXb'
