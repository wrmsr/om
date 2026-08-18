"""
The minitui chat surface: a commit-model inline TUI (streamed markdown scrollback above a live tail, vim-powered
input, warm-window tool cards).

This module is pure UI - it knows nothing of agents or sessions. `main` wires `on_submit` to the harness session,
`output` drives the streaming / display methods from agent events, and `input` drives the permission-card flow. All
methods here are loop-side (the agent shares the asyncio loop with the driver); none block.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import inject as inj
from omxtra.tui import minitui as mt

from ..config import Config


##


THEME = mt.DEFAULT_THEME.extend({
    'speaker.ai': mt.Style(fg=mt.SUCCESS, bold=True),
    'speaker.you': mt.Style(fg=mt.TEXT_SECONDARY, bold=True),
    'echo.command': mt.Style(fg=mt.TEXT_SECONDARY, italic=True),
})


##


class MinituiChatApp(mt.App):
    def __init__(
            self,
            driver: mt.AsyncDriver,
    ) -> None:
        super().__init__()

        self._driver = driver

        self._tail = mt.MarkdownTail(backend=mt.get_markdown_stream())
        self._spinner = mt.Spinner()
        self._popup = mt.SuggestionsPopup()
        self._status = mt.StatusBar(right=[('/ for commands, ctrl+d quits', 'status.dim')])
        self._input = mt.TextArea(
            prompt='> ',
            prompt_style='input.glyph',
            max_height=8,
            on_submit=self._on_submit_text,
            ex_handler=self._ex,
        )
        self._history = mt.InputHistory()

        self._card: mt.Card | None = None
        self._layout: mt.StackLayout | None = None

        self._busy = False
        self._thinking = False
        self._streaming = False

        self._commands: ta.Sequence[tuple[str, str]] = ()

        # The submit hook - `main` points this at the session prompt pump.
        self.on_submit: ta.Callable[[str], None] | None = None

        driver.timers.call_every(.1, self._tick)

    ##
    # Committing (scrollback side)

    @property
    def width(self) -> int:
        return max(self._driver.surface.width, 8)

    def _commit_rows(self, rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        self._driver.commit([mt.line_from_segments(row, THEME) for row in rows])

    def display_rows(self, rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        """Commit pre-rendered (already width-safe) rows followed by a blank separator."""

        self._commit_rows([*rows, []])
        self._driver.invalidate()

    def display_markdown(self, text: str) -> None:
        self.display_rows(mt.render_blocks(mt.parse_markdown(text), self.width, highlighter=mt.highlight_code))

    def display_inline(self, segments: ta.Sequence[mt.Segment]) -> None:
        self.display_rows(mt.wrap_segments(segments, self.width) if segments else [[]])

    ##
    # Chat flow

    def show_user_message(self, text: str) -> None:
        self._commit_rows([
            [mt.Segment('you', 'speaker.you')],
            *self._tail.render_settled(mt.parse_markdown(text), self.width),
            [],
        ])
        self._driver.invalidate()

    def show_command_echo(self, text: str) -> None:
        self.display_rows([[mt.Segment(text, 'echo.command')]])

    def begin_ai_turn(self) -> None:
        self._busy = True
        self._commit_rows([[mt.Segment('ai', 'speaker.ai')]])
        self._driver.invalidate()

    def end_ai_turn(self) -> None:
        self.stream_break()
        self._busy = False
        self._thinking = False
        self._refresh_status()
        self._driver.invalidate()

    ##
    # Streaming markdown

    def stream_feed(self, text: str) -> None:
        self._streaming = True
        self._tail.feed(text)
        if (settled := self._tail.pop_settled()):
            self._commit_rows(self._tail.render_settled(settled, self.width))
        self._driver.invalidate()

    def stream_break(self) -> None:
        """A content block ended: settle the whole tail into scrollback."""

        if not self._streaming:
            return
        self._streaming = False
        blocks = self._tail.finalize()
        if blocks:
            self._commit_rows(self._tail.render_settled(blocks, self.width))
        self._commit_rows([[]])
        self._driver.invalidate()

    def set_thinking(self, thinking: bool) -> None:
        self._thinking = thinking
        self._refresh_status()
        self._driver.invalidate()

    ##
    # Tool cards. Tools execute sequentially within a turn, so a single live-card slot suffices; a new card displaces
    # (finalizes) any leftover one.

    def begin_permission_card(
            self,
            title: str,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]],
            on_respond: ta.Callable[[bool], None],
    ) -> None:
        self.finalize_card()

        def respond(allowed: bool) -> None:
            card = self._card
            if card is not None:
                if allowed:
                    card.set_state(mt.CardState.RUNNING)
                    card.set_summary([(title, 'card.summary'), ('  running...', 'card.summary.dim')])
                else:
                    card.set_state(mt.CardState.DENIED)
                    card.set_summary([(title, 'card.summary'), ('  denied', 'card.summary.dim')])
                    self._driver.timers.call_later(.6, self.finalize_card)
            on_respond(allowed)
            self._driver.invalidate()

        self._card = mt.Card(
            [(title, 'card.summary'), ('  awaiting confirmation', 'card.summary.dim')],
            state=mt.CardState.CONFIRMING,
            detail=list(detail_rows),
            on_confirm=respond,
        )
        self._driver.invalidate()

    def tool_started(self, title: str, detail_rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        card = self._card
        if card is not None and card.state is mt.CardState.RUNNING:
            # The permission card already covers this execution.
            return
        self.finalize_card()
        self._card = mt.Card(
            [(title, 'card.summary'), ('  running...', 'card.summary.dim')],
            state=mt.CardState.RUNNING,
            detail=list(detail_rows),
        )
        self._driver.invalidate()

    def tool_finished(
            self,
            title: str,
            *,
            ok: bool,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]] | None = None,
    ) -> None:
        card = self._card
        if card is None:
            return
        card.set_state(mt.CardState.COMPLETE if ok else mt.CardState.FAILED)
        card.set_summary([(title, 'card.summary'), ('  done' if ok else '  failed', 'card.summary.dim')])
        if detail_rows is not None:
            card.set_detail(list(detail_rows))
        self._driver.timers.call_later(.8, self.finalize_card)
        self._driver.invalidate()

    def finalize_card(self) -> None:
        card = self._card
        if card is None:
            return
        self._card = None
        self._commit_rows([*card.render(self.width), []])
        self._driver.invalidate()

    ##
    # Input

    def set_commands(self, commands: ta.Iterable[tuple[str, str]]) -> None:
        self._commands = tuple(commands)

    def _on_submit_text(self, text: str) -> None:
        self._history.add(text)
        self._popup.clear()
        if (cb := self.on_submit) is not None:
            cb(text)

    def _ex(self, line: str) -> str | None:
        if line in ('q', 'q!', 'wq'):
            self._driver.stop()
            return None
        return f'Not an editor command: {line}'

    def _update_popup(self) -> None:
        text = self._input.doc.text()
        if text.startswith('/') and '\n' not in text and ' ' not in text:
            self._popup.set_items(
                mt.SuggestionItem(name, desc)
                for name, desc in self._commands
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
            self._driver.stop()
            return True

        if (card := self._card) is not None:
            if key == mt.Key('f10') and card.state is mt.CardState.CONFIRMING:
                card.respond(True)
                return True
            if key == mt.Key('f2') and card.state is mt.CardState.CONFIRMING:
                card.respond(False)
                return True
            if key == mt.Key('o', ctrl=True):
                card.toggle_expanded()
                return True

        if key == mt.Key('tab') and self._popup.visible:
            if (item := self._popup.cycle()) is not None:
                self._input.set_text(item.label)
            return True

        cursor = self._input.engine.cursor
        at_first_line = cursor.row == 0
        at_last_line = cursor.row == self._input.doc.line_count() - 1

        if key == mt.Key('p', ctrl=True) or (key == mt.Key('up') and at_first_line):
            self._history_step(back=True)
            return True
        if key == mt.Key('n', ctrl=True) or (key == mt.Key('down') and at_last_line):
            self._history_step(back=False)
            return True

        return False

    ##
    # Events & rendering

    def _tick(self) -> None:
        if self._busy:
            self._spinner.advance()
            self._refresh_status()
            self._driver.invalidate()

    def _refresh_status(self) -> None:
        st = self._input.engine.status()
        mode_part = st.cmdline if st.cmdline is not None else st.mode_text
        activity = 'thinking' if self._thinking else ('streaming' if self._busy else 'idle')
        self._status.set_left([
            (self._spinner.frame if self._busy else ' ', 'status.spinner'),
            (f' {activity}  ', 'status.dim'),
            (mode_part or '', 'status.mode'),
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
        controls: list[mt.Control] = [
            self._tail,
            *([self._card] if self._card is not None else []),
            self._popup,
            self._input,
            self._status,
        ]
        self._layout = mt.stack_layout(
            controls,
            width=width,
            max_height=max_height,
            theme=THEME,
            focus=self._input,
        )
        return self._layout.frame


##


def _provide_driver(surface: mt.InlineSurface) -> mt.AsyncDriver:
    return mt.AsyncDriver(surface)


def bind_app(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.bind(mt.InlineSurface(kitty_keys=True)),
        inj.bind(_provide_driver, singleton=True),
        inj.bind(MinituiChatApp, singleton=True),
    )
