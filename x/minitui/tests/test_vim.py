from ..docs.positions import Pos
from ..vim.engine import VimEngine
from ..vim.modes import Mode
from ..vim.parsing import ESC
from ..vim.status import SEARCH_CURRENT_TAG
from ..vim.status import SEARCH_MATCH_TAG
from ..vim.status import SELECTION_TAG


##
# Ported from x/vibes/minivim/tests/test_engine.py (adapted to the reshaped engine).


def make(text, keys='', cursor=(0, 0)):
    e = VimEngine(text)
    e.set_cursor(Pos(*cursor))
    e.send(keys)
    return e


def check(name, e, text=None, cursor=None, mode=None):
    if text is not None:
        assert e.render() == text, f'{name}: text {e.render()!r} != {text!r}'
    if cursor is not None:
        assert (e.cursor.row, e.cursor.col) == cursor, f'{name}: cursor {e.cursor} != {cursor}'
    if mode is not None:
        assert e.mode.name == mode, f'{name}: mode {e.mode.name} != {mode}'


def test_word_motions():
    s = 'foo bar_baz, qux'
    check('w over word',      make(s, 'w'),   cursor=(0, 4))
    check('w to punct',       make(s, 'ww'),  cursor=(0, 11))  # comma is its own word
    check('w past punct',     make(s, 'www'), cursor=(0, 13))
    check('3w = www',         make(s, '3w'),  cursor=(0, 13))
    check('W big word',       make(s, 'W'),   cursor=(0, 4))
    check('WW skips punct',   make(s, 'WW'),  cursor=(0, 13))
    check('e end of word',    make(s, 'e'),   cursor=(0, 2))
    check('ee',               make(s, 'ee'),  cursor=(0, 10))
    check('b back',           make(s, 'wwb'), cursor=(0, 4))
    check('b from mid-word',  make(s, 'b', (0, 6)), cursor=(0, 4))
    check('w lands on empty line', make('foo\n\nbar', 'w'),  cursor=(1, 0))
    check('w off empty line',      make('foo\n\nbar', 'ww'), cursor=(2, 0))
    check('w crosses lines',       make('foo\nbar', 'w'),    cursor=(1, 0))


def test_line_motions():
    e = make('a long line here\nab\nanother long line', '', (0, 10))
    e.send('j')
    check('j clamps col', e, cursor=(1, 1))
    e.send('j')
    check('j restores curswant', e, cursor=(2, 10))
    e = make('abcdef\nab\nabcdef', '$jj')
    check('$ pins curswant to EOL', e, cursor=(2, 5))
    check('G last line',  make('a\nb\nc', 'G'),  cursor=(2, 0))
    check('2G line 2',    make('a\nb\nc', '2G'), cursor=(1, 0))
    check('gg first',     make('a\nb\nc', 'Ggg'), cursor=(0, 0))
    check('G first non-blank', make('a\n   xb', 'G'), cursor=(1, 3))
    check('0 and ^', make('   abc', '$0'), cursor=(0, 0))
    check('^ first non-blank', make('   abc', '^'), cursor=(0, 3))


def test_exclusive_rule_payoffs():
    check('dw mid-line',  make('foo bar baz', 'dw', (0, 4)), text='foo baz')
    check("dw last word doesn't join lines",  # :help exclusive rule 1
          make('foo bar\nbaz', 'dw', (0, 4)), text='foo \nbaz', cursor=(0, 3))
    check('d2w at col0 goes linewise',  # :help exclusive rule 2
          make('foo bar\nbaz qux', 'd2w'), text='baz qux')
    check("db at col0 doesn't join",  # rule 1, backward motion
          make('foo bar\nbaz', 'db', (1, 0)), text='foo \nbaz')
    check('de inclusive', make('foo bar', 'de'), text=' bar')
    check('d$ / D',  make('foo bar', 'D', (0, 3)), text='foo')
    check('d0',      make('foo bar', 'd0', (0, 4)), text='bar')
    check('dG linewise', make('a\nb\nc\nd', 'dG', (1, 0)), text='a')
    check('dj deletes 2 lines', make('a\nb\nc', 'dj'), text='c')
    check('dgg', make('a\nb\nc', 'dgg', (1, 0)), text='c')


