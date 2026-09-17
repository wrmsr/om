import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from ..projection.types import LlmContextBuilder
from ..types.contexts import Context
from ..types.lifecycle import ContextBudget
from ..types.lifecycle import ContextLifecycleConfig
from ..types.lifecycle import ContextProjection
from ..types.lifecycle import ContextReduction
from ..types.lifecycle import ContextReductionReason
from ..types.lifecycle import ToolResultProjection
from .compactors import ContextCompactor
from .estimators import CharacterContextTokenEstimator
from .estimators import ContextTokenEstimator


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ContextLifecycleResult:
    context: Context
    llm_context: llm.Context
    context_budget: ContextBudget | None = None
    reduction: ContextReduction | None = None


class ContextLifecycleManager(lang.Abstract):
    """Prepares a model projection and, separately, tries a stronger reduction after a provider overflow."""

    @abc.abstractmethod
    async def prepare(
            self,
            context: Context,
            *,
            builder: LlmContextBuilder,
            model: llm.Model,
            options: llm.Options | None = None,
            config: ContextLifecycleConfig | None = None,
    ) -> ContextLifecycleResult:
        raise NotImplementedError

    @abc.abstractmethod
    async def recover_overflow(
            self,
            context: Context,
            *,
            builder: LlmContextBuilder,
            model: llm.Model,
            options: llm.Options | None = None,
            config: ContextLifecycleConfig | None = None,
    ) -> ContextLifecycleResult:
        raise NotImplementedError


