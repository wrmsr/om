"""
The phase-2/3 proof: typing while streaming - now with the real vim engine in the input.

A fake stream commits paragraphs above while you edit in a vim-powered textarea: start typing (insert mode), Esc for
normal mode (motions, dw/ciw/u, visual, `/` incremental search with live highlighting), Enter in normal mode submits,
Enter in insert mode is a newline, ctrl+enter (kitty terminals) or alt+enter submits from insert. Paste something big:
the input grows to its max height then scrolls like a vim window. The status bar shows the spinner, the vim
mode/pending-keys/cmdline, and the last event. Ctrl-d exits.

Run: ./python -m x.minitui.apps.inputdemo
"""
import itertools
import typing as ta

from ...controls.spinners import Spinner
from ...controls.stacks import stack_frame
from ...controls.static import Static
from ...controls.status import StatusBar
from ...controls.textarea import TextArea
from ...events.keys import Key
from ...events.types import Event
from ...events.types import KeyEvent
from ...events.types import PasteEvent
from ...events.types import ResizeEvent
from ...runtime.drivers import App
from ...runtime.drivers import SyncDriver
from ...screens.cells import Frame
from ...screens.cells import line_from_segments
from ...surfaces.inlines import InlineSurface
from ...text.segments import Segment
from ...text.styles import Style
from ...text.themes import DEFAULT_THEME
from ...text.themes import SUCCESS
from ...text.themes import TEXT_SECONDARY
from ...text.wraps import wrap_segments
from .streamdemo import PARAGRAPHS


##


DEMO_THEME = DEFAULT_THEME.extend({
    'speaker.ai': Style(fg=SUCCESS, bold=True),
    'speaker.you': Style(fg=TEXT_SECONDARY, bold=True),
})


class InputDemoApp(App):
    def __init__(self, driver: SyncDriver) -> None:
        super().__init__()

        self._driver = driver

        self._spinner = Spinner()
        self._stream = Static()
        self._status = StatusBar(right=[('type, paste, Esc for normal mode', 'status.dim')])
        self._input = TextArea(
            prompt='> ',
            prompt_style='input.glyph',
            max_height=6,
            on_submit=self._submit,
            ex_handler=self._ex,
        )

        self._words = itertools.cycle(' '.join(PARAGRAPHS).split())
        self._streamed: list[str] = []

        driver.timers.call_every(.1, self._spin)
        driver.timers.call_every(.06, self._stream_word)

    ##
    # The fake stream

    def _spin(self) -> None:
        self._spinner.advance()
        self._refresh_status()
        self._driver.invalidate()

    def _stream_word(self) -> None:
        self._streamed.append(next(self._words))
        if len(self._streamed) >= 42:
            self._commit_parts('speaker.ai', 'ai', ' '.join(self._streamed))
            self._streamed = []
            self._stream.set_parts([])
        else:
            self._stream.set_parts([(' '.join(self._streamed), None)])
        self._driver.invalidate()

    ##
    # Input

    def _commit_parts(self, speaker_style: str, speaker: str, text: str) -> None:
        width = max(self._driver.surface.width, 8)
        rows: list[ta.Sequence[Segment]] = [
            [Segment(speaker, speaker_style)],
            *(
                wrapped
                for line in text.split('\n')
                for wrapped in wrap_segments([Segment(line)] if line else [], width)
            ),
            [],
        ]
        self._driver.commit([line_from_segments(row, DEMO_THEME) for row in rows])

    def _submit(self, text: str) -> None:
        self._commit_parts('speaker.you', 'you', text)

    def _ex(self, line: str) -> str | None:
        if line in ('q', 'q!', 'wq'):
            self._driver.stop()
            return None
        return f'Not an editor command: {line}'

    def _refresh_status(self) -> None:
        st = self._input.engine.status()
        mode_part = st.cmdline if st.cmdline is not None else st.mode_text
        self._status.set_left([
            (self._spinner.frame, 'status.spinner'),
            (' streaming  ', 'status.dim'),
            (mode_part, 'status.mode'),
            (f'  {st.pending}', 'status.dim'),
            (f'  {st.message}' if st.message else '', 'status.dim'),
        ])

    def handle_event(self, event: Event) -> None:
        if isinstance(event, KeyEvent):
            if event.key == Key('d', ctrl=True):
                self._driver.stop()
                return
            self._status.set_right([(f'last: {event.key}', 'status.dim')])
        elif isinstance(event, PasteEvent):
            self._status.set_right([(f'pasted {len(event.text)} chars', 'status.dim')])
        elif isinstance(event, ResizeEvent):
            self._status.set_right([(f'resized {event.width}x{event.height}', 'status.dim')])

        self._input.handle_event(event)
        self._refresh_status()
        self._driver.invalidate()

    ##
    # Rendering

    def render(self, width: int, max_height: int) -> Frame:
        return stack_frame(
            [self._stream, self._input, self._status],
            width=width,
            max_height=max_height,
            theme=DEMO_THEME,
            focus=self._input,
        )


def _main() -> None:
    driver = SyncDriver(InlineSurface(kitty_keys=True))
    app = InputDemoApp(driver)
    try:
        driver.run(app)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
