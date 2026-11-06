"""
The agent's events, translated into feed events. Nothing here knows of the browser, or of whether anyone is watching.
"""
import typing as ta

from omcore import dataclasses as dc

from .... import agent as agn
from .... import llm
from ...config import UiConfig
from ..feed import events as fe
from ..feed.feed import Feed
from ..texts import WebTextRenderer
from ..tools import tool_call_args
from ..tools import tool_call_summary
from ..tools import tool_card_key


##


def _error_str(e: BaseException | None) -> str | None:
    return repr(e) if e is not None else None


def clip_text(s: str, n: int) -> str:
    """The text, or if it is longer than n, its head and tail with a note of what was left out between them."""

    if len(s) <= n:
        return s

    return f'{s[:n // 2]}\n... ({len(s) - n:,} characters not shown) ...\n{s[-(n // 2):]}'


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class AgentEventFeederLimits:
    """
    Everything fed is kept for the life of the session, and sent to every page which loads: a tool's result is clipped
    to `max_result_chars`, the output a running tool reports stops being fed past `max_output_chars`, and long strings
    in its arguments are cut to `max_arg_chars`.
    """

    max_result_chars: int = 64 * 1024
    max_output_chars: int = 256 * 1024

    # Each string in a call's arguments - the contents of a file being written, say.
    max_arg_chars: int = 16 * 1024


