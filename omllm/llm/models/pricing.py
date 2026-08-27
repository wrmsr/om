from omcore import dataclasses as dc

from ..types.messages import TokenCost
from ..types.messages import TokenUsage
from ..types.models import TokenPricing


##


def estimate_token_cost(
        usage: TokenUsage,
        pricing: TokenPricing,
) -> TokenCost:
    """
    Estimates a usage's cost, mirroring its inclusive/overlapping component semantics. Components whose price or
    token count is unknown are left unset, and the total is the sum of the known inclusive components.
    """

    def dollars(price: float | None, tokens: int | None) -> float | None:
        if price is None or tokens is None:
            return None
        return price * tokens / 1_000_000

    cache_read_cost = dollars(
        pricing.cache_read if pricing.cache_read is not None else pricing.input,
        usage.cache_read,
    )
    cache_write_cost = dollars(
        pricing.cache_write if pricing.cache_write is not None else pricing.input,
        usage.cache_write,
    )

    input_cost: float | None = None
    if usage.input is not None and pricing.input is not None:
        # The usage's input is inclusive - only the remainder past the cache traffic bills at the input price.
        uncached_tokens = max(usage.input - (usage.cache_read or 0) - (usage.cache_write or 0), 0)
        input_cost = pricing.input * uncached_tokens / 1_000_000
        if cache_read_cost is not None:
            input_cost += cache_read_cost
        if cache_write_cost is not None:
            input_cost += cache_write_cost

    reasoning_cost = dollars(pricing.reasoning if pricing.reasoning is not None else pricing.output, usage.reasoning)

    output_cost: float | None = None
    if usage.output is not None and pricing.output is not None:
        # The usage's output is inclusive - only the remainder past the reasoning bills at the output price.
        plain_tokens = max(usage.output - (usage.reasoning or 0), 0)
        output_cost = pricing.output * plain_tokens / 1_000_000
        if reasoning_cost is not None:
            output_cost += reasoning_cost

    total: float | None = None
    if input_cost is not None or output_cost is not None:
        total = (input_cost or 0.) + (output_cost or 0.)

    return TokenCost(
        source='estimated',
        input=input_cost,
        output=output_cost,
        reasoning=reasoning_cost,
        cache_read=cache_read_cost,
        cache_write=cache_write_cost,
        total=total,
    )


def fill_estimated_token_cost(
        usage: TokenUsage | None,
        pricing: TokenPricing | None,
) -> TokenUsage | None:
    """Fills in an estimated cost when pricing is known and no cost (such as a reported one) is already present."""

    if usage is None or pricing is None or usage.cost is not None:
        return usage
    return dc.replace(usage, cost=estimate_token_cost(usage, pricing))
