"""
The minitui chat surface: a commit-model inline TUI (streamed markdown scrollback above a live tail, vim-powered
input, warm-window tool cards).

This module is pure UI - it knows nothing of agents or sessions. `main` wires `on_submit` to the harness session,
`output` drives the streaming / display methods from agent events, and `input` drives the permission-card flow. All
methods here are loop-side (the agent shares the asyncio loop with the driver); none block.
"""
import collections
import enum
import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore.text import highlights as hl
from omdev import minitui as mt

from .... import llm
from ....core import ui


CardRows: ta.TypeAlias = tuple[tuple[mt.Segment, ...], ...]


##


THEME = mt.DEFAULT_THEME.extend({
    'speaker.ai': mt.Style(fg=mt.SUCCESS, bold=True),
    'speaker.you': mt.Style(fg=mt.TEXT_SECONDARY, bold=True),
    'turn.info': mt.Style(fg=mt.MUTED),
    'echo.command': mt.Style(fg=mt.TEXT_SECONDARY, italic=True),
    'turn.aborted': mt.Style(fg=mt.TEXT_SECONDARY, italic=True),
})


Speaker: ta.TypeAlias = ta.Literal['you', 'ai']

SPEAKER_VALS: frozenset[Speaker] = frozenset(['you', 'ai'])
MAX_SPEAKER_LEN = max(map(len, SPEAKER_VALS))

STYLES_BY_SPEAKER: ta.Mapping[Speaker, str] = {
    'you': 'speaker.you',
    'ai': 'speaker.ai',
}


