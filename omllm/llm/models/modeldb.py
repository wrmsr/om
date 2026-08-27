from omcore import check
from omcore import lang

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
            model = modeldb.load_provider_model(provider, model_id)
        except KeyError:
            return None

        cost = check.not_none(model.cost)

        return TokenPricing(
            input=cost.input,
            output=cost.output,
            reasoning=cost.reasoning,
            cache_read=cost.cache_read,
            cache_write=cost.cache_write,
        )

    return get
