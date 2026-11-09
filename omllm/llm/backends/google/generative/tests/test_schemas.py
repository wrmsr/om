import typing as ta

from .....tools.reflect import reflect_tool_dtype
from .....types.tools import MappingToolDtype
from .....types.tools import ObjectToolDtype
from .....types.tools import PrimitiveToolDtype
from .....types.tools import Tool
from .....types.tools import ToolDtype
from .....types.tools import ToolParam
from .....types.tools import TupleToolDtype
from ..tools import ANY_SCHEMA
from ..tools import ToolSchemaBuilder
from ..tools import build_tool_spec_schema


def _schema(t):
    return ToolSchemaBuilder().build_tool_dtype(t)


def test_objects_and_untyped_values():
    assert _schema(PrimitiveToolDtype('object')) == {'type': 'OBJECT'}
    assert _schema(ToolDtype.of(ta.Any)) == ANY_SCHEMA

    assert _schema(ObjectToolDtype({'a': ToolDtype.of(int), 'b': ToolDtype.of(ta.Any)})) == {
        'type': 'OBJECT',
        'properties': {
            'a': {'type': 'INTEGER'},
            'b': ANY_SCHEMA,
        },
    }


def test_mappings_are_objects_of_untold_keys():
    assert _schema(MappingToolDtype(ToolDtype.of(str), ToolDtype.of(int))) == {'type': 'OBJECT'}
    assert _schema(reflect_tool_dtype(dict[str, int])) == {'type': 'OBJECT'}


def test_tuples_are_arrays_of_exactly_so_many():
    assert _schema(TupleToolDtype([ToolDtype.of(str), ToolDtype.of(str)])) == {
        'type': 'ARRAY',
        'items': {'type': 'STRING'},
        'minItems': 2,
        'maxItems': 2,
    }

    assert _schema(reflect_tool_dtype(tuple[str, int, str])) == {
        'type': 'ARRAY',
        'items': {'anyOf': [{'type': 'STRING'}, {'type': 'INTEGER'}]},
        'minItems': 3,
        'maxItems': 3,
    }

    assert _schema(TupleToolDtype([])) == {
        'type': 'ARRAY',
        'items': ANY_SCHEMA,
        'minItems': 0,
        'maxItems': 0,
    }


def test_a_tool_with_every_kind_of_parameter_declares():
    tool = Tool(
        name='everything',
        description='Takes it all.',
        params=[
            ToolParam(name='s', type=ToolDtype.of(str)),
            ToolParam(name='o', type=PrimitiveToolDtype('object'), optional=True),
            ToolParam(name='a', type=ToolDtype.of(ta.Any), optional=True),
            ToolParam(name='m', type=reflect_tool_dtype(dict[str, str]), optional=True),
            ToolParam(name='t', type=reflect_tool_dtype(tuple[int, int]), optional=True),
        ],
    )

    decl = build_tool_spec_schema(tool)

    assert decl['name'] == 'everything'
    assert decl['parameters']['required'] == ['s']
    assert decl['parameters']['properties']['o'] == {'type': 'OBJECT'}
    assert decl['parameters']['properties']['a'] == ANY_SCHEMA
    assert decl['parameters']['properties']['m'] == {'type': 'OBJECT'}
    assert decl['parameters']['properties']['t']['maxItems'] == 2
