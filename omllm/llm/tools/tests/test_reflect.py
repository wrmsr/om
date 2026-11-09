import typing as ta

from omcore import dataclasses as dc

from ...types.tools import EnumToolDtype
from ...types.tools import MappingToolDtype
from ...types.tools import NullableToolDtype
from ...types.tools import ObjectToolDtype
from ...types.tools import PrimitiveToolDtype
from ...types.tools import SequenceToolDtype
from ...types.tools import TupleToolDtype
from ...types.tools import UnionToolDtype
from ..jsonschema import build_tool_dtype_json_schema
from ..reflect import reflect_tool_dtype


STRING = PrimitiveToolDtype('string')
INTEGER = PrimitiveToolDtype('integer')
ANY = PrimitiveToolDtype('any')


def test_primitives():
    assert reflect_tool_dtype(str) == STRING
    assert reflect_tool_dtype(int) == INTEGER
    assert reflect_tool_dtype(float) == PrimitiveToolDtype('number')
    assert reflect_tool_dtype(bool) == PrimitiveToolDtype('boolean')
    assert reflect_tool_dtype(ta.Any) == ANY


def test_unions_and_optionals():
    assert reflect_tool_dtype(int | None) == NullableToolDtype(INTEGER)
    assert reflect_tool_dtype(int | str) == UnionToolDtype((INTEGER, STRING))
    assert reflect_tool_dtype(int | str | None) == NullableToolDtype(UnionToolDtype((INTEGER, STRING)))


def test_literals():
    assert reflect_tool_dtype(ta.Literal['a', 'b']) == EnumToolDtype(STRING, ['a', 'b'])


def test_sequences_and_mappings():
    assert reflect_tool_dtype(list[int]) == SequenceToolDtype(INTEGER)
    assert reflect_tool_dtype(ta.Sequence[str]) == SequenceToolDtype(STRING)
    assert reflect_tool_dtype(dict[str, int]) == MappingToolDtype(STRING, INTEGER)
    assert reflect_tool_dtype(ta.Mapping[str, ta.Any]) == MappingToolDtype(STRING, ANY)


def test_tuples():
    # A tuple of so many is one; any number of one thing is a sequence.
    assert reflect_tool_dtype(tuple[str, int]) == TupleToolDtype((STRING, INTEGER))
    assert reflect_tool_dtype(ta.Tuple[int, str]) == TupleToolDtype((INTEGER, STRING))  # noqa: UP006
    assert reflect_tool_dtype(tuple[()]) == TupleToolDtype(())
    assert reflect_tool_dtype(tuple[str, ...]) == SequenceToolDtype(STRING)
    assert reflect_tool_dtype(tuple) == SequenceToolDtype(ANY)

    assert build_tool_dtype_json_schema(reflect_tool_dtype(tuple[str, int])) == {
        'type': 'array',
        'prefixItems': [{'type': 'string'}, {'type': 'integer'}],
    }


def test_dataclasses():
    @dc.dataclass(frozen=True)
    class Point:
        x: int
        tags: list[str]
        label: str | None = None
        span: tuple[int, int] | None = None

    assert reflect_tool_dtype(Point) == ObjectToolDtype({
        'x': INTEGER,
        'tags': SequenceToolDtype(STRING),
        'label': NullableToolDtype(STRING),
        'span': NullableToolDtype(TupleToolDtype((INTEGER, INTEGER))),
    })
