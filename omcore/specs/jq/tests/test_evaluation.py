import itertools

import pytest

from ..errors import JqCycleError
from ..errors import JqNameError
from ..errors import JqRecursionError
from ..errors import JqTypeError
from ..options import JqRuntimeOptions
from ..program import compile_jq


##


def evaluate(source, value=None, **kwargs):
    return list(compile_jq(source).evaluate(value, **kwargs))


def test_generator_composition_and_binary_order():
    assert evaluate('(1, 2) | (., . + 10)') == [1, 11, 2, 12]
    assert evaluate('(1, 2) + (10, 20)') == [11, 12, 21, 22]
    assert evaluate('(false, true) and (false, true)') == [False, False, True]
    assert evaluate('(true, false) or (false, true)') == [True, False, True]
    assert evaluate('(false, null, 1, 2) // 9') == [1, 2]
    assert evaluate('(false, empty) // 9') == [9]


def test_navigation_construction_and_truth():
    value = {
        'items': [
            {'id': 1, 'name': 'a', 'active': True},
            {'id': 2, 'name': 'b', 'active': False},
        ],
    }
    assert evaluate('[.items[] | {id, name}]', value) == [[
        {'id': 1, 'name': 'a'},
        {'id': 2, 'name': 'b'},
    ]]
    assert evaluate('if 0 then "yes" else "no" end') == ['yes']
    assert evaluate('.missing?') == [None]
    assert evaluate('.[]?', 1) == []


def test_variables_functions_and_interpolation():
    assert evaluate('. as $root | .items[] | [$root.name, .]', {'name': 'n', 'items': [1, 2]}) == [
        ['n', 1],
        ['n', 2],
    ]
    assert evaluate('def twice(f): f, f; twice(.name)', {'name': 'x'}) == ['x', 'x']
    assert evaluate('def plus($x): . + $x; plus(1, 2)', 10) == [11, 12]
    assert evaluate(r'"x=\((1, 2))"') == ['x=1', 'x=2']


def test_reduce_and_foreach():
    assert evaluate('reduce .[] as $x (0; . + $x)', [1, 2, 3]) == [6]
    assert evaluate('foreach .[] as $x (0; . + $x)', [1, 2, 3]) == [1, 3, 6]
    assert evaluate('reduce .[] as $x ((0, 10); . + $x)', [1, 2]) == [3, 13]
    assert evaluate('reduce (1, 2) as $x (0; . + $x, . - $x)') == [-3]


def test_try_and_lexical_break():
    assert evaluate('try (1 + "x") catch .') == ['cannot add number and string']
    assert evaluate('try (1 + "x")') == []
    assert evaluate('label $out | (1, break $out, 2)') == [1]
    assert evaluate('try (label $out | break $out) catch "caught"') == []
    with pytest.raises(JqNameError):
        compile_jq('break $missing')


def test_paths_and_assignment_copy_on_write():
    source = {'a': {'x': 1}, 'b': {'x': 2}, 'untouched': []}
    result = evaluate('(.a.x, .b.x) = range(3)', source)
    assert result == [
        {'a': {'x': 0}, 'b': {'x': 0}, 'untouched': []},
        {'a': {'x': 1}, 'b': {'x': 1}, 'untouched': []},
        {'a': {'x': 2}, 'b': {'x': 2}, 'untouched': []},
    ]
    assert all(item['untouched'] is source['untouched'] for item in result)
    assert source == {'a': {'x': 1}, 'b': {'x': 2}, 'untouched': []}

    assert evaluate('.items[].enabled = true', {'items': [{}, {}]}) == [
        {'items': [{'enabled': True}, {'enabled': True}]},
    ]
    assert evaluate('.foo |= empty', {'foo': 1, 'bar': 2}) == [{'bar': 2}]
    assert evaluate('.a += (1, 2)', {'a': 10}) == [{'a': 11}, {'a': 12}]
    assert evaluate('.a += .b', {'a': 1, 'b': 2}) == [{'a': 3, 'b': 2}]
    assert evaluate('.a += empty', {'a': 10}) == []
    assert evaluate('.[] |= empty', [0, 1, 2, 3]) == [[]]
    assert evaluate('(.[] | select(. % 2 == 0)) |= empty', [0, 1, 2, 3]) == [[1, 3]]
    assert evaluate('path(.a[2].b)', None) == [['a', 2, 'b']]
    assert evaluate('setpath(["a", 1]; 7)', None) == [{'a': [None, 7]}]
    assert evaluate('delpaths([[0], [2]])', [0, 1, 2, 3]) == [[1, 3]]


