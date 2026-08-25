"""Real-API integration tests of Gemini implicit prompt caching, verified by reported cached token counts."""
import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.models import ModelKey
from ....tests import caching
from ..immediate import GoogleGenerativeImmediateBackend


# Gemini's implicit caching engages above a model-specific minimum prompt size well below the scenario prompt; this is
# just a conservative floor asserting a substantial prefix was actually read.
_MIN_ASSERTED_CACHED_TOKENS = 1024


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(180)
async def test_google_prompt_caching(harness):
    svc = GoogleGenerativeImmediateBackend(
        default_model_catalog()[ModelKey('google', 'gemini-3-flash-preview')],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip('gemini_api_key'),
    )

    # Gemini 2.5+ caching is implicit with no request controls at all - Options stay None - and best-effort, so the
    # hit steps may retry until a hit is reported. Only cache reads are reported - there is no write count.
    usages = await caching.run_caching_scenario(
        svc,
        None,
        hit_attempts=6,
        min_cache_read=_MIN_ASSERTED_CACHED_TOKENS,
    )

    print(usages)

    prime, full, partial = usages.prime, usages.full, usages.partial

    # The run-unique nonce guarantees the prime starts cold - a cold request reports no cached count at all.
    assert not prime.cache_read

    # Full hit: the identical request reads a large cached prefix, less than the inclusive input total.
    assert full.cache_read is not None
    assert full.input is not None
    assert full.cache_read >= _MIN_ASSERTED_CACHED_TOKENS
    assert full.cache_read < full.input

    # Partial hit: the primed prefix is still read while the conversation extension grows the uncached input.
    assert partial.cache_read is not None
    assert partial.input is not None
    assert partial.cache_read >= _MIN_ASSERTED_CACHED_TOKENS
    assert partial.input > partial.cache_read
    assert partial.input > full.input
