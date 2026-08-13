"""
TODO:
 - '$schema': 'http://json-schema.org/draft-07/schema#'
"""
from omcore import check

from ..types.tools import EnumToolDtype
from ..types.tools import MappingToolDtype
from ..types.tools import NullableToolDtype
from ..types.tools import ObjectToolDtype
from ..types.tools import PrimitiveToolDtype
from ..types.tools import SequenceToolDtype
from ..types.tools import Tool
from ..types.tools import ToolDtype
from ..types.tools import TupleToolDtype
from ..types.tools import UnionToolDtype


##


class ToolJsonschemaBuilder:
    def build_tool_dtype(self, t: ToolDtype) -> dict:
        if isinstance(t, PrimitiveToolDtype):
            return {'type': t.type}

        if isinstance(t, UnionToolDtype):
            return {
                'anyOf': [self.build_tool_dtype(a) for a in t.args],
            }

        if isinstance(t, NullableToolDtype):
            return {
                **self.build_tool_dtype(t.type),
                'nullable': True,
            }

        if isinstance(t, SequenceToolDtype):
            return {
                'type': 'array',
                'items': self.build_tool_dtype(t.element),
            }

        if isinstance(t, MappingToolDtype):
            # FIXME: t.key
            return {
                'type': 'object',
                'additionalProperties': self.build_tool_dtype(t.value),
            }

        if isinstance(t, TupleToolDtype):
            return {
                'type': 'array',
                'prefixItems': [self.build_tool_dtype(e) for e in t.elements],
            }

        if isinstance(t, EnumToolDtype):
            return {
                **self.build_tool_dtype(t.type),
                'enum': list(t.values),
            }

        if isinstance(t, ObjectToolDtype):
            return {
                'type': 'object',
                'properties': {
                    k: self.build_tool_dtype(v)
                    for k, v in t.fields.items()
                },
            }

        raise TypeError(t)

    def build_tool_params(self, ts: Tool) -> dict:
        pr_dct: dict[str, dict] = {}
        req_lst: list[str] | None = None
        if ts.params:
            req_lst = []
            for p in ts.params:
                pr_dct[check.non_empty_str(p.name)] = {
                    **({'description': p.description} if p.description is not None else {}),
                    **(self.build_tool_dtype(p.type) if p.type is not None else {}),
                }
                if not p.optional:
                    req_lst.append(check.non_empty_str(p.name))

        return {
            'type': 'object',
            'properties': pr_dct,
            **({'required': req_lst} if req_lst is not None else {}),
            # By default any additional properties are allowed.
            # https://json-schema.org/understanding-json-schema/reference/object#additionalproperties
            **({'additionalProperties': False} if not ts.allow_additional_params else {}),
        }

    def build_tool(self, ts: Tool) -> dict:
        pa_dct = self.build_tool_params(ts)

        ret_dct = {
            **({'description': ts.return_description} if ts.return_description is not None else {}),
            **({'type': self.build_tool_dtype(ts.return_type)} if ts.return_type is not None else {}),
        }

        return {
            'name': ts.name,
            **({'description': ts.description} if ts.description is not None else {}),
            **({'parameters': pa_dct} if pa_dct else {}),
            **({'return': ret_dct} if ret_dct else {}),
        }


##


def build_tool_dtype_json_schema(t: ToolDtype) -> dict:
    return ToolJsonschemaBuilder().build_tool_dtype(t)


def build_tool_params_json_schema(ts: Tool) -> dict:
    return ToolJsonschemaBuilder().build_tool_params(ts)


def build_tool_json_schema(ts: Tool) -> dict:
    return ToolJsonschemaBuilder().build_tool(ts)
