"""
Output side of the minitui backend: the `ui.TextDisplayer` that renders the shared `Text` node family through the
minitui commit model, and the agent-event subscriber that drives streaming markdown and tool cards.

Agent callbacks run on the driver's asyncio loop. Tool-event handling mutates control state synchronously and
invalidates; concurrent tool tasks may interleave events, but never individual card updates.
"""
import json
import typing as ta

from omcore import inject as inj
from omcore.text import styled as st
from omdev.tui import minitui as mt

from .... import agent as agn
from .... import llm
from ....core import ui
from ..config import Config
from ..inject import bind_on_agent_event_subscriber
from .app import MinituiChatApp
from .toolcards import tool_card_key


##


# The shared Text family's deliberately-dumb color channel, mapped onto the theme's soft palette.
_TEXT_COLOR_STYLES: ta.Mapping[str, st.StylePatch] = {
    'red': st.StylePatch(fg=mt.TEXT_ERROR),
    'green': st.StylePatch(fg=mt.SUCCESS),
    'yellow': st.StylePatch(fg=mt.WARNING),
    'blue': st.StylePatch(fg=mt.TEXT_PRIMARY),
}


def _text_style(y: ui.TextStyle) -> st.StylePatch:
    base = _TEXT_COLOR_STYLES.get(y.color or '', st.StylePatch())
    if y.bold or y.italic:
        base = base.overlay(st.StylePatch(
            bold=True if y.bold else None,
            italic=True if y.italic else None,
        ))
    return base


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 3] + '...'


# The end reasons which close a turn normally but deserve a word: the model did not finish of its own accord.
_END_REASON_NOTES: ta.Mapping[agn.AgentEndReason, str] = {
    agn.AgentEndReason.LENGTH: 'output cut off by the token limit',
    agn.AgentEndReason.MAX_TURNS: 'turn limit reached',
}


def _detail_rows(text: str, *, limit_lines: int = 8) -> list[list[mt.Segment]]:
    """Card-detail rows from possibly-multiline text: newline-split (segments are single-line), line-capped."""

    rows = mt.split_segment_lines([(_truncate(text, 2000), 'card.detail')])
    if len(rows) > limit_lines:
        rows = [*rows[:limit_lines], [mt.Segment(f'... (+{len(rows) - limit_lines} more lines)', 'card.summary.dim')]]
    return rows


def _inline_parts(t: ui.Text, style: mt.Style) -> ta.Iterator[tuple[str, mt.StyleLike]]:
    # Yields (text, style) runs - text may contain newlines; `mt.split_segment_lines` rows them up.
    if isinstance(t, ui.StrText):
        yield t.s, (style if not style.is_plain else None)

    elif isinstance(t, ui.ConcatText):
        for c in t.l:
            yield from _inline_parts(c, style)

    elif isinstance(t, ui.StyleText):
        yield from _inline_parts(t.c, style.apply(_text_style(t.y)))

    elif isinstance(t, ui.JsonText):
        indent = None if t.y.mode == 'compact' else 2
        yield json.dumps(t.v, indent=indent, default=repr), 'md.code.inline'

    else:
        yield str(t), (style if not style.is_plain else None)


class MinituiTextDisplayer(ui.TextDisplayer):
    def __init__(self, *, app: MinituiChatApp) -> None:
        super().__init__()

        self._app = app

    def _display_one(self, t: ui.Text) -> None:
        if isinstance(t, ui.MarkdownText):
            self._app.display_markdown(t.s)

        elif isinstance(t, ui.DiffText):
            self._app.display_rows(mt.render_markdown_block(
                mt.MdCode('diff', tuple(ln.rstrip('\n') for ln in t.diff_lines)),
                self._app.width,
                highlighter=mt.highlight_code,
            ))

        else:
            # Inline nodes - possibly multi-line; rows wrap individually and commit as one block.
            rows: list[ta.Sequence[mt.Segment]] = []
            for row in mt.split_segment_lines(_inline_parts(t, mt.EMPTY_STYLE)):
                rows.extend(mt.wrap_segments(row, self._app.width) if row else [[]])
            self._app.display_rows(rows)

    async def display_text(self, *texts: ui.CanText) -> None:
        for t in texts:
            self._display_one(ui.Text.of(t))


##


