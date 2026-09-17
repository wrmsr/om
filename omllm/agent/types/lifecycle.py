import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ... import llm


ContextReductionReason: ta.TypeAlias = ta.Literal[
    'tool_output_limit',
    'threshold',
    'overflow',
    'manual',
]


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.truthy_repr)
class UsageLedger:
    """Cumulative provider traffic for one agent context, with overlapping usage details kept explicit."""

    input: int = 0
    output: int = 0
    reasoning: int = 0
    cache_read: int = 0
    cache_write: int = 0

    @property
    def uncached_input(self) -> int:
        return max(self.input - self.cache_read - self.cache_write, 0)

    @property
    def visible_output(self) -> int:
        return max(self.output - self.reasoning, 0)

    def add(self, usage: llm.TokenUsage | None) -> ta.Self:
        if usage is None:
            return self

        return dc.replace(
            self,
            input=self.input + (usage.input or 0),
            output=self.output + (usage.output or 0),
            reasoning=self.reasoning + (usage.reasoning or 0),
            cache_read=self.cache_read + (usage.cache_read or 0),
            cache_write=self.cache_write + (usage.cache_write or 0),
        )


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ContextLifecycleConfig:
    """Provider-neutral policy inputs shared by accounting and context reduction."""

    output_reserve_tokens: int = 16_000
    safety_margin_tokens: int = 1_024

    # An individual tool result is truncated in the model projection at this many characters. The complete result stays
    # in the transcript. None disables this bound.
    max_tool_result_chars: int | None = 30_000

    # Proactive pruning preserves approximately this much of the newest transcript. Forced overflow recovery may prune
    # inside it when that is the only reducible material left.
    keep_recent_tokens: int = 20_000
    prune_min_chars: int = 2_000
    prune_headroom_tokens: int = 4_000

    prune_tool_results: bool = True
    prunable_tool_names: ta.AbstractSet[str] = frozenset({
        'bash',
        'glob',
        'ls',
        'process_list',
        'process_read',
        'read',
        'ripgrep',
        'web_fetch',
        'web_search',
    })

    max_overflow_retries: int = 1

    def __post_init__(self) -> None:
        check.arg(self.output_reserve_tokens >= 0)
        check.arg(self.safety_margin_tokens >= 0)
        check.arg(self.max_tool_result_chars is None or self.max_tool_result_chars > 0)
        check.arg(self.keep_recent_tokens >= 0)
        check.arg(self.prune_min_chars > 0)
        check.arg(self.prune_headroom_tokens >= 0)
        check.arg(self.max_overflow_retries >= 0)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ContextBudget:
    """The latest observed prompt occupancy against a model's usable input budget."""

    context_limit: int
    input_limit: int
    threshold: int
    output_reserve: int

    observed_input: int | None = None
    estimated_input: int | None = None

    def __post_init__(self) -> None:
        check.arg(self.context_limit > 0)
        check.arg(0 <= self.threshold <= self.input_limit <= self.context_limit)
        check.arg(0 <= self.output_reserve <= self.context_limit)
        check.arg(self.observed_input is None or self.observed_input >= 0)
        check.arg(self.estimated_input is None or self.estimated_input >= 0)

    @property
    def input(self) -> int | None:
        return self.estimated_input if self.estimated_input is not None else self.observed_input

    @property
    def is_estimated(self) -> bool:
        return self.estimated_input is not None

    @classmethod
    def of(
            cls,
            limits: llm.ModelLimits,
            config: ContextLifecycleConfig,
            *,
            requested_output: int | None = None,
            observed_input: int | None = None,
            estimated_input: int | None = None,
    ) -> ta.Self:
        output_reserve = min(
            requested_output if requested_output is not None else config.output_reserve_tokens,
            limits.output,
        )
        input_limit = limits.input_budget(output_reserve=output_reserve)

        return cls(
            context_limit=limits.context,
            input_limit=input_limit,
            threshold=max(input_limit - config.safety_margin_tokens, 0),
            output_reserve=output_reserve,
            observed_input=observed_input,
            estimated_input=estimated_input,
        )


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolResultProjection:
    """A character limit for one tool-result message in the model view; zero means replace it with a placeholder."""

    message_index: int
    max_chars: int

    def __post_init__(self) -> None:
        check.arg(self.message_index >= 0)
        check.arg(self.max_chars >= 0)

    @property
    def is_pruned(self) -> bool:
        return self.max_chars == 0


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ContextProjection:
    """Durable instructions for deriving a reduced model view from the lossless transcript."""

    summary: str | None = None
    first_kept_message_index: int = 0
    tool_results: ta.Sequence[ToolResultProjection] = ()

    def __post_init__(self) -> None:
        check.arg(self.first_kept_message_index >= 0)
        check.unique(p.message_index for p in self.tool_results)
        check.arg(self.summary is not None or self.first_kept_message_index == 0)

    @property
    def tool_results_by_message_index(self) -> ta.Mapping[int, ToolResultProjection]:
        return {p.message_index: p for p in self.tool_results}

    def with_tool_result(self, projection: ToolResultProjection) -> ta.Self:
        by_index = dict(self.tool_results_by_message_index)
        current = by_index.get(projection.message_index)
        if current is not None and current.max_chars <= projection.max_chars:
            return self
        by_index[projection.message_index] = projection
        return dc.replace(self, tool_results=tuple(by_index[i] for i in sorted(by_index)))


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ContextReduction:
    """One change to the model projection, reported without exposing or altering the complete transcript."""

    reason: ContextReductionReason
    before_tokens: int
    after_tokens: int
    tool_result_indices: ta.Sequence[int] = ()
    compacted: bool = False

    @property
    def freed_tokens(self) -> int:
        return max(self.before_tokens - self.after_tokens, 0)
