import itertools

import pytest

from ..errors import JqRegexError
from ..errors import JqRegexUnavailableError
from ..program import compile_jq
from ..regexoptional import RegexPackageEngine
from ..streaming import tostream


##


def evaluate(source, value=None, **kwargs):
    return list(compile_jq(source, **kwargs).evaluate(value))


def test_collection_prelude():
    values = [{'key': 2, 'value': 'a'}, {'key': 1}, {'key': 2, 'value': 'b'}]
    assert evaluate('map(.key)', values) == [[2, 1, 2]]
    assert evaluate('map_values(. + 1)', {'a': 1, 'b': 2}) == [{'a': 2, 'b': 3}]
    assert evaluate('sort_by(.key)', values) == [[values[1], values[0], values[2]]]
    assert evaluate('group_by(.key)', values) == [[[values[1]], [values[0], values[2]]]]
    assert evaluate('unique_by(.key)', values) == [[values[1], values[0]]]
    assert evaluate('min_by(.key), max_by(.key)', values) == [values[1], values[2]]
    tied = [{'key': 1, 'value': 'first'}, {'key': 1, 'value': 'last'}]
    assert evaluate('min_by(.key), max_by(.key)', tied) == [tied[0], tied[1]]
    assert evaluate('add', [1, 2, 3]) == [6]
    assert evaluate('flatten, flatten(1)', [1, [2, [3]]]) == [[1, 2, 3], [1, 2, [3]]]


def test_object_and_sequence_prelude():
    assert evaluate('to_entries | from_entries', {'b': 2, 'a': 1}) == [{'b': 2, 'a': 1}]
    assert evaluate('with_entries(.value += 1)', {'a': 1, 'b': 2}) == [{'a': 2, 'b': 3}]
    assert evaluate('indices("ana")', 'bananana') == [[1, 3, 5]]
    assert evaluate('index(2), rindex(2)', [1, 2, 3, 2]) == [1, 3]
    assert evaluate('[paths]', {'a': [1, {'b': 2}]}) == [[
        ['a'],
        ['a', 0],
        ['a', 1],
        ['a', 1, 'b'],
    ]]
    assert evaluate('join("-")', ['a', 1, None, False]) == ['a-1--false']
    assert evaluate('indices(""), indices("ana")', 'bananana') == [[], [1, 3, 5]]
    assert evaluate('indices([])', [1, 2, 1]) == [[]]


def test_bounded_and_iterative_generators():
    assert evaluate('[limit(3; range(10))]') == [[0, 1, 2]]
    assert evaluate('[skip(2; range(5))]') == [[2, 3, 4]]
    assert evaluate('first(range(5)), nth(2; range(5)), isempty(empty)') == [0, 2, True]
    assert evaluate('last(range(5)), last(empty)') == [4, None]
    assert evaluate('all(. > 0), any(. > 2)', [1, 2, 3]) == [True, True]
    assert list(itertools.islice(compile_jq('limit(4; repeat(7))').evaluate(None), 10)) == [7, 7, 7, 7]
    assert evaluate('recurse(.[]?; type == "array")', [1, [2, [3]]]) == [[1, [2, [3]]], [2, [3]], [3]]


def test_inputs_and_stream_reconstruction():
    assert list(compile_jq('[inputs]').run([1, 2, 3, 4])) == [[2, 3, 4]]
    values = [None, [], {}, [1, {'a': 2}], {'a': [1, 2]}]
    for value in values:
        stream = list(tostream(value))
        assert evaluate('fromstream(.[])', stream) == [value]

    stream = list(tostream({'a': [1, 2]}))
    assert list(compile_jq('1 | [truncate_stream($stream[])]').evaluate(None, variables={'stream': stream})) == [[
        [[0], 1],
        [[1], 2],
        [[1]],
    ]]


def test_regex_result_shapes_and_operations():
    assert evaluate('test("^foo"; "i")', 'Foobar') == [True]
    assert evaluate('match("(?P<x>a)(z)?")', 'ab') == [{
        'offset': 0,
        'length': 1,
        'string': 'a',
        'captures': [
            {'offset': 0, 'length': 1, 'string': 'a', 'name': 'x'},
            {'offset': -1, 'length': 0, 'string': None, 'name': None},
        ],
    }]
    assert evaluate('capture("(?P<name>[a-z]+)-(?P<n>[0-9]+)")', 'abc-12') == [
        {'name': 'abc', 'n': '12'},
    ]
    assert evaluate('[scan("[a-z]+")]', '1ab2cd') == [['ab', 'cd']]
    assert evaluate('[splits(",")]', 'a,b,') == [['a', 'b', '']]
    assert evaluate('split(","; "")', 'a,b,') == [['a', 'b', '']]
    assert evaluate('sub("[0-9]+"; "X"), gsub("[0-9]+"; "X")', 'a12b3') == ['aXb3', 'aXbX']


def test_regex_backends_and_explicit_disable():
    with pytest.raises(JqRegexUnavailableError):
        evaluate('test("x")', 'x', regex_engine=None)
    with pytest.raises(JqRegexError):
        evaluate('test("x"; "q")', 'x')

    pytest.importorskip('regex')
    assert evaluate('test("^x")', 'xyz', regex_engine=RegexPackageEngine()) == [True]
