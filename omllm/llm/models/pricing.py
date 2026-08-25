"""Deferred model pricing fed by the baked modeldb cache (USD per million tokens, the models.dev convention)."""
from omcore import lang
from omcore import marshal as msh

from ..types.models import TokenPricing
from ..types.models import TokenPricingProvider


with lang.auto_proxy_import(globals()):
    from ... import modeldb


##


def modeldb_token_pricing(provider: str, model_id: str) -> TokenPricingProvider:
    """
    A deferred pricing lookup into the baked modeldb cache, keyed by modeldb's own provider and model ids. Nothing is
    read or parsed until the returned provider is called - at backend construction - and an unknown provider or model
    (such as after a cache refresh) yields None rather than failing.
    """

    def get() -> TokenPricing | None:
        try:
            raw_cost = modeldb.load_providers_raw()[provider]['models'][model_id]['cost']
        except KeyError:
            return None

        # Only the one model's cost subtree is unmarshaled - never the whole cache.
        cost = msh.unmarshal(raw_cost, modeldb.Cost)

        return TokenPricing(
            input=cost.input,
            output=cost.output,
            reasoning=cost.reasoning,
            cache_read=cost.cache_read,
            cache_write=cost.cache_write,
        )

    return get
