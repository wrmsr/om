"""
The chat-head-shaped demo: streaming markdown, history, slash commands - the whole commit-model pipeline.

Fake 'ai' responses stream word-by-word as markdown: settled blocks (closed paragraphs, fenced code with real python/
diff highlighting, lists, quotes) commit to scrollback as they finish; only the unsettled tail re-renders. Messages are
numbered - the registry pattern that keeps future browse/copy features possible over dead scrollback ('/show 2'
re-commits a message's raw source, standing in for '/pbcopy').

Input is the vim textarea (Esc for normal mode, /search, u/ctrl+r, ...). Up/ctrl+p and down/ctrl+n walk history when the
cursor is on the first/last line (vim j/k still work inside multi-line drafts). '/' opens the command popup - tab
cycles, enter runs. Ctrl-d quits.

Run: ./python -m x.minitui.apps.chatdemo
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..controls.cards import Card
from ..controls.cards import CardState
from ..controls.history import InputHistory
from ..controls.markdown import MarkdownTail
from ..controls.markdown import get_markdown_stream
from ..controls.spinners import Spinner
from ..controls.stacks import StackLayout
from ..controls.stacks import stack_layout
from ..controls.static import Static
from ..controls.status import StatusBar
from ..controls.suggestions import SuggestionItem
from ..controls.suggestions import SuggestionsPopup
from ..controls.textarea import TextArea
from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import MouseEvent
from ..runtime.drivers import App
from ..runtime.drivers import SyncDriver
from ..screens.cells import Frame
from ..screens.cells import line_from_segments
from ..surfaces.inlines import InlineSurface
from ..text.markdown import parse_markdown
from ..text.segments import Segment
from ..text.styles import Style
from ..text.themes import DEFAULT_THEME
from ..text.themes import SUCCESS
from ..text.themes import TEXT_SECONDARY


##


CHAT_THEME = DEFAULT_THEME.extend({
    'speaker.ai': Style(fg=SUCCESS, bold=True),
    'speaker.you': Style(fg=TEXT_SECONDARY, bold=True),
    'speaker.num': Style(fg=TEXT_SECONDARY),
})


CANNED_RESPONSES: ta.Sequence[str] = [
    (
        '# Streaming markdown\n'
        '\n'
        'Each **block** below commits to scrollback the moment it settles - a closed paragraph, a finished list, a '
        'closed code fence. Only the *unsettled tail* re-renders, so long chats cost nothing.\n'
        '\n'
        '- settled blocks are dead scrollback (native, tmux-friendly)\n'
        '- the live tail is retained-frame diffed\n'
        '- code fences highlight zero-dep: `python` and `diff` today\n'
        '\n'
        '```python\n'
        '@cached\n'
        'def settle(blocks: list[Block]) -> int:\n'
        '    """One commit per settled block."""\n'
        '    return sum(1 for b in blocks if b.done)  # cheap\n'
        '```\n'
        '\n'
        '> Committed lines are real terminal history - copy them, scroll them, keep them after exit.\n'
    ),
    (
        '## A diff, for good measure\n'
        '\n'
        '```diff\n'
        '--- a/render.py\n'
        '+++ b/render.py\n'
        '@@ -1,3 +1,3 @@\n'
        '-screen.repaint_everything()\n'
        '+screen.diff_and_commit()\n'
        ' flush()\n'
        '```\n'
        '\n'
        'And a [link](https://example.com) plus ~~struck~~ text, then a rule:\n'
        '\n'
        '---\n'
    ),
]


@dc.dataclass(frozen=True)
class ChatMessage(lang.Final):
    number: int
    speaker: str
    text: str


class ChatDemoApp(App):
    def __init__(
            self,
            driver: SyncDriver,
            *,
            md_backend: str | None = None,
    ) -> None:
        super().__init__()

        self._driver = driver

        self._spinner = Spinner()
        self._tail = MarkdownTail(backend=get_markdown_stream(md_backend))
        self._tail_header = Static()
        self._popup = SuggestionsPopup()
        self._status = StatusBar(right=[('/ for commands, ctrl+d quits', 'status.dim')])
        self._input = TextArea(
            prompt='> ',
            prompt_style='input.glyph',
            max_height=8,
            on_submit=self._submit,
            ex_handler=self._ex,
        )

        self._history = InputHistory()
        self._messages: list[ChatMessage] = []

        self._pending_responses = list(CANNED_RESPONSES)
        self._stream_text: str | None = None
        self._stream_pos = 0

        self._card: Card | None = None
        self._tool_fired = False
        self._layout: StackLayout | None = None

        self._commands: ta.Mapping[str, tuple[str, ta.Callable[[str], None]]] = {
            '/help': ('list commands', self._cmd_help),
            '/show': ('/show <n>: re-commit message n from the registry', self._cmd_show),
            '/quit': ('exit the demo', self._cmd_quit),
        }

        driver.timers.call_every(.1, self._spin)
        driver.timers.call_every(.03, self._pump_stream)

        # Committing requires a prepared surface; the constructor runs before driver.run(), so the first response starts
        # from inside the loop.
        driver.timers.call_later(0., self._start_response)

    ##
    # Committing

    def _width(self) -> int:
        return max(self._driver.surface.width, 8)

    def _commit_rows(self, rows: ta.Sequence[ta.Sequence[Segment]]) -> None:
        self._driver.commit([line_from_segments(row, CHAT_THEME) for row in rows])

    def _commit_header(self, speaker: str, number: int) -> None:
        self._commit_rows([
            [Segment(speaker, f'speaker.{speaker}'), Segment(f'  [{number}]', 'speaker.num')],
        ])

    def _register(self, speaker: str, text: str) -> ChatMessage:
        msg = ChatMessage(len(self._messages) + 1, speaker, text)
        self._messages.append(msg)
        return msg

    ##
    # The fake stream

    def _spin(self) -> None:
        self._spinner.advance()
        self._refresh_status()
        self._driver.invalidate()

    _STREAM_CHUNK = 4  # chars per tick - token-ish

    def _start_response(self) -> None:
        if not self._pending_responses:
            self._pending_responses = list(CANNED_RESPONSES)
        text = self._pending_responses.pop(0)
        msg = self._register('ai', text)
        self._commit_header('ai', msg.number)
        self._stream_text = text
        self._stream_pos = 0
        self._tool_fired = False

    def _pump_stream(self) -> None:
        if self._stream_text is None or self._card is not None:
            return  # a warm tool card holds the stream

        if not self._tool_fired and self._stream_pos >= len(self._stream_text) // 2:
            self._tool_fired = True
            self._start_tool_use()
            self._driver.invalidate()
            return

        if self._stream_pos >= len(self._stream_text):
            blocks = self._tail.finalize()
            if blocks:
                self._commit_rows(self._tail.render_settled(blocks, self._width()))
            self._commit_rows([[]])
            self._stream_text = None
        else:
            chunk = self._stream_text[self._stream_pos: self._stream_pos + self._STREAM_CHUNK]
            self._stream_pos += self._STREAM_CHUNK
            self._tail.feed(chunk)
            if (settled := self._tail.pop_settled()):
                self._commit_rows(self._tail.render_settled(settled, self._width()))

        self._driver.invalidate()

    ##
    # The warm-window tool card: confirm -> run -> complete -> commit, all in the live region.

    def _start_tool_use(self) -> None:
        self._card = Card(
            [
                ('fake_search', 'card.summary'),
                ('(query="minitui")  awaiting confirmation', 'card.summary.dim'),
            ],
            state=CardState.CONFIRMING,
            detail=[
                [Segment('tool: fake_search', 'card.detail')],
                [Segment('args: {"query": "minitui", "limit": 3}', 'card.detail')],
            ],
            on_confirm=self._on_tool_confirm,
        )

    def _on_tool_confirm(self, allowed: bool) -> None:
        card = self._card
        if card is None:
            return
        if allowed:
            card.set_state(CardState.RUNNING)
            card.set_summary([
                ('fake_search', 'card.summary'),
                ('(query="minitui")  running...', 'card.summary.dim'),
            ])
            self._driver.timers.call_later(1.2, lambda: self._tool_complete(card))
        else:
            card.set_state(CardState.DENIED)
            card.set_summary([
                ('fake_search', 'card.summary'),
                ('  denied', 'card.summary.dim'),
            ])
            self._driver.timers.call_later(.8, lambda: self._finalize_card(card))
        self._driver.invalidate()

    def _tool_complete(self, card: Card) -> None:
        # Identity-guarded: a deferred timer must only touch the card it was scheduled for, never a successor that
        # took the slot in the meantime.
        if self._card is not card:
            return
        card.set_state(CardState.COMPLETE)
        card.set_summary([
            ('fake_search', 'card.summary'),
            ('(query="minitui")  3 results', 'card.summary.dim'),
        ])
        card.set_detail([
            [Segment('1. the commit model', 'card.detail')],
            [Segment('2. a vim engine in a chat input', 'card.detail')],
            [Segment('3. this card, which is about to become scrollback', 'card.detail')],
        ])
        self._driver.timers.call_later(1.0, lambda: self._finalize_card(card))
        self._driver.invalidate()

    def _finalize_card(self, card: Card) -> None:
        if self._card is not card:
            return
        self._card = None
        # Commit the card exactly as displayed (expanded state included) - warm window becomes scrollback.
        self._commit_rows([*card.render(self._width()), []])
        self._driver.invalidate()

    ##
    # Input

    def _submit(self, text: str) -> None:
        self._history.add(text)
        self._popup.clear()

        if text.startswith('/'):
            self._run_command(text)
            return

        msg = self._register('you', text)
        self._commit_header('you', msg.number)
        self._commit_rows([
            *self._tail.render_settled(parse_markdown(text), self._width()),
            [],
        ])

        if self._stream_text is None:
            self._start_response()

    def _ex(self, line: str) -> str | None:
        if line in ('q', 'q!', 'wq'):
            self._driver.stop()
            return None
        return f'Not an editor command: {line}'

    ##
    # Slash commands

    def _run_command(self, text: str) -> None:
        name, _, arg = text.partition(' ')
        if (entry := self._commands.get(name)) is not None:
            entry[1](arg.strip())
        else:
            self._commit_rows([[Segment(f'unknown command: {name}', 'error')], []])

    def _cmd_help(self, arg: str) -> None:
        self._commit_rows([
            *([Segment(name, 'md.code.inline'), Segment(f'  {desc}', 'status.dim')]
              for name, (desc, _) in self._commands.items()),
            [],
        ])

    def _cmd_show(self, arg: str) -> None:
        if not arg.isdigit() or not 1 <= int(arg) <= len(self._messages):
            self._commit_rows([[Segment(f'no such message: {arg!r}', 'error')], []])
            return
        msg = self._messages[int(arg) - 1]
        width = self._width()
        raw_rows: list[list[Segment]] = []
        for line in msg.text.split('\n'):
            # Hard-chunk: committed lines must never exceed the width (autowrap is off; overflow pins).
            for start in range(0, max(len(line), 1), width):
                raw_rows.append([Segment(line[start: start + width], 'md.code')] if line else [])
        self._commit_rows([
            [Segment(f'[{msg.number}] {msg.speaker} (raw source)', 'status.dim')],
            *raw_rows,
            [],
        ])

    def _cmd_quit(self, arg: str) -> None:
        self._driver.stop()

    ##
    # Suggestions & history

    def _update_popup(self) -> None:
        text = self._input.doc.text()
        if text.startswith('/') and '\n' not in text and ' ' not in text:
            self._popup.set_items(
                SuggestionItem(name, desc)
                for name, (desc, _) in self._commands.items()
                if name.startswith(text)
            )
        else:
            self._popup.clear()

    def _history_step(self, *, back: bool) -> None:
        current = self._input.doc.text()
        entry = self._history.previous(current) if back else self._history.next(current)
        if entry is not None:
            self._input.set_text(entry)

    def _handle_app_key(self, event: KeyEvent) -> bool:
        key = event.key

        if key == Key('d', ctrl=True):
            self._driver.stop()
            return True

        if self._card is not None:
            if key == Key('f10') and self._card.state is CardState.CONFIRMING:
                self._card.respond(True)
                return True
            if key == Key('f2') and self._card.state is CardState.CONFIRMING:
                self._card.respond(False)
                return True
            if key == Key('o', ctrl=True):
                self._card.toggle_expanded()
                return True

        if key == Key('tab') and self._popup.visible:
            if (item := self._popup.cycle()) is not None:
                self._input.set_text(item.label + (' ' if item.label == '/show' else ''))
            return True

        cursor = self._input.engine.cursor
        at_first_line = cursor.row == 0
        at_last_line = cursor.row == self._input.doc.line_count() - 1

        if key == Key('p', ctrl=True) or (key == Key('up') and at_first_line):
            self._history_step(back=True)
            return True
        if key == Key('n', ctrl=True) or (key == Key('down') and at_last_line):
            self._history_step(back=False)
            return True

        return False

    ##
    # Events & rendering

    def _refresh_status(self) -> None:
        st = self._input.engine.status()
        mode_part = st.cmdline if st.cmdline is not None else st.mode_text
        streaming = 'streaming' if self._stream_text is not None else 'idle'
        self._status.set_left([
            (self._spinner.frame if self._stream_text is not None else ' ', 'status.spinner'),
            (f' {streaming}  ', 'status.dim'),
            (mode_part or '', 'status.mode'),
            (f'  {st.pending}' if st.pending else '', 'status.dim'),
            (f'  {st.message}' if st.message else '', 'status.dim'),
        ])

    def _handle_mouse(self, event: MouseEvent) -> None:
        if self._layout is None or (hit := self._layout.hit(event.y)) is None:
            return
        control, local_y = hit
        local = dc.replace(event, y=local_y)
        if control is self._popup:
            if (item := self._popup.item_at(local_y)) is not None:
                self._input.set_text(item.label + (' ' if item.label == '/show' else ''))
            return
        control.handle_event(local)

    def handle_event(self, event: Event) -> None:
        if isinstance(event, MouseEvent):
            self._handle_mouse(event)
        elif not (isinstance(event, KeyEvent) and self._handle_app_key(event)):
            self._input.handle_event(event)

        self._update_popup()
        self._refresh_status()
        self._driver.invalidate()

    def render(self, width: int, max_height: int) -> Frame:
        controls = [
            self._tail,
            *([self._card] if self._card is not None else []),
            self._popup,
            self._input,
            self._status,
        ]
        self._layout = stack_layout(
            controls,
            width=width,
            max_height=max_height,
            theme=CHAT_THEME,
            focus=self._input,
        )
        return self._layout.frame


def _main() -> None:
    import sys  # noqa: PLC0415

    md_backend: str | None = None
    for arg in sys.argv[1:]:
        if arg.startswith('--md='):
            md_backend = arg.partition('=')[2]

    driver = SyncDriver(InlineSurface(
        kitty_keys=True,
        # Opt-in: terminals route the wheel to us too once tracking is on, trading away native scrollback wheeling.
        mouse='--mouse' in sys.argv[1:],
    ))
    app = ChatDemoApp(driver, md_backend=md_backend)
    try:
        driver.run(app)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
