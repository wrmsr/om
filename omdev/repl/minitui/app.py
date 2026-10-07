"""
The standalone minitui repl: the console with a vim-powered input (syntax highlighted per language), a status bar, the
`/` popup for switching interpreters, and history. Outputs commit to scrollback as they arrive. Loop-neutral - the
driver and runner come in; `main.py` is the asyncio entry point.
"""
import functools
import typing as ta

from omcore import dataclasses as dc

from ... import minitui as mt
from ..runners import Runner
from ..sessions import Session
from .console import Console
from .rendering import render_note
from .styles import REPL_THEME


##


class ReplApp(mt.App):
    def __init__(
            self,
            driver: mt.AsyncioDriver,
            session: Session,
            *,
            runner: Runner,
    ) -> None:
        super().__init__()

        self._driver = driver
        self._session = session

        self._spinner = mt.Spinner()
        self._popup = mt.SuggestionsPopup()
        self._status = mt.StatusBar(right=[('ctrl+j runs  / commands  ctrl+d quits', 'status.dim')])
        self._input = mt.TextArea(
            max_height=16,
            on_submit=self._submit,
            ex_handler=self._ex,
        )
        self._history = mt.InputHistory()
        self._layout: mt.StackLayout | None = None

        self._console = Console(
            session,
            self._input,
            runner=runner,
            commit=self._commit,
            width=lambda: self.width,
            on_exit=self.quit,
            on_change=driver.invalidate,
        )
        self._console.activate()

        self._refresh_status()

        driver.timers.call_every(.1, self._tick)

    @property
    def width(self) -> int:
        return max(self._driver.surface.width, 8)

    @property
    def console(self) -> Console:
        return self._console

    @property
    def input(self) -> mt.TextArea:  # noqa: A003
        return self._input

    def _commit(self, rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        self._driver.commit([mt.line_from_segments(row, REPL_THEME) for row in rows])

    ##
    # Commands

    def _commands(self) -> ta.Mapping[str, tuple[str, ta.Callable[[str], None]]]:
        out: dict[str, tuple[str, ta.Callable[[str], None]]] = {
            f'/{name}': (f'switch to {name}', functools.partial(self._cmd_switch, name))
            for name in self._session.names
        }
        out['/help'] = ('list commands', self._cmd_help)
        out['/quit'] = ('quit', self._cmd_quit)
        return out

    def _cmd_switch(self, name: str, arg: str) -> None:
        self._console.switch(name)

    def _cmd_help(self, arg: str) -> None:
        self._commit([
            *([mt.Segment(name, 'repl.prompt'), mt.Segment(f'  {desc}', 'status.dim')]
              for name, (desc, _) in self._commands().items()),
            [],
        ])

    def _cmd_quit(self, arg: str) -> None:
        self.quit()

    def quit(self) -> None:
        self._driver.stop()

    ##
    # Input

    def _submit(self, text: str) -> None:
        self._history.add(text)
        self._popup.clear()

        if text.startswith('/') and '\n' not in text:
            name, _, arg = text.partition(' ')
            if (entry := self._commands().get(name)) is not None:
                entry[1](arg.strip())
            else:
                self._commit([*render_note(f'unknown command: {name}', self.width), []])
            return

        self._console.submit(text)

    def _ex(self, line: str) -> str | None:
        if line in ('q', 'q!', 'wq'):
            self.quit()
            return None
        return f'Not an editor command: {line}'

    def interrupt(self) -> None:
        """ctrl+c: stop the running execution, or else clear the input."""

        if not self._console.cancel():
            self._input.clear()
        self._driver.invalidate()

    def _update_popup(self) -> None:
        text = self._input.doc.text()
        if text.startswith('/') and '\n' not in text and ' ' not in text:
            self._popup.set_items(
                mt.SuggestionItem(name, desc)
                for name, (desc, _) in self._commands().items()
                if name.startswith(text)
            )
        else:
            self._popup.clear()

    def _history_step(self, *, back: bool) -> None:
        current = self._input.doc.text()
        entry = self._history.previous(current) if back else self._history.next(current)
        if entry is not None:
            self._input.set_text(entry)

    def _handle_app_key(self, event: mt.KeyEvent) -> bool:
        key = event.key

        if key == mt.Key('d', ctrl=True):
            self.quit()
            return True

        if key == mt.Key('c', ctrl=True):  # a key only on extended-key terminals; the kernel's SIGINT reaches `main`
            self.interrupt()
            return True

        if key == mt.Key('z', ctrl=True):
            self._driver.suspend()
            return True

        if key == mt.Key('tab') and self._popup.visible:
            if (item := self._popup.cycle()) is not None:
                self._input.set_text(item.label)
            return True

        cursor = self._input.engine.cursor
        at_first_line = cursor.row == 0
        at_last_line = cursor.row == self._input.doc.line_count() - 1

        if key in (mt.Key('p', ctrl=True), mt.Key('up')) and at_first_line:
            self._history_step(back=True)
            return True
        if key in (mt.Key('n', ctrl=True), mt.Key('down')) and at_last_line:
            self._history_step(back=False)
            return True

        return False

    ##
    # Events & rendering

    def _tick(self) -> None:
        if self._console.is_running:
            self._spinner.advance()
            self._refresh_status()
            self._driver.invalidate()

    def _refresh_status(self) -> None:
        st = self._input.engine.status()
        mode_part = st.cmdline if st.cmdline is not None else st.mode_text
        self._status.set_left([
            (self._spinner.frame if self._console.is_running else ' ', 'status.spinner'),
            (' ', 'status.dim'),
            *self._console.status_parts(),
            (f'  {mode_part}' if mode_part else '', 'status.mode'),
            (f'  {st.pending}' if st.pending else '', 'status.dim'),
            (f'  {st.message}' if st.message else '', 'status.dim'),
        ])

    def _handle_mouse(self, event: mt.MouseEvent) -> None:
        if self._layout is None or (hit := self._layout.hit(event.y)) is None:
            return
        control, local_y = hit
        local = dc.replace(event, y=local_y)
        if control is self._popup:
            if (item := self._popup.item_at(local_y)) is not None:
                self._input.set_text(item.label)
            return
        control.handle_event(local)

    def handle_event(self, event: mt.Event) -> None:
        if isinstance(event, mt.MouseEvent):
            self._handle_mouse(event)
        elif not (isinstance(event, mt.KeyEvent) and self._handle_app_key(event)):
            self._input.handle_event(event)

        self._update_popup()
        self._refresh_status()
        self._driver.invalidate()

    def render(self, width: int, max_height: int) -> mt.Frame:
        self._layout = mt.stack_layout(
            [self._popup, self._input, self._status],
            width=width,
            max_height=max_height,
            theme=REPL_THEME,
            focus=self._input,
        )
        return self._layout.frame
