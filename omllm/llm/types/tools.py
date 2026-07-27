"""Tool definitions advertised to providers. `parameters` is a plain JSON Schema mapping."""
import typing as ta

from omcore import cached
from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ToolParam:
    name: str = dc.xfield(coerce=check.non_empty_str)
    description: str | None = None
    type: str = dc.xfield(coerce=check.non_empty_str)
    optional: bool = dc.xfield(False, repr_fn=lang.truthy_repr)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class Tool:
    name: str = dc.xfield(coerce=check.non_empty_str)
    description: str | None = None
    params: ta.Sequence[ToolParam] = ()
    type: str | None = dc.xfield(None, validate=lambda s: s is None or (isinstance(s, str) and bool(s)))

    @cached.property
    @dc.init
    def params_by_name(self) -> ta.Mapping[str, ToolParam]:
        return col.make_map(((p.name, p) for p in self.params), strict=True)
