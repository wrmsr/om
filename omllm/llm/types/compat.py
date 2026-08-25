import typing as ta

from omcore import dataclasses as dc
from omcore import lang


TokenCostMode: ta.TypeAlias = ta.Literal[
    # Reported billed request cost as returned by openrouter: usage.cost, plus the
    # usage.cost_details.upstream_inference_* prompt/completions split.
    'openrouter',
]


##


@dc.dataclass(frozen=True, kw_only=True)
class Compat(lang.Abstract):
    pass


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.truthy_repr)
class OpenaiCompat(Compat):
    url_path: str | None = None

    max_tokens_field: str | None = None

    # The message / delta field reasoning text is surfaced in, for backends serving models which report it. None
    # probes the conventional reasoning_content.
    reasoning_field: str | None = None

    # Which (if any) reported request cost fields to translate out of response usage. Response cost fields are only
    # ever probed as predeclared here, never speculatively.
    cost_mode: TokenCostMode | None = None
