import pytest

from ...types.messages import TokenCost
from ...types.messages import TokenUsage
from ...types.models import TokenPricing
from ..pricing import estimate_token_cost
from ..pricing import fill_estimated_token_cost


# Real claude-sonnet-5 prices, USD per million tokens.
_PRICING = TokenPricing(
    input=2.,
    output=10.,
    cache_read=.2,
    cache_write=2.5,
)


def test_estimate_plain():
    cost = estimate_token_cost(TokenUsage(input=100, output=10), _PRICING)

    assert cost.source == 'estimated'
    assert cost.input == pytest.approx(2. * 100 / 1e6)
    assert cost.output == pytest.approx(10. * 10 / 1e6)
    assert cost.reasoning is None
    assert cost.cache_read is None
    assert cost.cache_write is None
    assert cost.total == pytest.approx((2. * 100 + 10. * 10) / 1e6)


def test_estimate_cache_write():
    # A captured cold-prime usage: the inclusive input is all but 2 tokens cache write.
    cost = estimate_token_cost(TokenUsage(input=8869, output=4, cache_write=8867), _PRICING)

    assert cost.input == pytest.approx((2. * 2 + 2.5 * 8867) / 1e6)
    assert cost.cache_write == pytest.approx(2.5 * 8867 / 1e6)
    assert cost.cache_read is None


def test_estimate_cache_read():
    # The corresponding full-hit usage: the same prefix read back at the (much cheaper) cache read price.
    cost = estimate_token_cost(TokenUsage(input=8869, output=4, cache_read=8867), _PRICING)

    assert cost.input == pytest.approx((2. * 2 + .2 * 8867) / 1e6)
    assert cost.cache_read == pytest.approx(.2 * 8867 / 1e6)
    assert cost.cache_write is None


def test_estimate_reasoning_priced_distinctly():
    pricing = TokenPricing(input=1., output=4., reasoning=2.)
    cost = estimate_token_cost(TokenUsage(input=100, output=50, reasoning=30), pricing)

    assert cost.output == pytest.approx((4. * 20 + 2. * 30) / 1e6)
    assert cost.reasoning == pytest.approx(2. * 30 / 1e6)


def test_estimate_reasoning_bills_as_output():
    pricing = TokenPricing(input=1., output=4.)
    cost = estimate_token_cost(TokenUsage(input=100, output=50, reasoning=30), pricing)

    assert cost.output == pytest.approx(4. * 50 / 1e6)
    assert cost.reasoning == pytest.approx(4. * 30 / 1e6)


def test_estimate_unpriced_cache_bills_as_input():
    pricing = TokenPricing(input=1., output=4.)
    cost = estimate_token_cost(TokenUsage(input=100, output=10, cache_read=60), pricing)

    assert cost.input == pytest.approx(1. * 100 / 1e6)
    assert cost.cache_read == pytest.approx(1. * 60 / 1e6)


def test_estimate_unknown_components():
    cost = estimate_token_cost(TokenUsage(input=100, output=10), TokenPricing(output=1.))

    assert cost.input is None
    assert cost.output == pytest.approx(1. * 10 / 1e6)
    assert cost.total == pytest.approx(1. * 10 / 1e6)

    empty = estimate_token_cost(TokenUsage(input=100, output=10), TokenPricing())
    assert empty.total is None


def test_fill_estimated_token_cost():
    usage = TokenUsage(input=100, output=10)
    filled = fill_estimated_token_cost(usage, _PRICING)
    assert filled is not None
    assert filled.cost is not None
    assert filled.cost.source == 'estimated'
    assert filled.input == 100

    assert fill_estimated_token_cost(None, _PRICING) is None
    assert fill_estimated_token_cost(usage, None) is usage

    # A cost already present - such as one reported by the provider - is never overwritten.
    reported = TokenUsage(input=100, cost=TokenCost(source='reported', total=1.))
    assert fill_estimated_token_cost(reported, _PRICING) is reported
