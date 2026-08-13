import collections.abc
import typing as ta

from omcore import check
from omcore import collections as col
from omcore import dataclasses as dc
from omcore import reflect as rfl

from ..types.tools import EnumToolDtype
from ..types.tools import MappingToolDtype
from ..types.tools import NullableToolDtype
from ..types.tools import ObjectToolDtype
from ..types.tools import PrimitiveToolDtype
from ..types.tools import SequenceToolDtype
from ..types.tools import ToolDtype
from ..types.tools import TupleToolDtype
from ..types.tools import UnionToolDtype


##


class ToolDtypeReflector:
    def reflect_union_type(self, *args: rfl.Type) -> ToolDtype:
        check.unique(args)

        if any(isinstance(a, rfl.NoneType) for a in args):
            is_nullable = True
            args = tuple(a for a in args if not isinstance(a, rfl.NoneType))
        else:
            is_nullable = False

        check.not_empty(args)

        ret: ToolDtype
        if len(args) == 1:
            ret = self.reflect_type(check.single(args))

        else:
            ret = UnionToolDtype(tuple(
                self.reflect_type(a_rty)
                for a_rty in args
            ))

        if is_nullable:
            ret = NullableToolDtype(ret)

        return ret

    SEQUENCE_TYPES: ta.Container[type] = frozenset([
        collections.abc.Sequence,
        list,
    ])

    MAPPING_TYPES: ta.Container[type] = frozenset([
        collections.abc.Mapping,
        dict,
    ])

    def reflect_type(self, rty: rfl.Type) -> ToolDtype:
        ty = rty.runtime_type

        if isinstance(rty, rfl.Instance) and ty is not None and dc.is_dataclass(ty):
            return ObjectToolDtype({
                f.name: self.reflect_type(rfl.reflect_type(f.type))
                for f in dc.fields(ty)
            })

        if isinstance(rty, rfl.AnyType):
            return PrimitiveToolDtype.of(rty)

        if (lvs := rfl.get_literal_values_or_none(rty)) is not None:
            return EnumToolDtype(
                self.reflect_union_type(*col.unique(
                    rfl.typeof(lv)
                    for lv in lvs
                )),
                lvs,
            )

        if isinstance(rty, rfl.UnionType):
            return self.reflect_union_type(*rty.items)

        if isinstance(rty, rfl.Instance):
            if not rty.args:
                return PrimitiveToolDtype.of(rty)

            g_cls = check.isinstance(rty.type.runtime_object, type)

            if g_cls in self.SEQUENCE_TYPES:
                a_rty = check.single(rty.args)
                return SequenceToolDtype(self.reflect_type(a_rty))

            if g_cls in self.MAPPING_TYPES:
                k_rty, v_rty = rty.args
                return MappingToolDtype(
                    self.reflect_type(k_rty),
                    self.reflect_type(v_rty),
                )

            if g_cls is tuple:
                return TupleToolDtype(tuple(
                    self.reflect_type(a_rty)
                    for a_rty in rty.args
                ))

        raise TypeError(rty)


##


def reflect_tool_dtype(ty: object) -> ToolDtype:
    rty = rfl.reflect_type(ty)

    return ToolDtypeReflector().reflect_type(rty)