def test_counts_multiply():
    check('2d3w == d6w', make('a b c d e f g h', '2d3w'), text='g h')


def test_synonyms():
    check('x',        make('abc', 'x'), text='bc', cursor=(0, 0))
    check('3x',       make('abcdef', '3x'), text='def')
    check('x at EOL clamps', make('ab', '5x'), text='')
    check('X',        make('abc', 'X', (0, 1)), text='bc')
    check('s enters insert', make('abc', 'sZ' + ESC), text='Zbc')
    check('S clears line',   make('  foo\nbar', 'SZ' + ESC), text='Z\nbar')


def test_operators_doubled():
    check('dd',  make('a\nb\nc', 'dd'), text='b\nc')
    check('2dd', make('a\nb\nc', '2dd'), text='c')
    check('dd last line leaves empty buffer line', make('only', 'dd'), text='')
    check('cc', make('hello\nx', 'ccbye' + ESC), text='bye\nx')
    check('>> indents', make('foo\nbar', '>>'), text='    foo\nbar')
    check('> with motion is linewise', make('foo\nbar', '>j'), text='    foo\n    bar')
    check('<< dedents', make('        foo', '<<'), text='    foo')


def test_registers():
    check('yy p duplicates line', make('aaa\nbbb', 'yyp'), text='aaa\naaa\nbbb', cursor=(1, 0))
    check('dd p moves line down', make('aaa\nbbb\nccc', 'ddp'), text='bbb\naaa\nccc')
    check('dd P puts above',      make('aaa\nbbb', 'ddP'), text='aaa\nbbb')
    check('charwise p splices',   make('abc', 'xp'), text='bac', cursor=(0, 1))
    check('yw P',  make('foo bar', 'ywP'), text='foo foo bar')
    check('3p repeats', make('ab', 'x3p'), text='baaa', cursor=(0, 3))
    e = make('one\ntwo', '"ayyj"ap')
    check('named register', e, text='one\ntwo\none')
    e = make('aaa\nbbb\nccc', '"ayyj"Ayyj"ap')
    check('uppercase appends', e, text='aaa\nbbb\nccc\naaa\nbbb')
    check('y0 cursor to start', make('foobar', 'y0', (0, 3)), cursor=(0, 0))
    # multi-line charwise put (from visual yank)
    e = make('abXY\nZWcd', 'llvjhy')  # select "XY\nZW" charwise
    e.send('P')
    check('multi-line charwise put', e, text='abXY\nZWXY\nZWcd', cursor=(1, 1))


def test_cw_special_case():
    check('cw acts like ce (no trailing space)',
          make('hello world', 'cwhey' + ESC), text='hey world', cursor=(0, 2))
    check('cw on blank behaves like dw', make('a   b', 'cwX' + ESC, (0, 1)), text='aXb')


def test_find():
    s2 = 'a.b.c.d'
    check('f finds',   make(s2, 'f.'),  cursor=(0, 1))
    check('2f',        make(s2, '2f.'), cursor=(0, 3))
    check('f; repeat', make(s2, 'f.;'), cursor=(0, 3))
    check('f, reverse', make(s2, '2f.,'), cursor=(0, 1))
    check('t stops before', make(s2, 't.'), cursor=(0, 0))
    check('t; unsticks',    make(s2, 't.;'), cursor=(0, 2))
    check('dt.', make('abc.def', 'dt.'), text='.def')
    check('df.', make('abc.def', 'df.'), text='def')
    check('dF backward exclusive', make('abc.def', 'dF.', (0, 5)), text='abcef')
    check('f miss aborts whole op', make('abc', 'dfz'), text='abc')