def test_structural_sharing_across_outputs():
    large = [{'index': index} for index in range(1000)]
    first, second = evaluate('{foo: .}, {bar: .}', large)
    assert first['foo'] is large
    assert second['bar'] is large
    assert first['foo'] is second['bar']


def test_stable_outputs_and_aliased_input_copy_on_write():
    shared = [{'value': 1}]
    source: dict[str, object] = {'a': shared, 'b': shared, 'untouched': {'large': list(range(1000))}}
    iterator = compile_jq('(.a[0].value, .new) = range(3)').evaluate(source)
    first = next(iterator)
    second = next(iterator)
    assert first['a'][0]['value'] == 0
    assert second['a'][0]['value'] == 1
    list(iterator)
    assert first['a'][0]['value'] == 0
    assert first['a'] is not shared
    assert first['b'] is shared
    assert first['untouched'] is source['untouched']
    assert shared[0]['value'] == 1


def test_shared_outer_input_source():
    program = compile_jq('[., input]')
    assert list(program.run([1, 2, 3, 4])) == [[1, 2], [3, 4]]
    assert list(program.run([1, 2], null_input=True)) == [[None, 1]]


def test_iterative_controls_and_user_recursion_guard():
    assert list(itertools.islice(compile_jq('repeat(1)').evaluate(None), 4)) == [1, 1, 1, 1]
    assert evaluate('while(. < 4; . + 1)', 1) == [1, 2, 3]
    assert evaluate('until(. >= 4; . + 1)', 1) == [4]
    assert evaluate('recurse(.[]?)', [1, [2]]) == [[1, [2]], 1, [2], 2]

    program = compile_jq('def recurse_user: recurse_user; recurse_user')
    with pytest.raises(JqRecursionError):
        list(program.evaluate(None, runtime_options=JqRuntimeOptions(max_recursion_depth=8)))


def test_numeric_indexing_slicing_and_operator_edges():
    assert evaluate('.[1.9], .[-1.9], .[1.1:2.1]', [10, 20, 30, 40]) == [20, 40, [20, 30]]
    assert evaluate('has(1.9), has(-1.9)', [10, 20, 30]) == [True, False]
    assert evaluate('[-5.9 % 2.1, 5.9 % -2.1, 1.9 % 1]') == [[-1, 1, 0]]
    assert evaluate('"abc" / ""') == [['a', 'b', 'c']]
    assert evaluate('1e308 * 1e308') == [pytest.approx(1.7976931348623157e308)]


def test_input_validation_and_cycle_detection():
    unsupported = object()
    with pytest.raises(JqTypeError):
        evaluate('.', unsupported)
    with pytest.raises(JqTypeError):
        evaluate('.[]', [unsupported])

    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(JqCycleError):
        evaluate('..', cyclic)


def test_builtin_basics_and_tostream():
    assert evaluate('[type, length, keys]', {'b': 1, 'a': 2}) == [['object', 2, ['a', 'b']]]
    assert evaluate('contains({a: 1})', {'a': 1, 'b': 2}) == [True]
    assert evaluate('"a,b" | split(",")') == [['a', 'b']]
    assert evaluate('"x" * 2.9, 3 * "y", "z" * -1') == ['xx', 'yyy', None]
    assert evaluate('[65.9, -1, 55296] | implode') == ['A��']
    with pytest.raises(JqTypeError):
        evaluate('[true] | implode')
    assert evaluate('tostream', ['a', ['b']]) == [
        [[0], 'a'],
        [[1, 0], 'b'],
        [[1, 0]],
        [[1]],
    ]
