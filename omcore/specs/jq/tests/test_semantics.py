import pytest

from ..errors import JqNameError
from ..errors import JqPathError
from ..program import compile_jq


##


def evaluate(source, value=None, **kwargs):
    return list(compile_jq(source).evaluate(value, **kwargs))


def test_generator_multiplicity_across_language_forms():
    assert evaluate('[{("a", "b"): (1, 2)}]') == [[
        {'a': 1},
        {'a': 2},
        {'b': 1},
        {'b': 2},
    ]]
    assert evaluate('[if (true, false) then "yes" else "no" end]') == [['yes', 'no']]
    assert evaluate(r'["x=\((1, 2))-\((3, 4))"]') == [[
        'x=1-3',
        'x=1-4',
        'x=2-3',
        'x=2-4',
    ]]


def test_function_parameters_and_lexical_scope():
    source = """
        def apply_twice(f): f | f;
        def outer($value):
          def inner: $value;
          inner;
        [apply_twice((. + 1, . + 10)), outer(7)]
    """
    assert evaluate(source, 0) == [[2, 11, 11, 20, 7]]


def test_foreach_branching_and_extract():
    assert evaluate('[foreach (1, 2) as $x ((0, 10); . + $x, . - $x; [$x, .])]') == [[
        [1, 1],
        [1, -1],
        [2, 1],
        [2, -3],
        [1, 11],
        [1, 9],
        [2, 11],
        [2, 7],
    ]]


def test_path_provenance_through_dynamic_selection():
    value = {
        'posts': [
            {'author': 'stedolan', 'comments': ['good']},
            {'author': 'someone', 'comments': ['fine']},
        ],
    }
    source = '(.posts[] | select(.author == "stedolan") | .comments) |= . + ["terrible."]'
    assert evaluate(source, value) == [{
        'posts': [
            {'author': 'stedolan', 'comments': ['good', 'terrible.']},
            {'author': 'someone', 'comments': ['fine']},
        ],
    }]
    assert evaluate('[path(.[] | select(.active) | .name)]', [
        {'active': False, 'name': 'no'},
        {'active': True, 'name': 'yes'},
    ]) == [[[1, 'name']]]


def test_assignment_evaluation_order_uses_shared_input_source():
    program = compile_jq('.[input] = input')
    assert list(program.evaluate(None, inputs=[0, 7])) == [[None, None, None, None, None, None, None, 0]]


def test_nested_errors_and_lexical_breaks():
    assert evaluate('try (try error("inner") catch error(. + "-outer")) catch .') == ['inner-outer']
    assert evaluate('label $outer | label $inner | (1, break $outer, 2)') == [1]
    assert evaluate('try (label $out | break $out) catch "caught"') == []
    with pytest.raises(JqNameError):
        compile_jq('label $out | ., break $missing')


def test_invalid_assignment_path_fails_loudly():
    with pytest.raises(JqPathError):
        evaluate('(. + 1) = 2', 1)
