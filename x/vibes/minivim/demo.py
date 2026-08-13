"""
A real terminal frontend for mini_vim in ~60 lines, proving the adapter claim: the engine never rendered anything and
never read a keyboard -- a frontend just (1) pumps decoded keys into Engine.feed() and (2) redraws from state.

Quit: Ctrl-Q
"""
import curses
import sys

from .engine import Engine
from .engine import ListBuffer
from .engine import Mode


##


SAMPLE = """\
def greet(name, punct):
    message = "hello, " + name
    return message + punct

words = [greet(w, "!") for w in ("world", "vim", "python")]
print(words)

Try: dw ciw di( f( ; 2dd yy p >> u . ve V\
"""


def decode(wch) -> str:
    """Map curses keys to the engine's key alphabet (plain chars + ESC)."""

    if isinstance(wch, str):
        return '\x7f' if wch == '\x08' else wch  # unify backspace
    return {
        curses.KEY_BACKSPACE: '\x7f',
        curses.KEY_ENTER: '\n',
        curses.KEY_LEFT: 'h',
        curses.KEY_RIGHT: 'l',
        curses.KEY_UP: 'k',
        curses.KEY_DOWN: 'j',
    }.get(wch, '')


def main(stdscr):
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else SAMPLE
    eng = Engine(ListBuffer(text.rstrip('\n')))
    curses.raw()
    stdscr.keypad(True)
    curses.set_escdelay(25)  # make ESC feel instant

    top = 0  # first visible buffer row (scrolling lives in the frontend too)
    while True:
        h, w = stdscr.getmaxyx()
        view_h = h - 1
        top = min(max(0, eng.cursor.row - view_h + 1), max(top, 0))
        if eng.cursor.row < top:
            top = eng.cursor.row
        if eng.cursor.row >= top + view_h:
            top = eng.cursor.row - view_h + 1

        stdscr.erase()
        for y in range(view_h):
            r = top + y
            if r >= eng.buf.line_count():
                stdscr.addstr(y, 0, '~', curses.A_DIM)
            else:
                stdscr.addnstr(y, 0, eng.buf.get_line(r), w - 1)
        mode = {
            Mode.NORMAL: '',
            Mode.INSERT: '-- INSERT --',
            Mode.VISUAL: '-- VISUAL --',
            Mode.VISUAL_LINE: '-- VISUAL LINE --',
        }[eng.mode]
        pos = f'{eng.cursor.row + 1},{eng.cursor.col + 1}'
        stdscr.addnstr(
            h - 1,
            0,
            f'{mode:<20}{pos:>{max(0, w - 22)}}',
            w - 1,
            curses.A_REVERSE,
        )
        col = eng.cursor.col
        if eng.mode is not Mode.INSERT:  # normal cursor can't pass last char
            col = min(col, max(0, len(eng.buf.get_line(eng.cursor.row)) - 1))
        stdscr.move(eng.cursor.row - top, min(col, w - 1))
        stdscr.refresh()

        wch = stdscr.get_wch()
        if wch == '\x11':  # Ctrl-Q quits
            return
        key = decode(wch)
        if key:
            eng.feed(key)


if __name__ == '__main__':
    curses.wrapper(main)