class AgentEventRenderer:
    """Drives the chat surface from the agent's event stream."""

    def __init__(
            self,
            *,
            app: MinituiChatApp,
            text_displayer: ui.TextDisplayer,
            config: Config,
    ) -> None:
        super().__init__()

        self._app = app
        self._text_displayer = text_displayer
        self._config = config

        # Output a running tool has reported so far, by card, shown live in its detail.
        self._tool_output: dict[str, str] = {}

    def _on_stream_event(self, lev: llm.AiStreamEvent) -> None:
        app = self._app

        if isinstance(lev, llm.TextDeltaAiStreamEvent):
            app.stream_feed(lev.text)

        elif isinstance(lev, llm.TextEndAiStreamEvent):
            app.stream_break()

        elif isinstance(lev, llm.ThinkingStartAiStreamEvent):
            app.set_thinking(True)

        elif isinstance(lev, llm.ThinkingEndAiStreamEvent):
            app.set_thinking(False)

    def _tool_title(self, ev: agn.ToolExecutionEvent) -> str:
        return ev.tool_name

    def _tool_detail(self, context: agn.ToolContext) -> list[list[mt.Segment]]:
        args = json.dumps(dict(context.args), default=repr)
        return [[mt.Segment(f'args: {_truncate(args, 200)}', 'card.detail')]]

    def _result_rows(self, result: agn.ToolResult) -> list[list[mt.Segment]]:
        if result.error is not None:
            return _detail_rows(repr(result.error))

        # Details are the structured story where a tool tells one; the model-facing text otherwise.
        if isinstance(d := result.details, agn.ExecToolResultDetails):
            notes = [f'exit code {d.rc}']
            if d.timed_out:
                notes.append('timed out')
            return [
                [mt.Segment('; '.join(notes), 'card.summary.dim')],
                *_detail_rows(d.stdout + d.stderr),
            ]

        return _detail_rows(result.content.text)

    async def on_agent_event(self, ev: agn.Event) -> None:
        app = self._app

        if isinstance(ev, agn.AgentStartEvent):
            app.begin_ai_turn()

        elif isinstance(ev, agn.AgentEndEvent):
            self._tool_output.clear()

            if ev.reason is agn.AgentEndReason.COMPLETED:
                app.end_ai_turn()

            elif (note := _END_REASON_NOTES.get(ev.reason)) is not None:
                # The run stopped short but nothing went wrong: the turn closes normally, with a note saying why.
                app.end_ai_turn()
                app.display_text(note, 'status.dim')

            else:
                app.abort_ai_turn(cancelled=ev.reason is agn.AgentEndReason.CANCELLED)
                if ev.reason is agn.AgentEndReason.FAILED:
                    app.display_text(f'error: {ev.error!r}', 'error')

        elif not app.is_busy:
            # A straggler from a turn that already ended - a detached tool finishing after its turn aborted, a delta
            # racing the end event. It must not reopen the tail or resurrect a finalized card.
            return

        elif isinstance(ev, agn.LlmAiStreamEvent):
            if not self._config.immediate:
                self._on_stream_event(ev.event)

        elif isinstance(ev, agn.LlmRetryEvent):
            app.display_text(f'retrying in {ev.delay_s:.0f}s: {ev.error!r}', 'status.dim')

        elif isinstance(ev, agn.TurnEndEvent):
            if self._config.immediate and isinstance(msg := ev.message, llm.AiMessage):
                for c in msg.content:
                    if isinstance(c, llm.TextContent) and (s := c.text.strip()):
                        await self._text_displayer.display_text(ui.MarkdownText(s))

        elif isinstance(ev, agn.ToolExecutionStartEvent):
            app.tool_started(tool_card_key(ev.context), self._tool_title(ev), self._tool_detail(ev.context))

        elif isinstance(ev, agn.ToolExecutionUpdateEvent):
            if isinstance(upd := ev.update, agn.OutputToolProgressUpdate):
                key = tool_card_key(ev.context)
                text = self._tool_output[key] = self._tool_output.get(key, '') + upd.text
                app.tool_updated(key, [
                    *self._tool_detail(ev.context),
                    *_detail_rows(text[-2000:]),
                ])

        elif isinstance(ev, agn.ToolExecutionEndEvent):
            key = tool_card_key(ev.context)
            self._tool_output.pop(key, None)
            app.tool_finished(
                key,
                self._tool_title(ev),
                ok=ev.result.error is None,
                detail_rows=[
                    *self._tool_detail(ev.context),
                    *self._result_rows(ev.result),
                ],
            )


class VerboseEventRenderer:
    def __init__(self, *, app: MinituiChatApp) -> None:
        super().__init__()

        self._app = app

    async def on_agent_event(self, ev: agn.Event) -> None:
        self._app.display_text(_truncate(repr(ev), 200), 'status.dim')


##


def bind_output(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(MinituiTextDisplayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=MinituiTextDisplayer),

        inj.bind(AgentEventRenderer, singleton=True),
        bind_on_agent_event_subscriber(AgentEventRenderer),
    ]

    if config.verbose:
        lst.extend([
            inj.bind(VerboseEventRenderer, singleton=True),
            bind_on_agent_event_subscriber(VerboseEventRenderer),
        ])

    return inj.as_elements(*lst)
