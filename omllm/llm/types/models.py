import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .compat import Compat
from .messages import TokenCost
from .messages import TokenUsage
from .options import CacheRetention
from .options import Options


type TokenPricingProvider = ta.Callable[[], TokenPricing | None]


CacheControlStyle: ta.TypeAlias = ta.Literal[
    'anthropic',
    'google_implicit',
    'openai_legacy',
    'openai_ttl',

    # Implicit upstream caching behind a load-balancing gateway - no request cache fields, but Options.cache_key is
    # translated to a session affinity header so repeat requests reach the same upstream (and thus its cache).
    'openrouter',
]


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class CacheCapabilities:
    # The provider request shape, including implicit-only providers which expose no request controls.
    control_style: CacheControlStyle

    # Exact retention policies which may be requested through Options.
    retentions: ta.AbstractSet[CacheRetention] = frozenset()

    # Whether Options.cache_key can be translated for this model.
    key: bool = False


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TokenPricing:
    """Static per-component prices, in USD per million tokens (the models.dev convention)."""

    input: float | None = None

    output: float | None = None

    # The price of reasoning output tokens, when priced distinctly. Otherwise they bill as ordinary output.
    reasoning: float | None = None

    # The prices of prompt cache reads / writes. When unpriced but reported in usage, they bill as ordinary input -
    # an over-estimate wherever cache reads are discounted, which is the safe direction.
    cache_read: float | None = None
    cache_write: float | None = None

    def estimate(self, usage: TokenUsage) -> TokenCost:
        """
        Estimates a usage's cost, mirroring its inclusive/overlapping component semantics. Components whose price or
        token count is unknown are left unset, and the total is the sum of the known inclusive components.
        """

        def dollars(price: float | None, tokens: int | None) -> float | None:
            if price is None or tokens is None:
                return None
            return price * tokens / 1_000_000

        cache_read_cost = dollars(self.cache_read if self.cache_read is not None else self.input, usage.cache_read)
        cache_write_cost = dollars(self.cache_write if self.cache_write is not None else self.input, usage.cache_write)

        input_cost: float | None = None
        if usage.input is not None and self.input is not None:
            # The usage's input is inclusive - only the remainder past the cache traffic bills at the input price.
            uncached_tokens = max(usage.input - (usage.cache_read or 0) - (usage.cache_write or 0), 0)
            input_cost = self.input * uncached_tokens / 1_000_000
            if cache_read_cost is not None:
                input_cost += cache_read_cost
            if cache_write_cost is not None:
                input_cost += cache_write_cost

        reasoning_cost = dollars(self.reasoning if self.reasoning is not None else self.output, usage.reasoning)

        output_cost: float | None = None
        if usage.output is not None and self.output is not None:
            # The usage's output is inclusive - only the remainder past the reasoning bills at the output price.
            plain_tokens = max(usage.output - (usage.reasoning or 0), 0)
            output_cost = self.output * plain_tokens / 1_000_000
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


def fill_estimated_token_cost(usage: TokenUsage | None, pricing: TokenPricing | None) -> TokenUsage | None:
    """Fills in an estimated cost when pricing is known and no cost (such as a reported one) is already present."""

    if usage is None or pricing is None or usage.cost is not None:
        return usage
    return dc.replace(usage, cost=pricing.estimate(usage))


##


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True, cache_hash=True)
class ModelKey:
    provider: str
    id: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.provider)
        check.non_empty_str(self.id)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class Model:
    key: ModelKey

    name: str | None = ''

    backend: str

    #

    compat: Compat | None = None

    #

    cache: CacheCapabilities | None = None

    #

    # Static pricing, or a deferred provider of it. Resolved once, at backend construction - catalog definitions must
    # never eagerly load pricing data. Reported response costs, where available, take precedence over estimates.
    pricing: TokenPricing | TokenPricingProvider | None = None

    #

    @ta.final
    @dc.dataclass(frozen=True, kw_only=True)
    @dc.extra_class_params(default_repr_fn=lang.opt_repr)
    class Http:
        base_url: str | None = None

        extra_headers: ta.Mapping[str, str] | None = None

    http: Http | None = None

    #

    default_options: Options | None = None
