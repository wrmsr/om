"""Real-API integration tests of Anthropic prompt caching, verified by reported cached token counts."""
import pytest

from omcore.secrets.tests.harness import HarnessSecrets

from .....models.default import default_model_catalog
from .....types.models import ModelKey
from .....types.options import CacheRetention
from .....types.options import Options
from ....tests import caching
from ..immediate import AnthropicMessagesImmediateBackend


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(180)
async def test_anthropic_prompt_caching(harness):
    svc = AnthropicMessagesImmediateBackend(
        default_model_catalog()[ModelKey('anthropic', 'claude-sonnet-5')],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip('anthropic_api_key'),
    )

    # Anthropic caching is explicit opt-in (the top-level moving-breakpoint cache_control) and deterministic - writes
    # and reads are reported exactly, so the hit steps need no retries.
    usages = await caching.run_caching_scenario(
        svc,
        Options(cache_retention=CacheRetention.FIVE_MINUTES),
    )

    print(usages)

    prime, full, partial = usages.prime, usages.full, usages.partial

    # The run-unique nonce guarantees the prime starts cold: it writes the whole prefix and reads nothing.
    assert not prime.cache_read
    assert prime.cache_write

    # Full hit: the identical request reads back exactly what the prime wrote, and writes nothing new.
    assert full.cache_read == prime.cache_write
    assert not full.cache_write

    # Partial hit: the extended conversation still reads exactly the primed prefix, while the moving breakpoint
    # writes only the small extension - which the inclusive input total counts on top of the read.
    assert partial.cache_read == prime.cache_write
    assert partial.cache_write
    assert partial.cache_write < partial.cache_read
    assert partial.input is not None
    assert partial.input > partial.cache_read

    # Anthropic reports no money - cost figures are estimated from the model's static modeldb-fed pricing, and the
    # cache discount shows up in dollars: the prime pays the cache write rate over the prefix, while the full hit
    # pays only the (much cheaper) cache read rate over it.
    for u in (prime, full, partial):
        assert u.cost is not None
        assert u.cost.source == 'estimated'
        assert u.cost.input is not None and u.cost.input > 0
        assert u.cost.output is not None and u.cost.output > 0
        assert u.cost.total is not None and u.cost.total > 0
    assert prime.cost is not None and full.cost is not None
    assert prime.cost.input is not None and full.cost.input is not None
    assert full.cost.input < prime.cost.input
