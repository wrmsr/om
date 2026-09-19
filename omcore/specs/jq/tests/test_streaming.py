import itertools

import pytest

from ..errors import JqStructureError
from ..events import BeginArray
from ..events import BeginObject
from ..events import EndArray
from ..events import EndObject
from ..events import ObjectKey
from ..events import Scalar
from ..jsonstream import parse_json_structural_events
from ..options import JqValueOptions
from ..streaming import encode_jq_stream
from ..streaming import tostream
from ..values import JqValueOps


##


@pytest.mark.parametrize(('value', 'expected'), [
    (['a', ['b']], [[[0], 'a'], [[1, 0], 'b'], [[1, 0]], [[1]]]),
    ({'a': 1}, [[['a'], 1], [['a']]]),
    ([[]], [[[0], []], [[0]]]),
    ({}, [[[], {}]]),
    ([], [[[], []]]),
    ({'a': {'b': 2}}, [[['a', 'b'], 2], [['a', 'b']], [['a']]]),
    (7, [[[], 7]]),
])
def test_tostream_examples(value, expected):
    assert list(tostream(value)) == expected


def test_json_adapter_converges_across_chunks():
    text = '{"emoji":"\ud83c\udf0d","nested":[[],{"x":1}]} 42'
    expected = list(encode_jq_stream(parse_json_structural_events(text)))
    chunks = [text[index:index + 1] for index in range(len(text))]
    assert list(encode_jq_stream(parse_json_structural_events(chunks))) == expected


def test_multiple_roots_and_lazy_infinite_events():
    def events():
        value = 0
        while True:
            yield Scalar(value)
            value += 1

    assert list(itertools.islice(encode_jq_stream(events()), 4)) == [
        [[], 0],
        [[], 1],
        [[], 2],
        [[], 3],
    ]


def test_stringified_object_key_collisions_are_deterministic():
    def stringify(key):
        assert isinstance(key, int)
        return str(key % 2)

    ops = JqValueOps(JqValueOptions(object_key_stringifier=stringify))
    assert list(tostream({1: 'first', 3: 'last'}, value_ops=ops)) == [
        [['1'], 'first'],
        [['1'], 'last'],
        [['1']],
    ]


@pytest.mark.parametrize('events', [
    [EndArray()],
    [BeginArray(), EndObject()],
    [BeginObject(), Scalar(1), EndObject()],
    [ObjectKey('x')],
    [BeginObject(), ObjectKey('x'), EndObject()],
    [BeginArray()],
    [Scalar([])],
    [Scalar(object())],
])
def test_malformed_event_streams(events):
    with pytest.raises(JqStructureError):
        list(encode_jq_stream(events))
