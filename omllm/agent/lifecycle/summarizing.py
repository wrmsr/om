"""
TODO:
 - a summarizer model of its own, cheaper than the run's
 - retry a transient summarizer failure rather than let it fail the run
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ... import llm
from ..projection.builders import StandardLlmContextBuilder
from ..projection.types import LlmContextBuilder
from ..types.contexts import Context
from ..types.lifecycle import ContextProjection
from ..types.lifecycle import ContextReductionReason
from ..types.lifecycle import ToolResultProjection
from .compactors import ContextCompactor
from .estimators import CharacterContextTokenEstimator
from .estimators import ContextTokenEstimator
from .transcripts import render_transcript_messages


##


DEFAULT_SUMMARY_SYSTEM_PROMPT: ta.Final[str] = (
    'You are summarizing the earlier part of a conversation between a user and an agent working for them. The agent '
    'will carry on with that part of the conversation replaced by your summary, so the summary has to carry '
    'everything the agent still needs from it.\n'
    '\n'
    'Cover, under these headings:\n'
    '\n'
    '- Goal: what the user asked for, with any constraints and preferences they stated.\n'
    '- Progress: what has been done, what worked, and what did not.\n'
    '- Facts: decisions taken, things learned, and the exact names, paths, identifiers, commands, and values which '
    'would otherwise have to be rediscovered.\n'
    '- Remaining: what is still to be done, and whatever was in progress at the end.\n'
    '\n'
    'Be specific, and keep exact wording where it matters. Do not add commentary, and do not address the user. Reply '
    'with the summary alone.'
)


class SummarizingContextCompactor(ContextCompactor):
    """
    Replaces the older part of the transcript with a summary of it, asked of a model, keeping the newest part verbatim
    behind it. What the model is given to summarize is a plain-text rendering of the model view of that older part -
    tool results as bounded or pruned, agent messages as projected - along with any summary already standing, so
    repeated compactions fold into one summary rather than stacking. The cut between the two parts never falls between
    a tool call and its results.
    """

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        # About how much of the newest transcript is kept verbatim. A target it would not fit in cuts it shorter.
        keep_recent_tokens: int = 20_000

        # The most the summary may run to: asked of the model, and allowed for in deciding what is kept.
        max_summary_tokens: int = 4_000

        # Kept back from the summarizer's own input budget when fitting the material to it.
        safety_margin_tokens: int = 1_024

        # A tool call's arguments are rendered for the summarizer up to this many characters. None renders them whole.
        max_tool_call_chars: int | None = 1_000

        # Options for the summarizing call, over the summary length.
        options: llm.Options | None = None

        system_prompt: str | None = None

        def __post_init__(self) -> None:
            check.arg(self.keep_recent_tokens >= 0)
            check.arg(self.max_summary_tokens > 0)
            check.arg(self.safety_margin_tokens >= 0)
            check.arg(self.max_tool_call_chars is None or self.max_tool_call_chars > 0)

    def __init__(
            self,
            *,
            config: Config | None = None,
            estimator: ContextTokenEstimator | None = None,
            context_builder: LlmContextBuilder | None = None,
    ) -> None:
        super().__init__()

        self._config = config if config is not None else self.Config()
        self._estimator = estimator if estimator is not None else CharacterContextTokenEstimator()
        self._builder = context_builder if context_builder is not None else StandardLlmContextBuilder()

    #

    def _message_tokens(self, context: Context, index: int, *, base_tokens: int) -> int:
        """What one message costs as the model would see it under the context's projection."""

        message = check.not_none(context.messages)[index]

        tool_results: tuple[ToolResultProjection, ...] = ()
        if (projection := context.projection) is not None:
            if (p := projection.tool_results_by_message_index.get(index)) is not None:
                tool_results = (dc.replace(p, message_index=0),)

        view = self._builder.build(Context(
            messages=[message],
            projection=ContextProjection(tool_results=tool_results),
        ))

        return max(self._estimator.estimate_context(view) - base_tokens, 0)

    def _choose_cut(self, context: Context, *, start: int, tail_limit: int) -> int:
        """
        Where the kept tail starts: the earliest boundary at which the tail still fits the limit. A boundary is anywhere
        but ahead of a tool result. The newest group is kept whatever its size, there being nothing to summarize it
        into.
        """

        messages = context.messages or ()

        boundaries = [
            i
            for i in range(start, len(messages))
            if not isinstance(messages[i], llm.ToolResultMessage)
        ]
        if not boundaries:
            return start

        base_tokens = self._estimator.estimate_context(self._builder.build(Context()))

        def group_tokens(begin: int, end: int) -> int:
            return sum(self._message_tokens(context, i, base_tokens=base_tokens) for i in range(begin, end))

        cut = boundaries[-1]
        tokens = group_tokens(cut, len(messages))
        for boundary in reversed(boundaries[:-1]):
            tokens += group_tokens(boundary, cut)
            if tokens > tail_limit:
                break
            cut = boundary

        return cut

    def _material(self, context: Context, *, start: int, cut: int) -> list[str]:
        """The model view of what is to be summarized, rendered as text: one block per message the view shows."""

        messages = check.not_none(context.messages)[start:cut]

        tool_results: list[ToolResultProjection] = []
        if (projection := context.projection) is not None:
            tool_results.extend(
                dc.replace(p, message_index=p.message_index - start)
                for p in projection.tool_results
                if start <= p.message_index < cut
            )

        view = self._builder.build(Context(
            messages=messages,
            projection=ContextProjection(tool_results=tuple(tool_results)),
        ))

        return render_transcript_messages(
            view.messages or (),
            max_tool_call_chars=self._config.max_tool_call_chars,
        )

    #

    def _request(
            self,
            blocks: ta.Sequence[str],
            *,
            omitted: int,
            previous_summary: str | None,
            instructions: str | None,
    ) -> llm.Context:
        parts: list[str] = []

        if previous_summary is not None:
            parts.append(
                'The conversation before this transcript was summarized earlier as follows. Carry forward whatever of '
                'it still matters.\n'
                '\n'
                f'{previous_summary}',
            )

        transcript = '\n\n'.join(blocks)
        if omitted:
            noun = 'message' if omitted == 1 else 'messages'
            transcript = f'[{omitted} earlier {noun} omitted]\n\n{transcript}'
        parts.append(f'<transcript>\n{transcript}\n</transcript>')

        if instructions is not None:
            parts.append(f'Additional instructions for this summary:\n\n{instructions}')

        system_prompt = self._config.system_prompt
        if system_prompt is None:
            system_prompt = DEFAULT_SUMMARY_SYSTEM_PROMPT

        return llm.Context(
            system_prompt=system_prompt,
            messages=[llm.UserMessage('\n\n'.join(parts))],
        )

    def _fit(
            self,
            blocks: ta.Sequence[str],
            *,
            budget_tokens: int | None,
            previous_summary: str | None,
            instructions: str | None,
    ) -> llm.Context:
        """
        The request, with as many of the oldest blocks left out as it takes to fit the budget - all but the newest, at
        most.
        """

        def request(omitted: int) -> llm.Context:
            return self._request(
                blocks[omitted:],
                omitted=omitted,
                previous_summary=previous_summary,
                instructions=instructions,
            )

        if budget_tokens is None:
            return request(0)

        def fits(omitted: int) -> bool:
            return self._estimator.estimate_context(request(omitted)) <= budget_tokens

        if fits(0):
            return request(0)

        # Leaving more out never makes it bigger, so the least that fits is found by bisection. If nothing does, the
        # newest block alone is sent anyway, and the backend has the last word.
        lo, hi = 1, len(blocks) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if fits(mid):
                hi = mid
            else:
                lo = mid + 1

        return request(lo)

    #

    async def compact(
            self,
            context: Context,
            *,
            backend: llm.ImmediateBackend,
            target_tokens: int,
            reason: ContextReductionReason,
            instructions: str | None = None,
    ) -> ContextProjection | None:
        messages = context.messages or ()
        projection = context.projection if context.projection is not None else ContextProjection.ZERO

        start = projection.first_kept_message_index
        if start >= len(messages):
            return None

        # The system prompt and tools are sent whatever is kept, and the summary has to fit alongside the tail.
        fixed_tokens = self._estimator.estimate_context(self._builder.build(dc.replace(
            context,
            messages=None,
            projection=None,
        )))
        tail_limit = min(
            self._config.keep_recent_tokens,
            max(target_tokens - fixed_tokens - self._config.max_summary_tokens, 0),
        )

        cut = self._choose_cut(context, start=start, tail_limit=tail_limit)
        if cut <= start:
            return None

        blocks = self._material(context, start=start, cut=cut)
        if not blocks:
            return None

        budget_tokens: int | None = None
        if (limits := llm.resolve_model_limits(backend.model)) is not None:
            budget_tokens = max(
                limits.input_budget(
                    output_reserve=min(self._config.max_summary_tokens, limits.output),
                ) - self._config.safety_margin_tokens,
                0,
            )

        request = self._fit(
            blocks,
            budget_tokens=budget_tokens,
            previous_summary=projection.summary,
            instructions=instructions,
        )

        response = await backend.immediate(
            request,
            llm.Options(max_tokens=self._config.max_summary_tokens).merge(self._config.options),
        )

        summary = '\n\n'.join(
            content.text
            for content in response.content
            if isinstance(content, llm.TextContent)
        ).strip()
        if not summary:
            return None

        return ContextProjection(
            summary=summary,
            first_kept_message_index=cut,
            tool_results=tuple(p for p in projection.tool_results if p.message_index >= cut),
        )