def _freeze_rows(rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> CardRows:
    return tuple(tuple(row) for row in rows)


@dc.dataclass()
class _ToolCardEntry:
    title: str
    call_summary: str | None
    base_detail: CardRows
    card: mt.Card

    ready_to_finalize: bool = False
    finalize_timer: mt.AsyncioTimer | None = None


@dc.dataclass(frozen=True)
class _PermissionCardRequest:
    key: str
    title: str
    call_summary: str | None
    detail: CardRows
    on_respond: ta.Callable[[bool], None]

    # Invoked only when the turn is over (`abort_ai_turn`) - never because of UI bookkeeping. Any task still parked on
    # the ask at that point is dead or detached, so the asker may unwind it as a cancellation.
    on_cancel: ta.Callable[[], None] | None = None


class _CardSpacer(mt.Control):
    """The blank row that follows every tool card, live and committed alike."""

    def render(self, width: int) -> ta.Sequence[ta.Sequence[mt.Segment]]:
        return [[]]


##


class AppKey(enum.StrEnum):
    CANCEL = enum.auto()
    EXIT = enum.auto()
    SUSPEND = enum.auto()

    CARD_ALLOW = enum.auto()
    CARD_DENY = enum.auto()
    CARD_EXPAND = enum.auto()

    POPUP_CYCLE = enum.auto()

    HISTORY_PREV = enum.auto()
    HISTORY_NEXT = enum.auto()


APP_KEY_MAP: ta.Final[ta.Mapping[AppKey, mt.Key | ta.Sequence[mt.Key]]] = {
    AppKey.CANCEL: mt.Key('q', ctrl=True),
    AppKey.EXIT: mt.Key('d', ctrl=True),
    # Reaches here only on extended-key terminals; on the legacy wire the kernel turns ctrl+z into SIGTSTP itself and
    # the driver's handler takes the same path.
    AppKey.SUSPEND: mt.Key('z', ctrl=True),

    AppKey.CARD_ALLOW: mt.Key('f10'),
    AppKey.CARD_DENY: mt.Key('f2'),
    AppKey.CARD_EXPAND: mt.Key('o', ctrl=True),

    AppKey.POPUP_CYCLE: mt.Key('tab'),

    AppKey.HISTORY_PREV: (mt.Key('p', ctrl=True), mt.Key('up')),
    AppKey.HISTORY_NEXT: (mt.Key('n', ctrl=True), mt.Key('down')),
}


APP_KEY_REVERSE_MAP: ta.Final[ta.Mapping[mt.Key, AppKey]] = col.make_map((
    (mk, ak)
    for ak, mks in APP_KEY_MAP.items()
    for mk in ([mks] if isinstance(mks, mt.Key) else mks)
), strict=True)


##


class AppQuitSignal(ui.QuitSignal):
    """
    Routes `/quit` through the app's quit funnel, so it sequences like ctrl+d and `:q` instead of raising through the
    turn.
    """

    def __init__(self, *, app: MinituiChatApp) -> None:
        super().__init__()

        self._app = app

    async def quit(self) -> None:
        self._app.request_quit()


##


class MinituiChatApp(mt.App):
    def __init__(
            self,
            driver: mt.AsyncioDriver,
    ) -> None:
        super().__init__()

        self._driver = driver

        self._tail = mt.MarkdownTail(backend=mt.get_markdown_stream())
        self._spinner = mt.Spinner()
        self._popup = mt.SuggestionsPopup()
        self._status = mt.StatusBar()
        self._input = mt.TextArea(
            max_height=16,
            on_submit=self._on_submit_text,
            ex_handler=self._ex,
            options=mt.vim.VimOptions(
                number=True,
                numberwidth=1,
            ),
        )
        self._history = mt.InputHistory()

        self._cards: collections.OrderedDict[str, _ToolCardEntry] = collections.OrderedDict()
        self._card_spacer = _CardSpacer()
        self._permission_queue: collections.deque[_PermissionCardRequest] = collections.deque()
        self._active_permission: _PermissionCardRequest | None = None
        self._layout: mt.StackLayout | None = None

        self._busy = False
        self._thinking = False
        self._streaming = False
        self._cancelling = False

        self._commands: ta.Sequence[tuple[str, str]] = ()

        # The submit hook - `main` points this at the session prompt pump.
        self.on_submit: ta.Callable[[str], None] | None = None
        self.on_cancel: ta.Callable[[], bool] | None = None
        self.on_quit: ta.Callable[[], None] | None = None

        self._refresh_status()

        driver.timers.call_every(.1, self._tick)

    ##
    # Committing (scrollback side)

    @property
    def width(self) -> int:
        return max(self._driver.surface.width, 8)

    @property
    def is_busy(self) -> bool:
        return self._busy

    @property
    def is_cancelling(self) -> bool:
        return self._cancelling

    def _commit_rows(self, rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        self._driver.commit([mt.line_from_segments(row, THEME) for row in rows])

    def display_rows(self, rows: ta.Sequence[ta.Sequence[mt.Segment]]) -> None:
        """Commit pre-rendered (already width-safe) rows followed by a blank separator."""

        self._commit_rows([*rows, []])
        self._driver.invalidate()

    def _parse_markdown(self, text: str) -> list[mt.MdBlock]:
        # Non-streamed content parses one-shot through a fresh instance of the same backend the streaming tail uses, so
        # immediate-mode responses and echoed prompts get full fidelity (pdcmark's real inline engine, tables) rather
        # than the internal fallback parser - without touching the live tail's state.
        return mt.parse_markdown_with(mt.get_markdown_stream(), text)

    def _render_markdown(self, text: str) -> list[list[mt.Segment]]:
        return mt.render_markdown_blocks(self._parse_markdown(text), self.width, highlighter=hl.highlight_code)

    def display_markdown(self, text: str) -> None:
        self.display_rows(self._render_markdown(text))

    def display_inline(self, segments: ta.Sequence[mt.Segment]) -> None:
        self.display_rows(mt.wrap_segments(segments, self.width) if segments else [[]])

    def display_text(self, text: str, style: mt.StyleLike | None = None) -> None:
        """Newline-safe plain-text display: splits into rows, wraps each, commits as one block."""

        out: list[ta.Sequence[mt.Segment]] = []
        for row in mt.split_segment_lines([(text, style)]):
            out.extend(mt.wrap_segments(row, self.width) if row else [[]])
        self.display_rows(out)

    ##
    # Chat flow

    def _build_turn_header(self, speaker: ta.Literal['you', 'ai']) -> list[mt.Segment]:
        speaker_style = STYLES_BY_SPEAKER[speaker]
        info_s = f'{lang.localnow().strftime("%d-%m-%Y %H:%M:%S")}'
        return [
            mt.Segment(speaker, speaker_style),
            mt.Segment(' ' * (MAX_SPEAKER_LEN - len(speaker) + 2)),
            mt.Segment(info_s, 'turn.info'),
        ]

    def show_user_message(self, text: str) -> None:
        # Not the tail's `render_settled`: that path separates a stream cycle's commits from each other, and a queued
        # submission lands mid-stream.
        self._commit_rows([
            self._build_turn_header('you'),
            *self._render_markdown(text),
            [],
        ])
        self._driver.invalidate()

    def show_command_echo(self, text: str) -> None:
        self.display_text(text, 'echo.command')

    def begin_ai_turn(self) -> None:
        self._busy = True
        self._cancelling = False
        self._commit_rows([self._build_turn_header('ai')])
        self._refresh_status()
        self._driver.invalidate()

    def end_ai_turn(self) -> None:
        self.stream_break()
        self._busy = False
        self._thinking = False
        self._cancelling = False
        self._refresh_status()
        self._driver.invalidate()

    def set_cancelling(self) -> None:
        """
        A cancellation is under way but the turn has not ended yet: the run is still unwinding - a tool's process being
        stopped, a parked ask - and the turn closes only when its terminal event arrives. Until then, say so.
        """

        if not self._busy or self._cancelling:
            return

        self._cancelling = True
        for entry in self._cards.values():
            if not entry.card.is_terminal:
                self._set_tool_card_summary(entry, 'cancelling...')
        self._refresh_status()
        self._driver.invalidate()

    def abort_ai_turn(self, *, cancelled: bool) -> None:
        self.stream_break()

        requests = [
            *([self._active_permission] if self._active_permission is not None else []),
            *self._permission_queue,
        ]
        self._active_permission = None
        self._permission_queue.clear()
        for request in requests:
            if request.on_cancel is not None:
                request.on_cancel()

        state = mt.CardState.CANCELLED if cancelled else mt.CardState.FAILED
        status = 'cancelled' if cancelled else 'failed'
        for entry in self._cards.values():
            entry.card.set_on_confirm(None)
            if not entry.card.is_terminal:
                entry.card.set_state(state)
                self._set_tool_card_summary(entry, status)
            entry.ready_to_finalize = True
        self._flush_ready_cards()

        if self._busy:
            # Close the open `ai` block visibly even when nothing streamed - a bare header would otherwise run straight
            # into the next prompt.
            self._commit_rows([[mt.Segment('× cancelled' if cancelled else '✗ failed', 'turn.aborted')], []])

        self._busy = False
        self._thinking = False
        self._cancelling = False
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
    # Tool cards

    def _set_tool_card_summary(self, entry: _ToolCardEntry, status: str) -> None:
        entry.card.set_summary([
            (entry.title, 'card.summary'),
            (f'  {entry.call_summary}' if entry.call_summary is not None else '', 'card.summary.dim'),
            (f'  {status}', 'card.summary.dim'),
        ])

    def _add_tool_card(
            self,
            key: str,
            title: str,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]],
            *,
            state: mt.CardState,
            call_summary: str | None = None,
    ) -> _ToolCardEntry:
        frozen_detail = _freeze_rows(detail_rows)
        entry = _ToolCardEntry(
            title=title,
            call_summary=call_summary,
            base_detail=frozen_detail,
            card=mt.Card(
                state=state,
                detail=frozen_detail,
            ),
        )
        self._set_tool_card_summary(entry, 'running...')
        self._cards[key] = entry
        return entry

    def _activate_next_permission(self) -> None:
        if self._active_permission is not None:
            return

        # F10/F2 are global bindings, so only one queued card may advertise them at a time.
        if not self._permission_queue:
            return
        request = self._permission_queue.popleft()

        # The card is display; the ask is a tool parked mid-execution. If the card was finalized out from under a queued
        # ask, re-present it on a fresh card - withdrawing a live turn's ask would surface in its executor as a
        # cancellation indistinguishable from the user's.
        if (entry := self._cards.get(request.key)) is None:
            entry = self._add_tool_card(
                request.key,
                request.title,
                request.detail,
                state=mt.CardState.PENDING,
                call_summary=request.call_summary,
            )

        def respond(allowed: bool) -> None:
            self._respond_permission(request, allowed)

        self._active_permission = request
        entry.card.set_state(mt.CardState.CONFIRMING)
        self._set_tool_card_summary(entry, 'awaiting confirmation')
        entry.card.set_on_confirm(respond)

    def _respond_permission(self, request: _PermissionCardRequest, allowed: bool) -> None:
        if self._active_permission is not request:
            return

        self._active_permission = None
        if (entry := self._cards.get(request.key)) is not None:
            entry.card.set_on_confirm(None)
            if allowed:
                entry.card.set_state(mt.CardState.RUNNING)
                self._set_tool_card_summary(entry, 'running...')
            else:
                entry.card.set_state(mt.CardState.DENIED)
                self._set_tool_card_summary(entry, 'denied')
                self._finalize_card_later(entry, .6)

        try:
            request.on_respond(allowed)
        finally:
            self._activate_next_permission()
            self._driver.invalidate()

    def begin_permission_card(
            self,
            key: str,
            title: str,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]],
            on_respond: ta.Callable[[bool], None],
            *,
            call_summary: str | None = None,
            on_cancel: ta.Callable[[], None] | None = None,
    ) -> None:
        if (
                (self._active_permission is not None and self._active_permission.key == key) or
                any(request.key == key for request in self._permission_queue)
        ):
            raise RuntimeError(f'Tool card already has a pending permission request: {key!r}')

        if (entry := self._cards.get(key)) is None:
            entry = self._add_tool_card(
                key,
                title,
                (),
                state=mt.CardState.PENDING,
                call_summary=call_summary,
            )
        else:
            entry.title = title
            if call_summary is not None:
                entry.call_summary = call_summary
            entry.ready_to_finalize = False
            self._cancel_finalize(entry)

        frozen_detail = _freeze_rows(detail_rows)
        entry.card.set_state(mt.CardState.PENDING)
        self._set_tool_card_summary(entry, 'queued for confirmation')
        entry.card.set_detail([*entry.base_detail, *frozen_detail])
        entry.card.set_on_confirm(None)

        self._permission_queue.append(_PermissionCardRequest(
            key=key,
            title=title,
            call_summary=entry.call_summary,
            detail=frozen_detail,
            on_respond=on_respond,
            on_cancel=on_cancel,
        ))
        self._activate_next_permission()
        self._driver.invalidate()

    def tool_started(
            self,
            key: str,
            title: str,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]],
            *,
            call_summary: str | None = None,
    ) -> None:
        frozen_detail = _freeze_rows(detail_rows)
        if (entry := self._cards.get(key)) is None:
            self._add_tool_card(
                key,
                title,
                frozen_detail,
                state=mt.CardState.RUNNING,
                call_summary=call_summary,
            )
        else:
            entry.title = title
            entry.call_summary = call_summary
            entry.base_detail = frozen_detail
            entry.ready_to_finalize = False
            self._cancel_finalize(entry)
            if entry.card.state not in (mt.CardState.PENDING, mt.CardState.CONFIRMING):
                entry.card.set_state(mt.CardState.RUNNING)
                self._set_tool_card_summary(entry, 'running...')
                entry.card.set_detail(frozen_detail)
                entry.card.set_on_confirm(None)
        self._driver.invalidate()

    def tool_updated(
            self,
            key: str,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]],
    ) -> None:
        """Live detail for a running card. A card which is not running, or not there at all, ignores it."""

        if (entry := self._cards.get(key)) is None or entry.card.state is not mt.CardState.RUNNING:
            return

        entry.card.set_detail(_freeze_rows(detail_rows))
        self._driver.invalidate()

    def tool_finished(
            self,
            key: str,
            title: str,
            *,
            ok: bool,
            call_summary: str | None = None,
            detail_rows: ta.Sequence[ta.Sequence[mt.Segment]] | None = None,
    ) -> None:
        if (entry := self._cards.get(key)) is None:
            entry = self._add_tool_card(
                key,
                title,
                (),
                state=mt.CardState.RUNNING,
                call_summary=call_summary,
            )

        entry.title = title
        if call_summary is not None:
            entry.call_summary = call_summary
        entry.card.set_on_confirm(None)
        entry.card.set_state(mt.CardState.COMPLETE if ok else mt.CardState.FAILED)
        self._set_tool_card_summary(entry, 'done' if ok else 'failed')
        if detail_rows is not None:
            entry.card.set_detail(detail_rows)
        self._finalize_card_later(entry, .8)
        self._driver.invalidate()

    def _flush_ready_cards(self) -> None:
        # A later tool may finish first, but scrollback should retain the model's tool-call order.
        while self._cards:
            key, entry = self._cards.popitem(last=False)
            if not entry.ready_to_finalize:
                self._cards[key] = entry
                self._cards.move_to_end(key, last=False)
                return
            self._cancel_finalize(entry)
            self._commit_rows([*entry.card.render(self.width), []])  # as displayed: the card and its spacer row

    def _cancel_finalize(self, entry: _ToolCardEntry) -> None:
        if (timer := entry.finalize_timer) is not None:
            timer.cancel()
            entry.finalize_timer = None

    def _finalize_card_later(self, entry: _ToolCardEntry, delay_s: float) -> None:
        # One pending finalize per entry: reactivation (`tool_started`, `begin_permission_card`) and flushing cancel it,
        # so a timer from an earlier lifecycle of the same key can never finalize a live successor.
        self._cancel_finalize(entry)

        def fn() -> None:
            entry.finalize_timer = None
            entry.ready_to_finalize = True
            self._flush_ready_cards()
            self._driver.invalidate()

        entry.finalize_timer = self._driver.timers.call_later(delay_s, fn)

    ##
    # Input

    def set_commands(self, commands: ta.Iterable[tuple[str, str]]) -> None:
        self._commands = tuple(commands)

    def _on_submit_text(self, text: str) -> None:
        self._history.add(text)
        self._popup.clear()
        if (cb := self.on_submit) is not None:
            cb(text)

    def request_quit(self) -> None:
        """
        Every quit path funnels here. `main` points `on_quit` at its shutdown sequence; unwired, the driver just stops.
        """

        if (fn := self.on_quit) is not None:
            fn()
        else:
            self._driver.stop()

    def _ex(self, line: str) -> str | None:
        if line in ('q', 'q!', 'wq'):
            self.request_quit()
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

        app_key = APP_KEY_REVERSE_MAP.get(key)

        if app_key is AppKey.CANCEL and (cancel := self.on_cancel) is not None and cancel():
            return True

        if app_key is AppKey.EXIT:
            self.request_quit()
            return True

        if app_key is AppKey.SUSPEND:
            self._driver.suspend()
            return True

        permission_card = None
        if (
                (permission := self._active_permission) is not None and
                (entry := self._cards.get(permission.key)) is not None
        ):
            permission_card = entry.card

        if permission_card is not None:
            if app_key is AppKey.CARD_ALLOW:
                permission_card.respond(True)
                return True
            if app_key is AppKey.CARD_DENY:
                permission_card.respond(False)
                return True

        card = permission_card
        if card is None and self._cards:
            card_key, entry = self._cards.popitem(last=True)
            self._cards[card_key] = entry
            card = entry.card
        if card is not None:
            if app_key is AppKey.CARD_EXPAND:
                card.toggle_expanded()
                return True

        if app_key is AppKey.POPUP_CYCLE and self._popup.visible:
            if (item := self._popup.cycle()) is not None:
                self._input.set_text(item.label)
            return True

        cursor = self._input.engine.cursor
        at_first_line = cursor.row == 0
        at_last_line = cursor.row == self._input.doc.line_count() - 1

        # History only at the buffer edge, arrow-style - mid-buffer, ctrl+p/n fall through to the editor as readline
        # line movement.
        if app_key is AppKey.HISTORY_PREV and at_first_line:
            self._history_step(back=True)
            return True
        if app_key is AppKey.HISTORY_NEXT and at_last_line:
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

    @dc.dataclass(frozen=True, kw_only=True)
    class Usage:
        input: int = 0
        input_cached: int = 0
        output: int = 0
        reasoning: int = 0

        #

        _SUFFIXES: ta.ClassVar = (
            (1_000_000_000_000_000, 'q'),
            (1_000_000_000_000, 't'),
            (1_000_000_000, 'b'),
            (1_000_000, 'm'),
            (1_000, 'k'),
        )

        @classmethod
        def _render_int(cls, n: int) -> str:
            a = abs(n)

            for scale, suffix in cls._SUFFIXES:
                if a >= scale:
                    value = n / scale
                    digits = len(str(int(abs(value))))
                    places = max(0, 3 - digits)

                    s = f'{value:.{places}f}'.rstrip('0').rstrip('.')
                    return f'{s}{suffix}'

            return str(n)

        def render(self) -> str:
            return ' '.join([
                f'{p}{self._render_int(v)}'
                for p, v in
                [
                    ('i', self.input),
                    ('c', self.input_cached),
                    ('o', self.output),
                    ('r', self.reasoning),
                ]
                if v
            ])

    _usage = Usage()

    def add_token_usage(self, usage: llm.TokenUsage) -> None:
        self._usage = MinituiChatApp.Usage(
            input=self._usage.input + max((usage.input or 0) - (usage.cache_read or 0), 0),
            input_cached=self._usage.input_cached + (usage.cache_read or 0),
            output=self._usage.output + max((usage.output or 0) - (usage.reasoning or 0), 0),
            reasoning=self._usage.reasoning + (usage.reasoning or 0),
        )

    def _refresh_status(self) -> None:
        st = self._input.engine.status()
        mode_part = st.cmdline if st.cmdline is not None else st.mode_text

        if self._cancelling:
            activity = 'cancelling'
        elif self._thinking:
            activity = 'thinking'
        elif self._busy:
            activity = 'streaming'
        else:
            activity = 'idle'

        self._status.set_left([
            (self._spinner.frame if self._busy else ' ', 'status.spinner'),
            (f' {activity}  ', 'status.dim'),
            (mode_part or '', 'status.mode'),
            (f'  {st.pending}' if st.pending else '', 'status.dim'),
            (f'  {st.message}' if st.message else '', 'status.dim'),
        ])

        self._status.set_right([
            (self._usage.render(), 'status.text'),
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
        if isinstance(event, mt.InputEofEvent):
            # The input is gone for good: the same way out as ctrl+d, so a turn in flight is wound down while the driver
            # is still bound and what it leaves behind reaches scrollback.
            self.request_quit()
        elif isinstance(event, mt.MouseEvent):
            self._handle_mouse(event)
        elif not (isinstance(event, mt.KeyEvent) and self._handle_app_key(event)):
            self._input.handle_event(event)

        self._update_popup()
        self._refresh_status()
        self._driver.invalidate()

    def render(self, width: int, max_height: int) -> mt.Frame:
        permission_card = None
        if (
                (permission := self._active_permission) is not None and
                (entry := self._cards.get(permission.key)) is not None
        ):
            permission_card = entry.card
        cards = [entry.card for entry in self._cards.values() if entry.card is not permission_card]
        if permission_card is not None:
            cards.append(permission_card)

        # Every live card is followed by the blank row its committed form gets in `_flush_ready_cards`, so finalizing
        # a card never changes the live region's geometry - it commits exactly as displayed.
        controls: list[mt.Control] = [self._tail]
        for card in cards:
            controls.extend((card, self._card_spacer))
        controls.extend((self._popup, self._input, self._status))
        self._layout = mt.stack_layout(
            controls,
            width=width,
            max_height=max_height,
            theme=THEME,
            focus=self._input,
        )
        return self._layout.frame
