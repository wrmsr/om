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
    'object': 'OBJECT',
    'null': 'NULL',
}

# Gemini's schema has no untyped value: the closest it can be told is any of the types a json value may have, less an
# array, whose items it would then have to be told as well.
ANY_SCHEMA: ta.Mapping[str, ta.Any] = {
    'anyOf': [
        {'type': 'STRING'},
        {'type': 'NUMBER'},
        {'type': 'BOOLEAN'},
        {'type': 'OBJECT'},
    ],
}


class ToolSchemaBuilder:
    def build_tool_dtype(self, t: ToolDtype) -> dict:
        if isinstance(t, PrimitiveToolDtype):
            if t.type == 'any':
                return dict(ANY_SCHEMA)
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
            # Gemini's schema has no additionalProperties: a mapping is an object whose keys it is not told, and the
            # parameter's description is where to say what they and their values are.
            return {'type': 'OBJECT'}

        if isinstance(t, TupleToolDtype):
            # Nor prefixItems: a tuple is an array of exactly so many items, each of any of the element types.
            item_schemas: list[dict] = []
            for e in t.elements:
                if (s := self.build_tool_dtype(e)) not in item_schemas:
                    item_schemas.append(s)

            return {
                'type': 'ARRAY',
                'items': (
                    item_schemas[0] if len(item_schemas) == 1 else
                    {'anyOf': item_schemas} if item_schemas else
                    dict(ANY_SCHEMA)
                ),
                'minItems': len(t.elements),
                'maxItems': len(t.elements),
            }

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