def test_text_objects():
    check('diw', make('foo bar baz', 'diw', (0, 5)), text='foo  baz')
    check('daw', make('foo bar baz', 'daw', (0, 5)), text='foo baz')
    check('2diw = word+space', make('foo bar baz', '2diw'), text='bar baz')
    check('ciw', make('foo bar', 'ciwqux' + ESC, (0, 5)), text='foo qux')
    check('di( inner parens', make('f(a, b) x', 'di(', (0, 3)), text='f() x')
    check('da( around',       make('f(a, b) x', 'da(', (0, 3)), text='f x')
    check('di( cursor on open',  make('f(a)b', 'di(', (0, 1)), text='f()b')
    check('di( cursor on close', make('f(a)b', 'di(', (0, 3)), text='f()b')
    check('di( nested', make('(a(b)c)', 'di(', (0, 3)), text='(a()c)')
    check('di( outer from between', make('(a(b)c)', 'di(', (0, 1)), text='()')
    check('di{ multi-line', make('if {\n  body\n}', 'di{', (1, 2)), text='if {\n}')
    check('ci"', make('say "hi" now', 'ci"yo' + ESC, (0, 5)), text='say "yo" now')
    check('di" from before pair', make('say "hi" now', 'di"'), text='say "" now')
    check('dib alias', make('f(a)b', 'dib', (0, 2)), text='f()b')


def test_insert_mode_editing():
    check('i inserts', make('bc', 'ia' + ESC), text='abc')
    check('a appends', make('ac', 'ab' + ESC), text='abc')
    check('A end of line', make('ab', 'Ac' + ESC), text='abc')
    check('I first non-blank', make('  bc', 'Ia' + ESC), text='  abc')
    check('o opens below', make('a', 'ob' + ESC), text='a\nb')
    check('O opens above', make('b', 'Oa' + ESC), text='a\nb')
    check('Esc moves cursor left', make('xyz', 'ix' + ESC), cursor=(0, 0))
    check('enter splits line', make('abcd', 'a\n' + ESC, (0, 1)), text='ab\ncd')
    check('backspace joins', make('ab\ncd', 'i\x7f' + ESC, (1, 0)), text='abcd')


def test_replace_join():
    check('r replaces', make('abc', 'rx'), text='xbc')
    check('3r', make('abcdef', '3rx'), text='xxxdef', cursor=(0, 2))
    check('r past EOL fails', make('ab', '5rx'), text='ab')
    check('J joins with space', make('foo\n  bar', 'J'), text='foo bar', cursor=(0, 3))
    check('3J', make('a\nb\nc\nd', '3J'), text='a b c\nd')


def test_visual_mode():
    check('v-select + d', make('hello world', 'ved'), text=' world')
    check('visual y then p', make('hello world', 'veyP'), text='hellohello world')
    check('V linewise d', make('a\nb\nc', 'Vjd'), text='c')
    check('visual o swaps ends', make('abcdef', '3lvlohd'), text='abf')
    check('visual esc cancels, cursor stays', make('abc', 'vl' + ESC + 'x'), text='ac')
    check('v with t.', make('a.b.c', 'vt.d'), text='.b.c')


def test_dot_repeat():
    check('dw then .', make('aaa bbb ccc', 'dw.'), text='ccc')
    check('x then . .', make('abcdef', 'x..'), text='def')
    e = make('foo foo foo', 'ciwbar' + ESC + 'ww.')
    check('. repeats change incl. typed text', e, text='bar foo bar')
    e = make('abc', 'ohi' + ESC + '.')
    check('. repeats o with text', e, text='abc\nhi\nhi')


