import typing as ta

from omcore import dataclasses as dc
from omcore import lang


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
