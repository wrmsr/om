import textwrap

import pytest

from .. import items
from .. import make
from .. import rendering


@pytest.mark.skip_unless_alone
def test_open_dot():
    src = textwrap.dedent("""
    digraph G {
        a;
        b;
        a -> b;
    }
    """)
    rendering.open_dot(src)


def test_dot():
    assert rendering.render(items.Value.of('hi')) == 'hi'
    assert rendering.render(items.Value.of([['a', 'b'], ['c', 'd']])) == (
        '<table><tr><td>a</td><td>b</td></tr><tr><td>c</td><td>d</td></tr></table>'
    )

    def print_and_open(no):
        print(no)
        gv = rendering.render(no)
        print(gv)
        # dot.open_dot(gv)

    print_and_open(items.Graph(
        [
            items.Node('a', {'shape': 'box'}),
            items.Node('b', {'label': [['a', 'b'], ['c', 'd']]}),
            items.Edge('a', 'b'),
        ],
    ))


def test_make_simple_with_one_shot_successors():
    graph = make.make_simple({
        'a': iter(['b']),
    })

    assert items.Edge('a', 'b') in graph.stmts


def test_id_escaping():
    assert rendering.render(items.Id('a"b\\c\r\nd')) == '"a\\"b\\\\c\\r\\nd"'