def test_undo():
    check('u undoes dd', make('a\nb', 'ddu'), text='a\nb')
    check('cw+typing is one undo unit', make('foo bar', 'cwqux' + ESC + 'u'), text='foo bar')
    check('uu walks back', make('ab', 'xxuu'), text='ab')
    check('u then redo-less state', make('abc', 'xu'), text='abc')


def test_register_indirection():
    check('c writes register too', make('foo bar', 'cwX' + ESC + '$p'), text='X barfoo')


def test_parser_robustness():
    check('Esc aborts pending op', make('abc', 'd' + ESC + 'x'), text='bc')
    check('mismatched op aborts', make('abc', 'dyx'), text='bc')  # dy invalid, x runs
    check('unknown key aborts cleanly', make('abc', 'dqx'), text='bc')


##
# New: features grown in the reshape.


def test_redo():
    e = make('abc', 'xx')
    assert e.render() == 'c'
    e.send('uu')
    assert e.render() == 'abc'
    e.redo()
    assert e.render() == 'bc'
    e.redo()
    assert e.render() == 'c'
    # A new change clears the redo stack.
    e.send('u')
    e.send('x')
    e.redo()
    assert e.render() == 'c'


def test_undo_restores_cursor():
    e = make('foo bar', 'dw', (0, 4))
    assert e.render() == 'foo '
    e.send('u')
    assert e.render() == 'foo bar'
    assert (e.cursor.row, e.cursor.col) == (0, 4)


def test_search_forward_and_n():
    e = make('alpha beta alpha beta', '/beta\r')
    assert (e.cursor.row, e.cursor.col) == (0, 6)
    e.send('n')
    assert (e.cursor.row, e.cursor.col) == (0, 17)
    e.send('n')  # wraps
    assert (e.cursor.row, e.cursor.col) == (0, 6)
    e.send('N')
    assert (e.cursor.row, e.cursor.col) == (0, 17)


def test_search_backward():
    e = make('x a x a x', '?a\r', (0, 8))
    assert (e.cursor.row, e.cursor.col) == (0, 6)


def test_search_operator_motion():
    # d/pattern is intentionally unsupported (cmdline only enters from an idle parser) - 'd' then '/' aborts the op
    # and enters search. But dn works.
    e = make('foo bar foo', '/bar\rgg')
    e.send('dn')
    assert e.render() == 'bar foo'


def test_search_status_and_decorations():
    e = make('aa bb aa', '/aa')
    # (fresh locals per read: mypy narrows the property otherwise)
    mode_during = e.mode
    assert mode_during is Mode.CMDLINE
    st = e.status()
    assert st.cmdline == '/aa'

    decs = e.decorations()
    tags = sorted(d.tag for d in decs)
    assert tags == sorted([SEARCH_CURRENT_TAG, SEARCH_MATCH_TAG])

    e.send('\r')
    mode_after = e.mode
    assert mode_after is Mode.NORMAL
    assert (e.cursor.row, e.cursor.col) == (0, 6)
    # Highlight persists until Esc.
    assert len(e.decorations()) == 2
    e.send(ESC)
    assert e.decorations() == []


def test_search_not_found_message():
    e = make('abc', '/zzz\r')
    assert 'not found' in e.status().message.lower()
    e.send(ESC)
    assert e.status().message == ''


def test_cmdline_escape_and_backspace():
    e = make('abc', '/ab' + ESC)
    assert e.mode is Mode.NORMAL
    e.send('/a\x7f\x7f')  # backspace past empty cancels
    assert e.mode is Mode.NORMAL


def test_ex_handler():
    seen = []

    def handler(line):
        seen.append(line)
        return f'ran {line}'

    e = VimEngine('abc', ex_handler=handler)
    e.send(':wq\r')
    assert seen == ['wq']
    assert e.status().message == 'ran wq'

    e2 = make('abc', ':boom\r')
    assert 'not an editor command' in e2.status().message.lower()


