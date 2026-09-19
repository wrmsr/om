import pytest

from .. import ast
from ..errors import JqParseError
from ..parsing import parse


##


def test_precedence_matches_jq_grammar():
    node = parse('1, 2 | . + 10 // 20')
    assert isinstance(node, ast.Pipe)
    assert isinstance(node.left, ast.Comma)
    assert isinstance(node.right, ast.Alternative)
    assert isinstance(node.right.left, ast.Binary)

    binding = parse('1 // 2 as $x | [$x, .]')
    assert isinstance(binding, ast.Alternative)
    assert isinstance(binding.right, ast.Binding)


def test_navigation_construction_and_interpolation():
    node = parse(r'[.items[] | {id, name: .name, ("x"): "v=\(.value)"}]')
    assert isinstance(node, ast.Array)
    assert isinstance(node.value, ast.Pipe)
    assert isinstance(node.value.right, ast.Object)
    assert len(node.value.right.members) == 3
    string = node.value.right.members[2].value
    assert isinstance(string, ast.String)
    assert isinstance(string.parts[1], ast.Index)


def test_def_bind_reduce_foreach_and_control():
    source = """
        def twice(f): f, f;
        def addn($n): . + $n;
        . as $root |
        reduce .items[] as $x (0; . + $x) |
        foreach .[] as $x (0; . + $x; {root: $root, value: .})
    """
    node = parse(source)
    assert isinstance(node, ast.FunctionDefinition)
    assert not node.parameters[0].binding
    assert isinstance(node.next, ast.FunctionDefinition)
    assert node.next.parameters[0].binding
    assert isinstance(node.next.next, ast.Binding)


def test_try_labels_assignments_and_slices():
    node = parse('label $out | try ((.a[1:-1], .b?) |= . + 1) catch break $out')
    assert isinstance(node, ast.Label)
    assert isinstance(node.body, ast.Try)
    assert isinstance(node.body.value, ast.Assignment)
    assert isinstance(node.body.handler, ast.Break)


@pytest.mark.parametrize('source', ['', 'if . then 1', '{foo:', 'reduce .[] as $x (0)'])
def test_parse_errors(source):
    with pytest.raises(JqParseError):
        parse(source)