class AgentEventFeeder:
    """Translates the agent's event stream into feed events."""

    # The end reasons which close a run normally but deserve a word: the model did not finish of its own accord.
    _END_REASON_NOTES: ta.ClassVar[ta.Mapping[agn.AgentEndReason, str]] = {
        agn.AgentEndReason.LENGTH: 'output cut off by the token limit',
        agn.AgentEndReason.CONTEXT_LENGTH: 'model stopped at the context-window limit',
        agn.AgentEndReason.MAX_TURNS: 'turn limit reached',
    }

    def __init__(
            self,
            *,
            feed: Feed,
            renderer: WebTextRenderer,
            config: UiConfig,
            limits: AgentEventFeederLimits | None = None,
    ) -> None:
        super().__init__()

        self._feed = feed
        self._renderer = renderer
        self._config = config

        limits = limits if limits is not None else AgentEventFeederLimits()
        self._max_result_chars = limits.max_result_chars
        self._max_output_chars = limits.max_output_chars
        self._max_arg_chars = limits.max_arg_chars

        self._running = False

        # How much output each running call has fed so far, by card.
        self._output_chars: dict[str, int] = {}

    #

    def _on_stream_event(self, lev: llm.AiStreamEvent) -> None:
        if isinstance(lev, llm.TextDeltaAiStreamEvent):
            if lev.text:
                self._feed.append(fe.AiTextDeltaFeedEvent(text=lev.text))

        elif isinstance(lev, llm.TextEndAiStreamEvent):
            self._feed.append(fe.AiTextEndFeedEvent(text=lev.text))

        elif isinstance(lev, llm.ThinkingStartAiStreamEvent):
            self._feed.append(fe.ThinkingStartFeedEvent())

        elif isinstance(lev, llm.ThinkingDeltaAiStreamEvent):
            if lev.text:
                self._feed.append(fe.ThinkingDeltaFeedEvent(text=lev.text))

        elif isinstance(lev, llm.ThinkingEndAiStreamEvent):
            self._feed.append(fe.ThinkingEndFeedEvent(text=lev.text))

    def _on_turn_end(self, ev: agn.TurnEndEvent) -> None:
        if not isinstance(msg := ev.message, llm.AiMessage):
            return

        if (usage := ev.usage) is not None:
            self._feed.append(fe.UsageFeedEvent(
                input=usage.uncached_input,
                input_cached=usage.cache_read,
                input_cache_write=usage.cache_write,
                output=usage.visible_output,
                reasoning=usage.reasoning,
            ))

        if (budget := ev.context_budget) is not None and budget.input is not None:
            self._feed.append(fe.ContextFeedEvent(
                input=budget.input,
                limit=budget.input_limit,
                estimated=budget.is_estimated,
            ))

        # Unstreamed, the model's text arrives only now, whole.
        if self._config.immediate:
            for c in msg.content:
                if isinstance(c, llm.TextContent) and c.text.strip():
                    self._feed.append(fe.AiTextFeedEvent(text=c.text))

    def _on_run_end(self, ev: agn.AgentEndEvent) -> None:
        self._feed.append(fe.RunEndFeedEvent(
            reason=ev.reason.name.lower(),
            error=_error_str(ev.error),
        ))

        if (note := self._END_REASON_NOTES.get(ev.reason)) is not None:
            self._feed.append(fe.NoticeFeedEvent(text=note, level='warn'))

        elif ev.reason is agn.AgentEndReason.FAILED:
            self._feed.append(fe.NoticeFeedEvent(text=f'error: {ev.error!r}', level='error'))

    #

    def _result_fields(self, result: agn.ToolResult) -> dict[str, ta.Any]:
        # A subagent's result is its final word, under the facts of its run - a failure's text says what failed.
        if isinstance(d := result.details, agn.SubagentToolResultDetails):
            notes = [
                f'run {d.run_id.v}',
                f'profile {d.profile}',
                f'{d.num_turns} turns',
                d.reason.name.lower(),
            ]
            if (usage := d.usage) is not None:
                notes.append(f'tokens in {usage.input:,} out {usage.output:,}')

            return dict(
                note='; '.join(notes),
                result=clip_text(result.content.text, self._max_result_chars),
            )

        if result.error is not None:
            return dict(result=clip_text(repr(result.error), self._max_result_chars))

        # What the tool has to show the user, where it has something - shown without asking.
        if display := result.display:
            return dict(
                result=self._renderer.render(display),
                show=True,
            )

        # Details are the structured story where a tool tells one; the model-facing text otherwise.
        if isinstance(d := result.details, agn.ExecToolResultDetails):
            notes = [f'exit code {d.rc}']
            if d.timed_out:
                notes.append('timed out')

            return dict(
                note='; '.join(notes),
                result=clip_text(d.stdout + d.stderr, self._max_result_chars),
            )

        return dict(result=clip_text(result.content.text, self._max_result_chars))

    def _on_tool_output(self, key: str, upd: agn.OutputToolProgressUpdate) -> None:
        if not upd.text or (fed := self._output_chars.get(key, 0)) > self._max_output_chars:
            return

        text = upd.text
        if (fed := fed + len(text)) > self._max_output_chars:
            text = text[:max(self._max_output_chars - (fed - len(text)), 0)] + '\n... (further output not shown) ...\n'

        self._output_chars[key] = fed

        self._feed.append(fe.ToolOutputFeedEvent(
            key=key,
            text=text,
            stream=upd.stream,
        ))

    def _on_tool_execution_event(
            self,
            ev: agn.ToolExecutionEvent,
            *,
            parent: str | None = None,
            via: str | None = None,
    ) -> None:
        """
        One tool call's card, from start to finish. A subagent's tool calls get cards of their own, beneath the card of
        the call which spawned it: the events reach here wrapped as progress of the spawning call, and are unwrapped.
        """

        key = tool_card_key(ev.context)

        if isinstance(ev, agn.ToolExecutionStartEvent):
            self._feed.append(fe.ToolStartFeedEvent(
                key=key,
                name=ev.tool_name,
                summary=tool_call_summary(ev.context, self._renderer),
                args=tool_call_args(ev.context, max_str_chars=self._max_arg_chars),
                parent=parent,
                via=via,
            ))

        elif isinstance(ev, agn.ToolExecutionUpdateEvent):
            if isinstance(upd := ev.update, agn.OutputToolProgressUpdate):
                self._on_tool_output(key, upd)

            elif isinstance(upd, agn.SubagentEventToolProgressUpdate):
                # Of all a subagent does, its tool calls are what is shown live. Its model calls and messages are not:
                # its final word comes back as the spawning call's result.
                if isinstance(sub_ev := upd.event, agn.ToolExecutionEvent):
                    self._on_tool_execution_event(
                        sub_ev,
                        parent=key,
                        via=f'{upd.profile} {upd.run_id.v}',
                    )

        elif isinstance(ev, agn.ToolExecutionEndEvent):
            self._output_chars.pop(key, None)

            result = ev.result
            self._feed.append(fe.ToolEndFeedEvent(
                key=key,
                ok=result.error is None,
                **self._result_fields(result),
            ))

    #

    async def on_agent_event(self, ev: agn.Event) -> None:
        if isinstance(ev, agn.AgentStartEvent):
            self._running = True
            self._feed.append(fe.RunStartFeedEvent())

        elif isinstance(ev, agn.AgentEndEvent):
            self._running = False
            self._on_run_end(ev)

        elif isinstance(ev, agn.LlmAiStreamEvent):
            # A delta racing the end event must not open a new block of text after the run is over.
            if self._running and not self._config.immediate:
                self._on_stream_event(ev.event)

        elif isinstance(ev, agn.LlmRetryEvent):
            self._feed.append(fe.NoticeFeedEvent(
                text=f'retrying in {ev.delay_s:.0f}s: {ev.error!r}',
                level='warn',
            ))

        elif isinstance(ev, agn.ContextWindowEvent):
            if (budget_input := ev.context_budget.input) is not None:
                self._feed.append(fe.ContextFeedEvent(
                    input=budget_input,
                    limit=ev.context_budget.input_limit,
                    estimated=ev.context_budget.is_estimated,
                ))

        elif isinstance(ev, agn.ContextReductionEvent):
            reduction = ev.reduction
            self._feed.append(fe.NoticeFeedEvent(text=(
                f'context {reduction.reason.replace("_", " ")}: '
                f'{reduction.before_tokens:,} -> {reduction.after_tokens:,} tokens'
            )))

        elif isinstance(ev, agn.TurnEndEvent):
            self._on_turn_end(ev)

        elif isinstance(ev, agn.ToolExecutionEvent):
            self._on_tool_execution_event(ev)


class VerboseAgentEventFeeder:
    """Every agent event, as a debug notice."""

    def __init__(self, *, feed: Feed) -> None:
        super().__init__()

        self._feed = feed

    async def on_agent_event(self, ev: agn.Event) -> None:
        r = repr(ev)
        if len(r) > 500:
            r = r[:497] + '...'

        self._feed.append(fe.NoticeFeedEvent(text=r, level='debug'))