def test_visual_selection_decoration():
    e = make('abcdef', 'vll')
    (dec,) = e.decorations()
    assert dec.tag == SELECTION_TAG
    assert dec.span.start == Pos(0, 0)
    assert dec.span.end == Pos(0, 3)


def test_status_pending_keys():
    e = make('abc', '2d')
    assert e.status().pending == '2d'
    e.send('d')
    assert e.status().pending == ''


def test_insert_tokens():
    e = make('ab\ncd', 'i')
    e.feed('<down>')
    e.feed('<end>')
    e.feed('!')
    assert e.render() == 'ab\ncd!'
    e.feed('<up>')
    e.feed('<home>')
    e.feed('#')
    assert e.render() == '#ab\ncd!'


def test_normal_tokens():
    e = make('abc\ndef', '')
    e.feed('<down>')
    e.feed('<right>')
    assert (e.cursor.row, e.cursor.col) == (1, 1)
    e.feed('<end>')
    assert (e.cursor.row, e.cursor.col) == (1, 2)


def test_insert_text_paste():
    e = make('ab', 'i')
    e.insert_text('xy\nz')
    assert e.render() == 'xy\nzab'
    assert (e.cursor.row, e.cursor.col) == (1, 1)


def test_external_edit_clears_history():
    e = make('abc', 'x')
    assert e.render() == 'bc'
    e.doc.set_text('external')
    e.send('u')
    assert e.render() == 'external'  # history was invalidated, not corrupted


##
# Grown in the depth pass: %, ~, blockwise visual.


def test_percent_matching():
    check('% open->close', make('f(a(b)c)x', '%', (0, 1)), cursor=(0, 7))
    check('% close->open', make('f(a(b)c)x', '%', (0, 7)), cursor=(0, 1))
    check('% seeks first bracket on line', make('ab (c)', '%'), cursor=(0, 5))
    check('% multiline', make('if {\n  x\n}', '%', (0, 3)), cursor=(2, 0))
    check('d% deletes through match', make('a(bc)d', 'd%', (0, 1)), text='ad')
    check('% no bracket is a no-op', make('abc', '%', (0, 1)), cursor=(0, 1))


def test_tilde_toggles_case():
    check('~ toggles and advances', make('aBc', '~~'), text='Abc', cursor=(0, 2))
    check('3~', make('abc', '3~'), text='ABC', cursor=(0, 2))
    check('~ undoes as one unit', make('abc', '3~u'), text='abc')
    check('~ at eol clamps', make('ab', '5~'), text='AB')


def test_visual_block_basics():
    e = make('abcd\nefgh\nijkl', '')
    e.feed('l')
    e.feed('<c-v>')
    assert e.mode is Mode.VISUAL_BLOCK
    e.send('jjl')  # 3 rows x cols 1-2

    (dec,) = e.decorations()
    assert dec.span.kind.name == 'BLOCK'
    assert (dec.span.start.row, dec.span.start.col) == (0, 1)
    assert (dec.span.end.row, dec.span.end.col) == (2, 3)

    e.feed('d')
    assert e.render() == 'ad\neh\nil'
    assert e.mode is Mode.NORMAL


def test_visual_block_yank_put():
    e = make('abcd\nefgh', '')
    e.feed('<c-v>')
    e.send('jly')  # yank the 2x2 block at cols 0-1
    assert e.render() == 'abcd\nefgh'  # yank doesn't edit

    e.send('$p')  # block-paste after end of line 0
    assert e.render() == 'abcdab\nefghef'


def test_visual_block_paste_pads_short_lines():
    e = make('abcd\nx', '')
    e.feed('<c-v>')
    e.send('jy')  # 2x1 block: 'a', 'x'... anchor col0 row0 -> row1: pieces 'a','x'
    e.send('gg$p')
    assert e.render() == 'abcda\nx   x'


