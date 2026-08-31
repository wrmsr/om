"""
Output side of the minitui backend: the `ui.TextDisplayer` that renders the shared `Text` node family through the
minitui commit model, and the agent-event subscriber that drives streaming markdown and tool cards.

Event handlers are awaited serially inside the agent's turn - everything here mutates control state and invalidates,
never blocks.
"""
import json
import typing as ta

from omcore import inject as inj
from omdev.tui import minitui as mt

from .... import agent as agn
from .... import llm
from ....core import ui
from ..config import Config
from ..inject import bind_on_agent_event_subscriber
from .app import MinituiChatApp


##


# The shared Text family's deliberately-dumb color channel, mapped onto the theme's soft palette.
_TEXT_COLOR_STYLES: ta.Mapping[str, mt.Style] = {
    'red': mt.Style(fg=mt.TEXT_ERROR),
    'green': mt.Style(fg=mt.SUCCESS),
    'yellow': mt.Style(fg=mt.WARNING),
    'blue': mt.Style(fg=mt.TEXT_PRIMARY),
}


def _text_style(y: ui.TextStyle) -> mt.Style:
    base = _TEXT_COLOR_STYLES.get(y.color or '', mt.EMPTY_STYLE)
    if y.bold or y.italic:
        base = base.overlay(mt.Style(bold=bool(y.bold), italic=bool(y.italic)))
    return base


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 3] + '...'


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
        yield from _inline_parts(t.c, style.overlay(_text_style(t.y)))

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

    def _tool_title(self, tool: agn.Tool) -> str:
        return tool.name

    def _tool_detail(self, context: agn.ToolContext) -> list[list[mt.Segment]]:
        args = json.dumps(dict(context.args), default=repr)
        return [[mt.Segment(f'args: {_truncate(args, 200)}', 'card.detail')]]

    async def on_agent_event(self, ev: agn.Event) -> None:
        app = self._app

        if isinstance(ev, agn.AgentStartEvent):
            app.begin_ai_turn()

        elif isinstance(ev, agn.AgentEndEvent):
            app.end_ai_turn()

        elif isinstance(ev, agn.LlmAiStreamEvent):
            if not self._config.immediate:
                self._on_stream_event(ev.event)

        elif isinstance(ev, agn.TurnEndEvent):
            if self._config.immediate and isinstance(msg := ev.message, llm.AiMessage):
                for c in msg.content:
                    if isinstance(c, llm.TextContent) and (s := c.text.strip()):
                        await self._text_displayer.display_text(ui.MarkdownText(s))

        elif isinstance(ev, agn.ToolExecutionStartEvent):
            app.tool_started(self._tool_title(ev.tool), self._tool_detail(ev.context))

        elif isinstance(ev, agn.ToolExecutionEndEvent):
            result_text = ev.result.content.text if ev.result.error is None else repr(ev.result.error)
            app.tool_finished(
                self._tool_title(ev.tool),
                ok=ev.result.error is None,
                detail_rows=[
                    *self._tool_detail(ev.context),
                    *_detail_rows(result_text),
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
