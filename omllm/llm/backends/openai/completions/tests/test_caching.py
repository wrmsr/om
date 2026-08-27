"""
Real-API integration tests of prompt caching through the openai completions backend - for OpenAI itself and for
OpenRouter - verified by reported cached token counts.
"""
import uuid

import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.context import Context
from .....types.messages import UserMessage
from .....types.models import ModelKey
from .....types.options import CacheRetention
from .....types.options import Options
from ....tests import caching
from ..immediate import OpenaiCompletionsImmediateBackend
from ..requests import RequestPreparer


# OpenAI's implicit caching only engages for prompts of at least this many tokens (with reads reported in 128-token
# blocks), and it doubles as this module's floor for what counts as a substantial cache hit.
_MIN_CACHEABLE_PROMPT_TOKENS = 1024


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(180)
async def test_openai_prompt_caching(harness):
    svc = OpenaiCompletionsImmediateBackend(
        default_model_catalog()[ModelKey('openai', 'gpt-5.6-luna')],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip('openai_api_key'),
    )

    # OpenAI caching is implicit and best-effort: the cache key pins request routing, and the hit steps may retry
    # until a hit is reported. Only cache reads are reported - there is no write count.
    usages = await caching.run_caching_scenario(
        svc,
        Options(
            cache_key=f'om-test-{uuid.uuid4().hex}',
            cache_retention=CacheRetention.ONE_DAY,
        ),
        hit_attempts=6,
        min_cache_read=_MIN_CACHEABLE_PROMPT_TOKENS,
    )

    print(usages)

    prime, full, partial = usages.prime, usages.full, usages.partial

    # The run-unique nonce guarantees the prime starts cold.
    assert not prime.cache_read

    # Full hit: the identical request reads a large block-rounded prefix, strictly less than the inclusive input total
    # (the tail past the last block boundary is never cached).
    assert full.cache_read is not None
    assert full.input is not None
    assert full.cache_read >= _MIN_CACHEABLE_PROMPT_TOKENS
    assert full.cache_read < full.input

    # Partial hit: the primed prefix is still read while the conversation extension grows the uncached input.
    assert partial.cache_read is not None
    assert partial.input is not None
    assert partial.cache_read >= _MIN_CACHEABLE_PROMPT_TOKENS
    assert partial.input > partial.cache_read
    assert partial.input > full.input

    # Openai reports no money - cost figures are estimated from the model's static modeldb-fed pricing, and the cache
    # discount shows up in dollars: the full hit prices its read-back prefix at the (cheaper) cache read rate.
    for u in (prime, full, partial):
        assert u.cost is not None
        assert u.cost.source == 'estimated'
        assert u.cost.input is not None and u.cost.input > 0
        assert u.cost.output is not None and u.cost.output > 0
        assert u.cost.total is not None and u.cost.total > 0
    assert prime.cost is not None and full.cost is not None
    assert prime.cost.input is not None and full.cost.input is not None
    assert full.cost.input < prime.cost.input


##


def test_openrouter_cache_request_translation():
    model = default_model_catalog()[ModelKey('openrouter', 'deepseek/deepseek-v4-flash-0731')]  # noqa
    context = Context(messages=[UserMessage('hi')])

    # The cache key becomes the session affinity header, never a request body field.
    preparer = RequestPreparer(model, context, Options(cache_key='some-key'))
    assert preparer.raw_headers() == {'x-session-id': 'some-key'}
    assert 'prompt_cache_key' not in preparer.raw_request()

    # Without a cache key there is nothing to pin.
    assert RequestPreparer(model, context, None).raw_headers() == {}

    # Upstream caching is implicit - no retention policy is controllable.
    with pytest.raises(ValueError):  # noqa: PT011
        RequestPreparer(model, context, Options(cache_retention=CacheRetention.ONE_DAY)).raw_request()


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(180)
@pytest.mark.parametrize('model_id', [
    'deepseek/deepseek-v4-flash-0731',
    'deepseek/deepseek-v4-pro-0813',
    'moonshotai/kimi-k3',
    'z-ai/glm-5.3',
])
async def test_openrouter_prompt_caching(harness, model_id):
    svc = OpenaiCompletionsImmediateBackend(
        default_model_catalog()[ModelKey('openrouter', model_id)],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip('openrouter_api_key'),
    )

    # OpenRouter passes through its upstream providers' implicit caching, and load-balances across them - the cache key
    # pins repeat requests to one upstream via session affinity, without which a hit is routing luck. Only cache reads
    # are reported for these models - their upstreams cache implicitly, with no write count.
    usages = await caching.run_caching_scenario(
        svc,
        Options(
            cache_key=f'om-test-{uuid.uuid4().hex}',
            max_tokens=512,
        ),
        hit_attempts=6,
        min_cache_read=_MIN_CACHEABLE_PROMPT_TOKENS,
    )

    print(usages)

    prime, full, partial = usages.prime, usages.full, usages.partial

    # The run-unique nonce guarantees the prime starts cold, so it must not read any substantial prefix - though some
    # upstreams report sub-block noise on a cold prompt (observed: a flat 64 tokens from moonshot).
    assert (prime.cache_read or 0) < _MIN_CACHEABLE_PROMPT_TOKENS

    # Full hit: the identical request reads a large prefix, bounded by the inclusive input total. Cache granularity
    # varies per upstream provider, not per model - the same model has shown coarse 128-token blocks on one run and
    # all-but-one-token coverage on another - so no tighter upper bound holds.
    assert full.cache_read is not None
    assert full.input is not None
    assert full.cache_read >= _MIN_CACHEABLE_PROMPT_TOKENS
    assert full.cache_read <= full.input

    # Partial hit: the primed prefix is still read while the conversation extension goes uncached. Input totals are not
    # compared across steps here - upstream providers tokenize differently, so counts are only self-consistent within a
    # response.
    assert partial.cache_read is not None
    assert partial.input is not None
    assert partial.cache_read >= _MIN_CACHEABLE_PROMPT_TOKENS
    assert partial.input > partial.cache_read

    # Openrouter reports each request's billed cost - authoritative under per-upstream price variance - which rides
    # usage as a reported TokenCost. Only the prompt/completions split is reported, never cache-level components. The
    # figures are only non-negative, not positive: routing to free upstream capacity legitimately bills 0.0.
    for u in (prime, full, partial):
        assert u.cost is not None
        assert u.cost.source == 'reported'
        assert u.cost.input is not None and u.cost.input >= 0
        assert u.cost.output is not None and u.cost.output >= 0
        assert u.cost.total is not None and u.cost.total >= 0
