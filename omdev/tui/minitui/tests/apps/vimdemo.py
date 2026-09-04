"""
A tiny fullscreen vim clone on the alt-screen surface - the demotty successor, sharing the whole headless stack.

The same engine, document, and TextArea that power the chat input, composed differently: full screen, normal mode first,
'~' filler rows, a vim status line (mode / pending keys / cmdline, filename + modified flag + ruler), file ex commands -
:w [name], :q, :q!, :wq, ZZ-free minimalism - and a `:set [no]number` sliver (`--number` starts with it on). `/` search
with live highlighting works exactly as in the input textarea, because it's the same code.
"""
import os.path
import sys
import typing as ta

from omcore import dataclasses as dc
from omcore.text.highlights import get_highlighter

from ...controls.base import Control
from ...controls.stacks import stack_frame
from ...controls.status import StatusBar
from ...controls.textarea import TextArea
from ...docs.treesitter import get_tree_sitter_highlighter
from ...events.keys import Key
from ...events.types import Event
from ...events.types import KeyEvent
from ...runtime.base import App
from ...runtime.sync import SyncDriver
from ...screens.cells import Frame
from ...surfaces.alts import AltSurface
from ...text.segments import Segment
from ...text.styles import Style
from ...text.themes import DEFAULT_THEME
from ...text.themes import FOREGROUND
from ...text.themes import PRIMARY
from ...text.themes import SURFACE
from ...text.themes import TEXT_PRIMARY
from ...text.themes import TEXT_SECONDARY
from ...vim.options import get_language_options


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
                'code.keyword',
                'code.builtin',
                'code.def',
                'code.string',
                'code.comment',
                'code.number',
                'code.decorator',
                'code.type',
                'code.diff.add',
                'code.diff.del',
                'code.diff.hunk',
                'code.diff.meta',
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
    def __init__(
            self,
            driver: SyncDriver,
            path: str | None,
            lang: str | None = None,
            *,
            number: bool = False,
    ) -> None:
        super().__init__()

        self._driver = driver
        self._path = path

        ext: str | None = None
        highlighter = None
        if path is not None and '.' in os.path.basename(path):
            ext = os.path.basename(path).rsplit('.', 1)[-1]
            # tree-sitter (incremental) when available; zero-dep/pygments full-retokenize otherwise.
            highlighter = get_tree_sitter_highlighter(ext) or get_highlighter(ext)

        self._editor = TextArea(
            start_in_normal=True,
            ex_handler=self._ex,
            highlighter=highlighter,
            # Indent style follows the file extension ('go' edits with real tabs); --lang overrides.
            options=dc.replace(get_language_options(lang if lang is not None else ext), number=number),
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

    def _set(self, arg: str) -> str | None:
        """A sliver of :set - just the boolean 'number' option, with vim's 'no' prefix and '!' toggle suffix."""

        name = arg.removesuffix('!')
        toggle = name != arg
        off = name.startswith('no')
        name = name.removeprefix('no')
        if name not in ('number', 'nu'):
            return f'Unknown option: {arg}'

        engine = self._editor.engine
        opts = engine.options
        engine.set_options(dc.replace(opts, number=(not opts.number) if toggle else not off))
        return None

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
        if name in ('set', 'se'):
            return self._set(arg)
        return f'Not an editor command: {name}'

    ##
    # Events & rendering

    def handle_event(self, event: Event) -> None:
        if isinstance(event, KeyEvent) and event.key == Key('z', ctrl=True):
            self._driver.suspend()  # vim's ctrl+z (as a key only on extended-key terminals; else the kernel's)
            return
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
    args = sys.argv[1:]
    lang: str | None = None
    number = False
    while args and args[0].startswith('--'):
        opt = args.pop(0)
        if opt.startswith('--lang='):
            lang = opt.partition('=')[2]
        elif opt == '--number':
            number = True
        else:
            raise ValueError(f'Unknown option: {opt}')
    path = args[0] if args else None
    driver = SyncDriver(AltSurface(kitty_keys=True))
    app = VimDemoApp(driver, path, lang, number=number)
    try:
        driver.run(app)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
