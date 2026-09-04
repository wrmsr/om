import abc
import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from .... import llm
from ....core import ui
from ..config import Config
from ..inject import bind_on_agent_event_subscriber
from ..rendering import TerminalTextDisplayer
from ..rendering import build_terminal_text_displayer


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
        inj.bind(build_terminal_text_displayer, singleton=True),
        inj.bind(ui.TextDisplayer, to_key=TerminalTextDisplayer),

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
