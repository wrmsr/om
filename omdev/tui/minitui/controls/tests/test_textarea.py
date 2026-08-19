from ...docs.positions import Pos
from ...events.keys import Key
from ...events.keys import key_text
from ...events.types import KeyEvent
from ...events.types import PasteEvent
from ...text.highlights import PythonHighlighter
from ...text.segments import segments_text
from ...vim.modes import Mode
from ...vim.options import get_language_options
from ...vim.status import CURSOR_TAG
from ...vim.status import SEARCH_MATCH_TAG
from ...vim.status import SEARCH_MATCH_TAG as _SM
from ..textarea import TextArea


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


def test_tab_and_control_display():
    # noexpandtab profile (go): the document holds a real tab; the display shows tabstop spaces, and the cursor math
    # agrees.
    ta_ = TextArea(options=get_language_options('go'))
    press(ta_, 'tab')
    type_text(ta_, 'x')
    assert ta_.doc.text() == '\tx'
    assert rows(ta_) == ['    x']
    assert ta_.cursor(20) == (5, 0)

    # Default profile: expandtab - the tab key writes spaces to the next tabstop column.
    ta3 = TextArea()
    press(ta3, 'tab')
    type_text(ta3, 'x')
    press(ta3, 'tab')
    assert ta3.doc.text() == '    x   '

    ta2 = TextArea()
    ta2.handle_event(PasteEvent('a\x01b'))
    assert rows(ta2) == ['a^Ab']
    assert ta2.cursor(20) == (4, 0)


def test_syntax_highlighting_base_layer():
    ta_ = TextArea(highlighter=PythonHighlighter())
    ta_.handle_event(PasteEvent('def foo():\n    return "s"'))

    styles = {seg.style for row in ta_.render(40) for seg in row}
    assert 'code.keyword' in styles
    assert 'code.def' in styles
    assert 'code.string' in styles

    # Decorations layer over syntax: search highlight wins where they overlap.
    press(ta_, 'escape')
    type_text(ta_, '/return')
    styles = {seg.style for row in ta_.render(40) for seg in row}
    assert _SM in styles or 'vim.search.current' in styles
    # And the keyword tag no longer covers the matched word.
    texts_by_style = {(seg.style, seg.text) for row in ta_.render(40) for seg in row}
    assert ('code.keyword', 'return') not in texts_by_style


##
# Viewport operations (the view side of vim: scrolling belongs to the window).


def make_tall(n=20, max_height=5):
    ta_ = TextArea(max_height=max_height, start_in_normal=True)
    ta_.doc.set_text('\n'.join(f'line{i}' for i in range(n)))
    ta_.engine.set_cursor(Pos(0, 0))
    rows(ta_)  # establish geometry
    return ta_


def test_ctrl_d_u_half_page():
    ta_ = make_tall()
    press(ta_, Key('d', ctrl=True))
    assert ta_.engine.cursor.row == 2
    press(ta_, Key('d', ctrl=True))
    assert ta_.engine.cursor.row == 4
    press(ta_, Key('u', ctrl=True))
    assert ta_.engine.cursor.row == 2


def test_ctrl_f_b_full_page():
    # Vim's ctrl+f/b: a full page less the two-line overlap (height 5 -> 3 rows per press).
    ta_ = make_tall()
    press(ta_, Key('f', ctrl=True))
    assert ta_.engine.cursor.row == 3
    press(ta_, Key('f', ctrl=True))
    assert ta_.engine.cursor.row == 6
    press(ta_, Key('b', ctrl=True))
    assert ta_.engine.cursor.row == 3
    press(ta_, Key('b', ctrl=True), Key('b', ctrl=True))
    assert ta_.engine.cursor.row == 0


def test_ctrl_e_y_scrolls_view():
    ta_ = make_tall()
    assert rows(ta_)[0] == 'line0'
    press(ta_, Key('e', ctrl=True))
    r = rows(ta_)
    assert r[0] == 'line1'
    # The cursor was pushed to stay visible.
    assert ta_.engine.cursor.row >= 1
    press(ta_, Key('y', ctrl=True))
    assert rows(ta_)[0] == 'line0'


def test_zz_zt_zb():
    ta_ = make_tall()
    ta_.engine.set_cursor(Pos(10, 0))
    rows(ta_)

    press(ta_, 'z', 't')
    assert rows(ta_)[0] == 'line10'

    press(ta_, 'z', 'z')
    r = rows(ta_)
    assert r[2] == 'line10'  # centered in a 5-row viewport

    press(ta_, 'z', 'b')
    assert rows(ta_)[-1] == 'line10'


def test_hml_screen_lines():
    ta_ = make_tall()
    ta_.engine.set_cursor(Pos(10, 0))
    press(ta_, 'z', 't')  # viewport now shows 10..14
    press(ta_, 'L')
    assert ta_.engine.cursor.row == 14
    press(ta_, 'M')
    assert ta_.engine.cursor.row == 12
    press(ta_, 'H')
    assert ta_.engine.cursor.row == 10


