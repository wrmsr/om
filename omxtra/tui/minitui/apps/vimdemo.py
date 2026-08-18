"""
A tiny fullscreen vim clone on the alt-screen surface - the demotty successor, sharing the whole headless stack.

The same engine, document, and TextArea that power the chat input, composed differently: full screen, normal mode
first, '~' filler rows, a vim status line (mode / pending keys / cmdline, filename + modified flag + ruler), and file
ex commands - :w [name], :q, :q!, :wq, ZZ-free minimalism. `/` search with live highlighting works exactly as in the
input textarea, because it's the same code.

Run: ./python -m x.minitui.apps.vimdemo [path]
"""
import os.path
import sys
import typing as ta

from ..controls.base import Control
from ..controls.stacks import stack_frame
from ..controls.status import StatusBar
from ..controls.textarea import TextArea
from ..docs.treesitter import get_tree_sitter_highlighter
from ..events.types import Event
from ..runtime.drivers import App
from ..runtime.drivers import SyncDriver
from ..screens.cells import Frame
from ..surfaces.alts import AltSurface
from ..text.highlights import get_highlighter
from ..text.segments import Segment
from ..text.styles import Style
from ..text.themes import DEFAULT_THEME
from ..text.themes import FOREGROUND
from ..text.themes import PRIMARY
from ..text.themes import SURFACE
from ..text.themes import TEXT_PRIMARY
from ..text.themes import TEXT_SECONDARY


##


# Fullscreen editor: untinted syntax (no code-block background) and a surface-backed status bar.
VIM_THEME = DEFAULT_THEME.extend({
    'filler': Style(fg=TEXT_SECONDARY),
    'msg': Style(fg=TEXT_PRIMARY),
    'status.bar': Style(fg=FOREGROUND, bg=SURFACE),
    'status.mode': Style(fg=PRIMARY, bg=SURFACE, bold=True),
    'status.file': Style(fg=FOREGROUND, bg=SURFACE, bold=True),
    **{
        tag: Style(fg=style.fg, bold=style.bold, italic=style.italic)
        for tag, style in (
            (t, DEFAULT_THEME.resolve(t))
            for t in (
                'code.keyword', 'code.builtin', 'code.def', 'code.string', 'code.comment', 'code.number',
                'code.decorator', 'code.type', 'code.diff.add', 'code.diff.del', 'code.diff.hunk', 'code.diff.meta',
            )
        )
    },
})


class TildeFiller(Control):
    """vim's '~' rows for the space between end-of-buffer and the status line."""

    def __init__(self) -> None:
        super().__init__()

        self._height = 0

    def set_height(self, height: int) -> None:
        self._height = max(height, 0)

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        return [[Segment('~', 'filler')] for _ in range(self._height)]


class VimDemoApp(App):
    def __init__(self, driver: SyncDriver, path: str | None) -> None:
        super().__init__()

        self._driver = driver
        self._path = path

        highlighter = None
        if path is not None and '.' in os.path.basename(path):
            ext = os.path.basename(path).rsplit('.', 1)[-1]
            # tree-sitter (incremental) when available; zero-dep/pygments full-retokenize otherwise.
            highlighter = get_tree_sitter_highlighter(ext) or get_highlighter(ext)

        self._editor = TextArea(
            start_in_normal=True,
            ex_handler=self._ex,
            highlighter=highlighter,
        )
        self._filler = TildeFiller()
        self._status = StatusBar()

        if path is not None and os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                self._editor.engine.doc.set_text(f.read().rstrip('\n'))

        self._saved_version = self._editor.doc.version

    ##
    # Ex commands

    @property
    def _modified(self) -> bool:
        return self._editor.doc.version != self._saved_version

    def _write(self, path: str | None) -> str:
        target = path or self._path
        if target is None:
            return 'No file name'
        with open(target, 'w', encoding='utf-8') as f:
            f.write(self._editor.doc.text() + '\n')
        self._path = target
        self._saved_version = self._editor.doc.version
        return f'"{target}" written'

    def _ex(self, line: str) -> str | None:
        name, _, arg = line.partition(' ')
        arg = arg.strip()

        if name == 'w':
            return self._write(arg or None)
        if name == 'wq':
            message = self._write(arg or None)
            if 'written' in message:
                self._driver.stop()
            return message
        if name == 'q':
            if self._modified:
                return 'No write since last change (add ! to override)'
            self._driver.stop()
            return None
        if name == 'q!':
            self._driver.stop()
            return None
        return f'Not an editor command: {name}'

    ##
    # Events & rendering

    def handle_event(self, event: Event) -> None:
        self._editor.handle_event(event)
        self._driver.invalidate()

    def _refresh_status(self, width: int) -> None:
        st = self._editor.engine.status()
        cur = self._editor.engine.cursor

        left = st.cmdline if st.cmdline is not None else (st.message or st.mode_text)
        name = self._path if self._path is not None else '[No Name]'
        modified = ' [+]' if self._modified else ''

        self._status.set_left([
            (f'{left}  ', 'status.mode'),
            (st.pending, 'status.bar'),
        ])
        self._status.set_right([
            (f'{name}{modified}  ', 'status.file'),
            (f'{cur.row + 1},{cur.col + 1}', 'status.bar'),
        ])

    def render(self, width: int, max_height: int) -> Frame:
        self._refresh_status(width)

        # The status bar is elastic (long filenames wrap); measure it so the editor budget is exact.
        status_height = max(len(self._status.render(width)), 1)
        editor_budget = max(max_height - status_height, 1)
        self._editor.set_max_height(editor_budget)

        editor_height = len(self._editor.render(width))
        self._filler.set_height(editor_budget - editor_height)

        return stack_frame(
            [self._editor, self._filler, self._status],
            width=width,
            max_height=max_height,
            theme=VIM_THEME,
            focus=self._editor,
        )


def _main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else None
    driver = SyncDriver(AltSurface(kitty_keys=True))
    app = VimDemoApp(driver, path)
    try:
        driver.run(app)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