def test_visual_block_escape_and_toggle():
    e = make('abc', '')
    e.feed('<c-v>')
    m1 = e.mode
    assert m1 is Mode.VISUAL_BLOCK
    e.feed('<c-v>')  # toggles off
    m2 = e.mode
    assert m2 is Mode.NORMAL
    e.feed('v')
    e.feed('<c-v>')  # v -> block switch
    m3 = e.mode
    assert m3 is Mode.VISUAL_BLOCK
    e.feed(ESC)
    m4 = e.mode
    assert m4 is Mode.NORMAL


def test_visual_block_change_replicates():
    # Multi-cursor: block change types onto EVERY row, live - real vim replays at Esc, we show it as you type.
    e = make('abcd\nefgh', '')
    e.feed('<c-v>')
    e.send('jlc')
    assert e.mode is Mode.INSERT
    assert e.status().cursor_count == 2
    e.send('XY' + ESC)
    assert e.render() == 'XYcd\nXYgh'
    assert e.status().cursor_count == 1


##
# Multi-cursor.


def test_block_insert_replicates():
    e = make('one\ntwo\nthree', '')
    e.feed('<c-v>')
    e.send('jjI')
    assert e.status().cursor_count == 3
    e.send('>> ' + ESC)
    assert e.render() == '>> one\n>> two\n>> three'
    assert e.status().cursor_count == 1


def test_block_append_pads_short_lines():
    e = make('long line\nab\nmedium', '')
    e.send('$')          # col 8 on row 0
    e.feed('<c-v>')
    e.send('jjA')        # append at the block's right edge on all rows
    e.send('!' + ESC)
    assert e.render() == 'long line!\nab       !\nmedium   !'


def test_block_insert_skips_short_lines():
    e = make('abcdef\nab\nabcdef', '', (0, 4))
    e.feed('<c-v>')
    e.send('jjI')
    # Row 1 ('ab') doesn't reach col 4: vim skips it.
    assert e.status().cursor_count == 2
    e.send('X' + ESC)
    assert e.render() == 'abcdXef\nab\nabcdXef'


def test_add_cursor_api_typing_backspace_enter():
    e = make('aaa\nbbb', 'i')  # insert mode, cursor at (0,0)
    e.add_cursor(Pos(1, 0))
    e.send('X')
    assert e.render() == 'Xaaa\nXbbb'
    e.send('\x7f')  # backspace at both
    assert e.render() == 'aaa\nbbb'
    e.send('Y\r')   # type + enter at both
    assert e.render() == 'Y\naaa\nY\nbbb'


def test_multicursor_same_row_ordering():
    # Two cursors on one row: edits at the earlier position must shift the later cursor correctly.
    e = make('axbx', 'i')
    e.set_cursor(Pos(0, 1))
    e.add_cursor(Pos(0, 3))
    e.send('!')
    assert e.render() == 'a!xb!x'
    e.send('\x7f')
    assert e.render() == 'axbx'


def test_multicursor_merge_on_collision():
    e = make('ab', 'i')
    e.set_cursor(Pos(0, 1))
    e.add_cursor(Pos(0, 2))
    assert e.status().cursor_count == 2
    e.send('\x7f')  # both delete left; positions collide at col 0... second deletes 'b' -> both land at 0
    assert e.render() == ''
    assert e.status().cursor_count == 1


def test_multicursor_paste_and_undo_unit():
    e = make('a\nb', 'i')
    e.add_cursor(Pos(1, 0))
    e.insert_text('<<')
    assert e.render() == '<<a\n<<b'
    e.send(ESC)
    e.send('u')
    assert e.render() == 'a\nb'


def test_secondary_cursor_decorations():
    from ..vim.status import CURSOR_TAG  # noqa: PLC0415

    e = make('aaa\nbbb', 'i')
    e.add_cursor(Pos(1, 1))
    decs = [d for d in e.decorations() if d.tag == CURSOR_TAG]
    assert len(decs) == 1
    assert decs[0].span.start == Pos(1, 1)


##
# :s[ubstitute] and ex ranges.