def test_view_keys_yield_to_pending_commands():
    ta_ = make_tall()
    # 'd' then 'H' must not be hijacked by the view layer (it aborts the op instead; dH is unsupported).
    press(ta_, 'd')
    assert ta_.engine.status().pending == 'd'
    press(ta_, 'H')
    assert ta_.doc.line(0) == 'line0'  # nothing deleted, nothing moved by view


def test_ctrl_v_block_from_textarea():
    ta_ = TextArea(start_in_normal=True)
    ta_.doc.set_text('abcd\nefgh')
    press(ta_, Key('v', ctrl=True))
    assert ta_.engine.mode is Mode.VISUAL_BLOCK
    press(ta_, 'j', 'l', 'd')
    assert ta_.doc.text() == 'cd\ngh'


def test_multicursor_rendering_in_textarea():
    ta_ = TextArea(start_in_normal=True)
    ta_.doc.set_text('aaa\nbbb\nccc')
    press(ta_, Key('v', ctrl=True))
    press(ta_, 'j', 'j', 'I')  # block insert: 3 cursors
    assert ta_.engine.status().cursor_count == 3

    # Secondary cursors render as tagged cells (the primary is the terminal cursor).
    styles = {seg.style for row in ta_.render(20) for seg in row}
    assert CURSOR_TAG in styles

    type_text(ta_, 'zz')
    assert ta_.doc.text() == 'zzaaa\nzzbbb\nzzccc'

    # A secondary cursor parked at end-of-line renders as a styled space beyond the text.
    press(ta_, 'escape')
    ta_.engine.set_cursor(Pos(0, 0))
    press(ta_, '$')
    press(ta_, Key('v', ctrl=True))
    press(ta_, 'j', 'A')
    rows_ = ta_.render(20)
    eol_cells = [seg for row in rows_ for seg in row if seg.style == CURSOR_TAG and seg.text == ' ']
    assert eol_cells


def test_ctrl_j_submits_from_insert():
    submitted: list = []
    ta_ = TextArea(on_submit=submitted.append)
    type_text(ta_, 'hello')
    press(ta_, Key('j', ctrl=True))
    assert submitted == ['hello']
    assert ta_.engine.mode is Mode.INSERT

    # Without a submit handler (the vimdemo editor), ctrl+j is not consumed.
    ta2 = TextArea(start_in_normal=True)
    assert not ta2.handle_event(KeyEvent(Key('j', ctrl=True)))


def test_all_modified_enters_submit():
    submitted: list = []
    ta_ = TextArea(on_submit=submitted.append)
    for i, key in enumerate([
        Key('enter', ctrl=True),
        Key('enter', alt=True),
        Key('enter', shift=True),
    ]):
        type_text(ta_, f'm{i}')
        press(ta_, key)
    assert submitted == ['m0', 'm1', 'm2']


def test_insert_readline_chords():
    ta_ = TextArea()
    type_text(ta_, 'foo bar')

    press(ta_, Key('a', ctrl=True))
    assert ta_.engine.cursor == Pos(0, 0)
    press(ta_, Key('e', ctrl=True))
    assert ta_.engine.cursor == Pos(0, 7)
    press(ta_, Key('b', ctrl=True), Key('b', ctrl=True))
    assert ta_.engine.cursor == Pos(0, 5)
    press(ta_, Key('f', ctrl=True))
    assert ta_.engine.cursor == Pos(0, 6)

    press(ta_, Key('b', alt=True))
    assert ta_.engine.cursor == Pos(0, 4)
    press(ta_, Key('f', alt=True))
    assert ta_.engine.cursor == Pos(0, 7)

    press(ta_, Key('backspace', alt=True))
    assert ta_.doc.text() == 'foo '
    press(ta_, Key('u', ctrl=True))
    assert ta_.doc.text() == ''


def test_insert_ctrl_p_n_move_lines():
    ta_ = TextArea()
    type_text(ta_, 'one')
    press(ta_, 'enter')
    type_text(ta_, 'two')
    assert ta_.engine.cursor == Pos(1, 3)

    press(ta_, Key('p', ctrl=True))
    assert ta_.engine.cursor == Pos(0, 3)
    press(ta_, Key('n', ctrl=True))
    assert ta_.engine.cursor == Pos(1, 3)


def test_readline_chords_are_insert_only():
    # In NORMAL mode the emacs chords stay the app's business (return False, unhandled).
    ta_ = TextArea()
    type_text(ta_, 'foo')
    press(ta_, 'escape')
    assert not ta_.handle_event(KeyEvent(Key('a', ctrl=True), text=None))
    assert not ta_.handle_event(KeyEvent(Key('p', ctrl=True), text=None))
    assert ta_.doc.text() == 'foo'
