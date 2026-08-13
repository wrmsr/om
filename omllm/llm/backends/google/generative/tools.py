"""https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ....types.tools import EnumToolDtype
from ....types.tools import MappingToolDtype
from ....types.tools import NullableToolDtype
from ....types.tools import ObjectToolDtype
from ....types.tools import PrimitiveToolDtype
from ....types.tools import SequenceToolDtype
from ....types.tools import Tool
from ....types.tools import ToolDtype
from ....types.tools import TupleToolDtype
from ....types.tools import UnionToolDtype


##


def _shallow_dc_asdict_not_none(o: ta.Any) -> dict[str, ta.Any]:
    return {k: v for k, v in dc.shallow_asdict(o).items() if v is not None}


PT_TYPE_BY_PRIMITIVE_TYPE: ta.Mapping[str, str] = {
    'string': 'STRING',
    'number': 'NUMBER',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'array': 'ARRAY',
    'null': 'NULL',
}


class ToolSchemaBuilder:
    def build_tool_dtype(self, t: ToolDtype) -> dict:
        if isinstance(t, PrimitiveToolDtype):
            return {'type': PT_TYPE_BY_PRIMITIVE_TYPE[t.type]}

        if isinstance(t, UnionToolDtype):
            return {
                'any_of': [self.build_tool_dtype(a) for a in t.args],
            }

        if isinstance(t, NullableToolDtype):
            return {
                **self.build_tool_dtype(t.type),
                'nullable': True,
            }

        if isinstance(t, SequenceToolDtype):
            return {
                'type': 'ARRAY',
                'items': self.build_tool_dtype(t.element),
            }

        if isinstance(t, MappingToolDtype):
            # FIXME: t.key
            # return {
            #     'type': 'object',
            #     'additionalProperties': self.build_tool_dtype(t.value),
            # }
            raise NotImplementedError

        if isinstance(t, TupleToolDtype):
            # return {
            #     'type': 'array',
            #     'prefixItems': [self.build_tool_dtype(e) for e in t.elements],
            # }
            raise NotImplementedError

        if isinstance(t, EnumToolDtype):
            return {
                **self.build_tool_dtype(t.type),
                'enum': list(t.values),
            }

        if isinstance(t, ObjectToolDtype):
            return {
                'type': 'OBJECT',
                'properties': {
                    k: self.build_tool_dtype(v)
                    for k, v in t.fields.items()
                },
            }

        raise TypeError(t)

    def build_tool_params(self, ts: Tool) -> dict:
        pr_dct: dict[str, dict] | None = None
        req_lst: list[str] | None = None
        if ts.params is not None:
            pr_dct = {}
            req_lst = []
            for p in ts.params or []:
                pr_dct[check.non_empty_str(p.name)] = {
                    **({'description': p.description} if p.description is not None else {}),
                    **(self.build_tool_dtype(p.type) if p.type is not None else {}),
                }
                if not p.optional:
                    req_lst.append(check.non_empty_str(p.name))

        return {
            'type': 'OBJECT',
            **({'properties': pr_dct} if pr_dct is not None else {}),
            **({'required': req_lst} if req_lst is not None else {}),
        }

    def build_tool(self, ts: Tool) -> dict:
        ret_dct = {
            **({'description': ts.return_description} if ts.return_description is not None else {}),
            **(self.build_tool_dtype(ts.return_type) if ts.return_type is not None else {}),
        }

        return {
            'name': check.non_empty_str(ts.name),
            'description': ts.description if ts.description is not None else None,
            'behavior': 'BLOCKING',
            'parameters': self.build_tool_params(ts) if ts.params else None,
            **({'response': ret_dct} if ret_dct else {}),
        }


##


def build_tool_spec_params_schema(ts: Tool) -> dict:
    return ToolSchemaBuilder().build_tool_params(ts)


def build_tool_spec_schema(ts: Tool) -> dict:
    return ToolSchemaBuilder().build_tool(ts)
