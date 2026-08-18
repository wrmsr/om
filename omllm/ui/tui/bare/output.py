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
from ..agent import bind_on_agent_event_subscriber
from ..config import Config


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


##


def bind_output(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.extend([
        inj.bind(build_rich_text_displayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=ui.RichTextDisplayer),
    ])

    if config.verbose:
        lst.extend([
            inj.bind(VerbosePrinter, singleton=True),
            bind_on_agent_event_subscriber(VerbosePrinter),
        ])

    if config.stream:
        lst.extend([
            inj.bind(StreamResponsePrinter, singleton=True),
            bind_on_agent_event_subscriber(StreamResponsePrinter),
        ])

    else:
        lst.extend([
            inj.bind(ImmediateResponsePrinter, singleton=True),
            bind_on_agent_event_subscriber(ImmediateResponsePrinter),
        ])

    return inj.as_elements(*lst)
