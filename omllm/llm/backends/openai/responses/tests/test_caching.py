"""
Real-API integration tests of prompt caching through the openai responses backend, verified by reported cached token
counts.
"""
import uuid

import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.models import ModelKey
from .....types.options import CacheRetention
from .....types.options import Options
from ....tests import caching
from ..immediate import OpenaiResponsesImmediateBackend


# OpenAI's implicit caching only engages for prompts of at least this many tokens (with reads reported in 128-token
# blocks), and it doubles as this module's floor for what counts as a substantial cache hit.
_MIN_CACHEABLE_PROMPT_TOKENS = 1024


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(180)
async def test_openai_prompt_caching(harness):
    svc = OpenaiResponsesImmediateBackend(
        default_model_catalog()[ModelKey('openai', 'gpt-5.6-luna')],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip('openai_api_key'),
    )

    # OpenAI caching is implicit and best-effort: the cache key pins request routing, and the hit steps may retry
    # until a hit is reported. The partial step replays the prime response - reasoning identity included - through
    # the stateless request translation.
    usages = await caching.run_caching_scenario(
        svc,
        Options(
            cache_key=f'om-test-{uuid.uuid4().hex}',
            cache_retention=CacheRetention.THIRTY_MINUTES,
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
