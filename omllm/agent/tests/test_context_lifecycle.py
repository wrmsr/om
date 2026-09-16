from ... import llm
from ..types.context_lifecycle import ContextBudget
from ..types.context_lifecycle import ContextLifecycleConfig
from ..types.context_lifecycle import UsageLedger


##


def test_usage_ledger_keeps_inclusive_totals_and_exclusive_views():
    ledger = UsageLedger().add(llm.TokenUsage(
        input=15_000,
        output=100,
        reasoning=20,
        cache_read=12_000,
        cache_write=2_000,
    ))
    ledger = ledger.add(llm.TokenUsage(input=100, output=10))

    assert ledger == UsageLedger(
        input=15_100,
        output=110,
        reasoning=20,
        cache_read=12_000,
        cache_write=2_000,
    )
    assert ledger.uncached_input == 1_100
    assert ledger.visible_output == 90


def test_context_budget_honors_model_input_and_requested_output_limits():
    limits = llm.ModelLimits(context=100_000, input=80_000, output=30_000)
    config = ContextLifecycleConfig(output_reserve_tokens=16_000, safety_margin_tokens=1_000)

    by_input = ContextBudget.of(limits, config, observed_input=12_000)
    assert by_input.input_limit == 80_000
    assert by_input.threshold == 79_000
    assert by_input.input == 12_000
    assert not by_input.is_estimated

    by_context = ContextBudget.of(limits, config, requested_output=30_000, estimated_input=50_000)
    assert by_context.input_limit == 70_000
    assert by_context.threshold == 69_000
    assert by_context.input == 50_000
    assert by_context.is_estimated
