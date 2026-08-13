"""Tool definitions advertised to providers. `parameters` is a plain JSON Schema mapping."""
import types
import typing as ta

from omcore import cached
from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import lang
from omcore import reflect as rfl


##


@dc.dataclass(frozen=True)
class ToolDtype(lang.Abstract, lang.Sealed):
    @classmethod
    def of(cls, obj: ta.Any) -> ToolDtype:
        if isinstance(obj, ToolDtype):
            return obj

        elif isinstance(obj, str):
            return PrimitiveToolDtype(obj)

        else:
            return PrimitiveToolDtype.of(obj)


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class PrimitiveToolDtype(ToolDtype):
    type: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.type)

    @classmethod
    def of(cls, obj: ta.Any) -> PrimitiveToolDtype:
        if isinstance(obj, PrimitiveToolDtype):
            return obj

        try:
            return PRIMITIVE_TOOL_DTYPE_MAP[obj]
        except KeyError:
            pass

        rty = rfl.reflect_type(obj)

        if isinstance(rty, rfl.AnyType):
            return PRIMITIVE_TOOL_DTYPE_MAP[ta.Any]

        if (pty := rfl.get_runtime_type_or_none(rty)) is not None:
            return PRIMITIVE_TOOL_DTYPE_MAP.get(pty, OBJECT_PRIMITIVE_TOOL_DTYPE)

        raise TypeError(rty)


OBJECT_PRIMITIVE_TOOL_DTYPE = PrimitiveToolDtype('object')

NULL_PRIMITIVE_TOOL_DTYPE = PrimitiveToolDtype('null')

PRIMITIVE_TOOL_DTYPE_MAP: ta.Mapping[ta.Any, PrimitiveToolDtype] = {
    int: PrimitiveToolDtype('integer'),
    float: PrimitiveToolDtype('number'),
    str: PrimitiveToolDtype('string'),
    bool: PrimitiveToolDtype('boolean'),
    types.NoneType: NULL_PRIMITIVE_TOOL_DTYPE,

    ta.Any: PrimitiveToolDtype('any'),
}


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class UnionToolDtype(ToolDtype):
    args: ta.Sequence[ToolDtype]

    def __post_init__(self) -> None:
        check.arg(len(self.args) > 1)
        check.unique(self.args)
        check.not_in(NULL_PRIMITIVE_TOOL_DTYPE, self.args)


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class NullableToolDtype(ToolDtype):
    type: ToolDtype


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class SequenceToolDtype(ToolDtype):
    element: ToolDtype


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class MappingToolDtype(ToolDtype):
    key: ToolDtype
    value: ToolDtype


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class TupleToolDtype(ToolDtype):
    elements: ta.Sequence[ToolDtype]


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class EnumToolDtype(ToolDtype):
    type: ToolDtype
    values: ta.Sequence[ta.Any]


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class ObjectToolDtype(ToolDtype):
    fields: ta.Mapping[str, ToolDtype]


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class ToolParam:
    name: str = dc.xfield(coerce=check.non_empty_str)
    description: str | None = None
    type: ToolDtype
    optional: bool = dc.xfield(False, repr_fn=lang.truthy_repr)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class Tool:
    name: str = dc.xfield(coerce=check.non_empty_str)
    description: str | None = None

    params: ta.Sequence[ToolParam] = ()
    allow_additional_params: bool | None = None

    return_type: ToolDtype | None = None
    return_description: str | None = None

    @cached.property
    @dc.init
    def params_by_name(self) -> ta.Mapping[str, ToolParam]:
        return col.make_map(((p.name, p) for p in self.params), strict=True)