class StandardContextLifecycleManager(ContextLifecycleManager):
    def __init__(
            self,
            *,
            estimator: ContextTokenEstimator | None = None,
            compactor: ContextCompactor | None = None,
    ) -> None:
        super().__init__()

        self._estimator = estimator if estimator is not None else CharacterContextTokenEstimator()
        self._compactor = compactor

    @staticmethod
    def _tool_result_chars(message: llm.ToolResultMessage) -> int:
        return sum(len(content.text) for content in message.content)

    def _with_tool_output_limits(
            self,
            context: Context,
            config: ContextLifecycleConfig,
    ) -> tuple[Context, list[int]]:
        if (max_chars := config.max_tool_result_chars) is None:
            return context, []

        projection = context.projection or ContextProjection.ZERO
        changed: list[int] = []
        for index, message in enumerate(context.messages or ()):
            if not isinstance(message, llm.ToolResultMessage):
                continue
            if self._tool_result_chars(message) <= max_chars:
                continue

            new_projection = projection.with_tool_result(ToolResultProjection(
                message_index=index,
                max_chars=max_chars,
            ))
            if new_projection is not projection:
                projection = new_projection
                changed.append(index)

        return dc.replace(context, projection=projection), changed

    def _protected_message_start(self, context: Context, config: ContextLifecycleConfig) -> int:
        if config.keep_recent_tokens == 0:
            return len(context.messages or ())

        tokens = 0
        start = len(context.messages or ())
        for index in range(start - 1, -1, -1):
            message = (context.messages or ())[index]
            if isinstance(message, llm.Message):
                tokens += self._estimator.estimate_message(message)
            start = index
            if tokens >= config.keep_recent_tokens:
                break
        return start

    def _prunable_tool_result_indices(
            self,
            context: Context,
            config: ContextLifecycleConfig,
            *,
            force: bool,
    ) -> ta.Iterator[int]:
        if not config.prune_tool_results:
            return

        protected_start = self._protected_message_start(context, config)
        if context.projection is not None:
            projected = context.projection.tool_results_by_message_index
        else:
            projected = {}

        for index, message in enumerate(context.messages or ()):
            if not isinstance(message, llm.ToolResultMessage):
                continue
            if message.is_error:
                continue
            if message.tool_name not in (config.prunable_tool_names or ()):
                continue
            if self._tool_result_chars(message) < config.prune_min_chars:
                continue
            if projected.get(index) is not None and projected[index].is_pruned:
                continue
            if not force and index >= protected_start:
                continue
            yield index

    @staticmethod
    def _requested_output(model: llm.Model, options: llm.Options | None) -> int | None:
        return llm.Options().merge(model.default_options, options).max_tokens

    async def _prepare(
            self,
            context: Context,
            *,
            builder: LlmContextBuilder,
            model: llm.Model,
            options: llm.Options | None,
            config: ContextLifecycleConfig | None = None,
            reason: ContextReductionReason,
            force: bool,
    ) -> ContextLifecycleResult:
        if config is None:
            config = ContextLifecycleConfig.ZERO

        before_context = builder.build(context)
        before_tokens = self._estimator.estimate_context(before_context)
        original_projection = context.projection

        context, changed_indices = self._with_tool_output_limits(context, config)
        llm_context = builder.build(context)
        estimated_tokens = self._estimator.estimate_context(llm_context)

        budget: ContextBudget | None = None
        target_tokens: int | None = None
        if (limits := llm.resolve_model_limits(model)) is not None:
            budget = ContextBudget.of(
                limits,
                config,
                requested_output=self._requested_output(model, options),
                observed_input=(
                    context.context_budget.observed_input
                    if context.context_budget is not None
                    else None
                ),
                estimated_input=estimated_tokens,
            )
            if force or estimated_tokens > budget.threshold:
                target_tokens = max(
                    budget.threshold - min(config.prune_headroom_tokens, budget.threshold),
                    0,
                )

        elif force:
            # A provider overflow is authoritative even when its catalog has no limits. One deterministic reduction is
            # still worthwhile; the target makes the loop stop after at least one candidate.
            target_tokens = estimated_tokens

        pruned_indices: list[int] = []
        if target_tokens is not None:
            for index in self._prunable_tool_result_indices(context, config, force=force):
                context = dc.replace(
                    context,
                    projection=(context.projection or ContextProjection.ZERO).with_tool_result(ToolResultProjection(
                        message_index=index,
                        max_chars=0,
                    )),
                )
                pruned_indices.append(index)

                llm_context = builder.build(context)
                estimated_tokens = self._estimator.estimate_context(llm_context)
                if estimated_tokens <= target_tokens:
                    break

        compacted = False
        if (
                target_tokens is not None and
                (estimated_tokens > target_tokens or (force and not pruned_indices)) and
                self._compactor is not None
        ):
            compacted_projection = await self._compactor.compact(
                context,
                target_tokens=target_tokens,
                reason=reason,
            )
            if compacted_projection is not None and compacted_projection != context.projection:
                context = dc.replace(context, projection=compacted_projection)
                compacted = True
                llm_context = builder.build(context)
                estimated_tokens = self._estimator.estimate_context(llm_context)

        if budget is not None:
            budget = dc.replace(budget, estimated_input=estimated_tokens)
        context = dc.replace(context, context_budget=budget)

        reduction: ContextReduction | None = None
        if (context.projection or ContextProjection.ZERO) != (original_projection or ContextProjection.ZERO):
            reduction_reason = reason
            if reason == 'threshold' and not pruned_indices and not compacted:
                reduction_reason = 'tool_output_limit'
            reduction = ContextReduction(
                reason=reduction_reason,
                before_tokens=before_tokens,
                after_tokens=estimated_tokens,
                tool_result_indices=tuple(sorted({*changed_indices, *pruned_indices})),
                compacted=compacted,
            )

        return ContextLifecycleResult(
            context=context,
            llm_context=llm_context,
            context_budget=budget,
            reduction=reduction,
        )

    async def prepare(
            self,
            context: Context,
            *,
            builder: LlmContextBuilder,
            model: llm.Model,
            options: llm.Options | None = None,
            config: ContextLifecycleConfig | None = None,
    ) -> ContextLifecycleResult:
        return await self._prepare(
            context,
            builder=builder,
            model=model,
            options=options,
            config=config,
            reason='threshold',
            force=False,
        )

    async def recover_overflow(
            self,
            context: Context,
            *,
            builder: LlmContextBuilder,
            model: llm.Model,
            options: llm.Options | None = None,
            config: ContextLifecycleConfig | None = None,
    ) -> ContextLifecycleResult:
        return await self._prepare(
            context,
            builder=builder,
            model=model,
            options=options,
            config=config,
            reason='overflow',
            force=True,
        )