def test_substitute_current_line():
    e = make('aa bb aa\naa', ':s/aa/XX/\r')
    assert e.render() == 'XX bb aa\naa'  # first occurrence, current line only
    assert '1 substitution on 1 line' in e.status().message


def test_substitute_g_flag():
    e = make('aa bb aa\naa', ':s/aa/XX/g\r')
    assert e.render() == 'XX bb XX\naa'


def test_substitute_percent_range():
    e = make('aa\nbb aa\naa aa', ':%s/aa/X/g\r')
    assert e.render() == 'X\nbb X\nX X'
    assert '4 substitutions on 3 lines' in e.status().message


def test_substitute_line_range():
    e = make('a\na\na\na', ':2,3s/a/b/\r')
    assert e.render() == 'a\nb\nb\na'


def test_substitute_dot_dollar_range():
    e = make('a\na\na', 'j')  # cursor on line 2
    e.send(':.,$s/a/z/\r')
    assert e.render() == 'a\nz\nz'


def test_substitute_regex_and_groups():
    e = make('foo123bar', ':s/([a-z]+)(\\d+)/\\2-\\1/\r')
    assert e.render() == '123-foobar'


def test_substitute_ampersand_and_literal():
    e = make('cat', ':s/cat/[&]/\r')
    assert e.render() == '[cat]'
    e2 = make('cat', ':s/cat/a\\&b/\r')
    assert e2.render() == 'a&b'


def test_substitute_ignorecase_flag():
    e = make('Foo foo', ':s/foo/x/gi\r')
    assert e.render() == 'x x'


def test_substitute_alternate_separator():
    e = make('a/b', ':s#a/b#c#\r')
    assert e.render() == 'c'
    # Escaped separator inside the pattern.
    e2 = make('a/b', ':s/a\\/b/c/\r')
    assert e2.render() == 'c'


def test_substitute_newline_replacement():
    e = make('one two', ':s/ /\\r/\r')
    assert e.render() == 'one\ntwo'


def test_substitute_empty_pattern_reuses_search():
    e = make('hay needle hay', '/needle\r')
    e.send(':s//FOUND/\r')
    assert e.render() == 'hay FOUND hay'

    e2 = make('abc', ':s//x/\r')
    assert 'no previous search' in e2.status().message.lower()
    assert e2.render() == 'abc'


def test_substitute_errors_and_undo():
    e = make('abc', ':s/zzz/x/\r')
    assert 'not found' in e.status().message.lower()
    assert e.render() == 'abc'

    e2 = make('abc', ':s/[/x/\r')
    assert 'invalid pattern' in e2.status().message.lower()

    # The whole substitute is one undo unit.
    e3 = make('a a\na a', ':%s/a/b/g\r')
    assert e3.render() == 'b b\nb b'
    e3.send('u')
    assert e3.render() == 'a a\na a'


def test_substitute_visual_range():
    e = make('a\na\na\na', '')
    e.send('jVj')          # linewise-select rows 2-3
    e.send(':')            # ex from visual: range prefilled
    assert e.status().cmdline == ":'<,'>"
    e.send('s/a/Q/\r')
    assert e.render() == 'a\nQ\nQ\na'


def test_bare_range_jumps():
    e = make('l1\nl2\nl3\nl4', ':3\r')
    assert e.cursor.row == 2
    e.send(':$\r')
    assert e.cursor.row == 3
    e.send(':1\r')
    assert e.cursor.row == 0


def test_non_builtin_ex_still_delegates():
    seen: list = []

    def handler(line):
        seen.append(line)
        return 'ok'

    e = VimEngine('abc', ex_handler=handler)
    e.send(':w somefile\r')
    assert seen == ['w somefile']
    # 'set' starts with 's' but has no separator - must reach the app handler, not the substitute parser.
    e.send(':set number\r')
    assert seen == ['w somefile', 'set number']
