import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from .compat import Compat
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
@msh.update_field_options(omit_if=lang.is_none)
class CacheCapabilities:
    # The provider request shape, including implicit-only providers which expose no request controls.
    control_style: CacheControlStyle

    # Exact retention policies which may be requested through Options.
    retentions: ta.AbstractSet[CacheRetention] | None = None

    # Whether Options.cache_key can be translated for this model.
    key: bool | None = None


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
@msh.update_field_options(omit_if=lang.is_none)
class TokenPricing:
    """Static per-component prices, in USD per million tokens (the models.dev convention)."""

    input: float | None = None

    output: float | None = None

    # The price of reasoning output tokens, when priced distinctly. Otherwise they bill as ordinary output.
    reasoning: float | None = None

    # The prices of prompt cache reads / writes. When unpriced but reported in usage, they bill as ordinary input - an
    # over-estimate wherever cache reads are discounted, which is the safe direction.
    cache_read: float | None = None
    cache_write: float | None = None


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
@msh.update_field_options(omit_if=lang.is_none)
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
    pricing: TokenPricing | TokenPricingProvider | None = dc.xfield(
        default=None,
    ) | msh.dc_field_options(
        omit_if=lang.is_none,
        marshal_via=msh.MarshalVia(TokenPricing | None),
        unmarshal_via=msh.UnmarshalVia(TokenPricing | None),
    )

    #

    @ta.final
    @dc.dataclass(frozen=True, kw_only=True)
    @dc.extra_class_params(default_repr_fn=lang.opt_repr)
    @msh.update_field_options(omit_if=lang.is_none)
    class Http:
        base_url: str | None = None

        extra_headers: ta.Mapping[str, str] | None = None

    http: Http | None = None

    #

    default_options: Options | None = None
