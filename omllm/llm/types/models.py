import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from .compat import Compat
from .options import CacheRetention
from .options import Options
from .options import ReasoningEffort


type TokenPricingProvider = ta.Callable[[], TokenPricing | None]
type ModelLimitsProvider = ta.Callable[[], ModelLimits | None]


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


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
@msh.update_field_options(omit_if=lang.is_none)
class ModelLimits:
    """Provider-advertised token limits for a model."""

    context: int
    output: int
    input: int | None = None

    def __post_init__(self) -> None:
        check.arg(self.context > 0)
        check.arg(self.output > 0)
        check.arg(self.output <= self.context)
        check.arg(self.input is None or 0 < self.input <= self.context)

    def input_budget(self, *, output_reserve: int) -> int:
        """Maximum prompt tokens while retaining `output_reserve` tokens for the response."""

        check.arg(output_reserve >= 0)
        by_context = max(self.context - output_reserve, 0)
        return min(by_context, self.input) if self.input is not None else by_context


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
    # Must be present for actual use but may be None for temporary or base instances (and must be explicitly set to None
    # for such cases).
    key: ModelKey | None
    backend: str | None

    @property
    def key_(self) -> ModelKey:
        return check.not_none(self.key)

    @property
    def backend_(self) -> str:
        return check.not_none(self.backend)

    name: str | None = ''

    #

    compat: Compat | None = None

    #

    cache: CacheCapabilities | None = None

    # Exact levels accepted by this model on its configured backend. Unspecified models do not advertise effort control.
    reasoning_efforts: ta.AbstractSet[ReasoningEffort] | None = None
    # An optional further restriction when tools are supplied; None imposes no additional restriction.
    reasoning_efforts_with_tools: ta.AbstractSet[ReasoningEffort] | None = None

    #

    # Static token limits, or a deferred provider of them. As with pricing, catalog definitions use deferred modeldb
    # lookups so importing the catalog does not eagerly load the baked database.
    limits: ModelLimits | ModelLimitsProvider | None = dc.xfield(
        default=None,
    ) | msh.dc_field_options(
        omit_if=lang.is_none,
        marshal_via=msh.MarshalVia(ModelLimits | None),
        unmarshal_via=msh.UnmarshalVia(ModelLimits | None),
    )

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


def resolve_model_limits(model: Model) -> ModelLimits | None:
    """Resolves a model's possibly deferred limits without changing the catalog model."""

    limits = model.limits
    if callable(limits):
        limits = limits()
    return check.isinstance(limits, (ModelLimits, None))


def supported_reasoning_efforts(model: Model, *, with_tools: bool = False) -> ta.AbstractSet[ReasoningEffort]:
    levels = model.reasoning_efforts or frozenset()
    if with_tools and model.reasoning_efforts_with_tools is not None:
        levels = levels & model.reasoning_efforts_with_tools
    return levels


def validate_reasoning_effort(model: Model, effort: ReasoningEffort | None, *, with_tools: bool = False) -> None:
    levels = supported_reasoning_efforts(model, with_tools=with_tools)
    if effort is not None and effort not in levels:
        supported = ', '.join(e.value for e in ReasoningEffort if e in levels) or 'unavailable'
        qualifier = ' with tools' if with_tools else ''
        raise ValueError(
            f'Model {model.key!r} does not support effort {effort!s}{qualifier}. Supported levels: {supported}',
        )
