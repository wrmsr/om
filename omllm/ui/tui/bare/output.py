import abc
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
from omcore import lang
from omdev.tui import rich
from omdev.tui.rich import textual as rich_tx

from .... import agent as agn
from .... import llm
from ....core import ui
from ..config import Config
from ..inject import bind_on_agent_event_subscriber


##


@dc.dataclass(frozen=True, kw_only=True)
class RichUiStyles:
    theme: ta.Any
    code_theme: ta.Any
    json_styles: ui.RichJsonStyles


@lang.cached_function
def rich_ui_styles() -> RichUiStyles:
    dtx = rich_tx.TEXTUAL_DARK

    ps = check.not_none(dtx.pygments_styles)

    return RichUiStyles(
        theme=rich_tx.build_theme(dtx),
        code_theme=rich_tx.build_pygments_theme(dtx),
        json_styles=ui.RichJsonStyles(
            # Match the theme's code-block highlighting of json source.
            key=ps['Token.Name.Tag'],
            string=ps['Token.Literal.String.Double'],
            number=ps['Token.Literal.Number'],
            literal=ps['Token.Keyword.Constant'],
        ),
    )


def build_rich_text_displayer() -> ui.RichTextDisplayer:
    rs = rich_ui_styles()

    return ui.RichTextDisplayer(
        console=rich.Console(theme=rs.theme),
        renderer=ui.RichTextRenderer(
            markdown_code_theme=rs.code_theme,
            json_styles=rs.json_styles,
        ),
    )


##


class AgentEventDisplayer(lang.Abstract):
    def __init__(self, text_displayer: ui.TextDisplayer) -> None:
        super().__init__()

        self._text_displayer = text_displayer

    @abc.abstractmethod
    def on_agent_event(self, ev: agn.Event) -> ta.Awaitable[None]:
        raise NotImplementedError


class VerbosePrinter(AgentEventDisplayer):
    async def on_agent_event(self, ev: agn.Event) -> None:
        print(ev)


class ImmediateResponsePrinter(AgentEventDisplayer):
    async def on_agent_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.TurnEndEvent):
            if isinstance(msg := ev.message, llm.AiMessage):
                for c in msg.content:
                    if isinstance(c, llm.TextContent):
                        if (s := c.text.strip()):
                            await self._text_displayer.display_text(ui.MarkdownText(s))


class StreamResponsePrinter(AgentEventDisplayer):
    async def on_agent_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.LlmAiStreamEvent):
            lev = ev.event

            if isinstance(lev, llm.TextDeltaAiStreamEvent):
                await self._text_displayer.display_text(lev.text)

            elif isinstance(lev, llm.TextEndAiStreamEvent):
                await self._text_displayer.display_text('\n')


class EndReasonPrinter(AgentEventDisplayer):
    """Says how a run ended whenever it was not the model ending its own turn: a failure comes back as a result now."""

    _NOTES: ta.ClassVar[ta.Mapping[agn.AgentEndReason, str]] = {
        agn.AgentEndReason.LENGTH: '(output cut off by the token limit)',
        agn.AgentEndReason.MAX_TURNS: '(turn limit reached)',
        agn.AgentEndReason.CANCELLED: '(cancelled)',
    }

    async def on_agent_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.LlmRetryEvent):
            await self._text_displayer.display_text(f'(retrying in {ev.delay_s:.0f}s: {ev.error!r})\n')

        elif isinstance(ev, agn.AgentEndEvent):
            if ev.reason is agn.AgentEndReason.FAILED:
                await self._text_displayer.display_text(f'error: {ev.error!r}\n')

            elif (note := self._NOTES.get(ev.reason)) is not None:
                await self._text_displayer.display_text(note + '\n')


##


def bind_output(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(build_rich_text_displayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=ui.RichTextDisplayer),

        inj.bind(EndReasonPrinter, singleton=True),
        bind_on_agent_event_subscriber(EndReasonPrinter),
    ])

    if config.verbose:
        lst.extend([
            inj.bind(VerbosePrinter, singleton=True),
            bind_on_agent_event_subscriber(VerbosePrinter),
        ])

    if config.immediate:
        lst.extend([
            inj.bind(ImmediateResponsePrinter, singleton=True),
            bind_on_agent_event_subscriber(ImmediateResponsePrinter),
        ])

    else:
        lst.extend([
            inj.bind(StreamResponsePrinter, singleton=True),
            bind_on_agent_event_subscriber(StreamResponsePrinter),
        ])

    return inj.as_elements(*lst)
