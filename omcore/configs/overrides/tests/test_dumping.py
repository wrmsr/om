import json

import pytest

from ..applying import apply_overrides
from ..dumping import dump_overrides
from ..dumping import dump_tree
from ..shapes import ListShape
from ..shapes import MapShape
from ..shapes import ObjectShape
from ..shapes import OptionalShape
from ..shapes import ScalarShape
from ..shapes import TaggedShape
from ..shapes import UnknownShape


TREE = {
    'name': 'm',
    'version': '1.10',
    'count': 5,
    'lr': 1e-05,
    'big': 1e+16,
    'on': True,
    'dropout': None,
    'label': None,
    'opt': {'adam': {'lr': 0.001, 'betas': [0.9, 0.99]}},
    'layers': [
        {'name': 'enc', 'dim': 8},
        {'name': '007', 'dim': 16},
    ],
    'empty_map': {},
    'empty_list': [],
    'weird': {
        'a b': 1,
        '0': 'zero',
        'x.y': [[1, 'two'], []],
        '': 'empty key',
    },
    'strs': [
        '',
        ' padded ',
        'null',
        'true',
        '5',
        '-1.5e3',
        'Infinity',
        '{a: 1}',
        '[a-z]+',
        '"quoted"',
        "it's",
        '@file',
        'a=b',
        'two words, and a comma',
        'multi\nline',
        'plain',
        '2026-01-01',
        '/removed',
    ],
    'floats': [float('inf'), float('-inf'), 0., -0.5, 1e300],
}

STR = ScalarShape(str)

SHAPE = ObjectShape(
    {
        'name': STR,
        'version': STR,
        'count': ScalarShape(int),
        'lr': ScalarShape(float),
        'on': ScalarShape(bool),
        'dropout': OptionalShape(ScalarShape(float)),
        'label': OptionalShape(STR),
        'opt': TaggedShape({'adam': ObjectShape({'lr': ScalarShape(float), 'betas': ListShape(ScalarShape(float))})}),
        'layers': ListShape(ObjectShape({'name': STR, 'dim': ScalarShape(int)})),
        'strs': ListShape(STR),
        'weird': MapShape(UnknownShape()),
    },
    open=True,
)


def test_dump():
    assert list(dump_overrides({
        'name': 'm',
        'version': '1.10',
        'opt': {'adam': {'lr': 0.001, 'betas': [0.9, 0.99]}},
        'layers': [{'name': 'enc', 'on': True}, {'name': 'a b', 'on': False}],
        'dropout': None,
        'extra': {},
        'tags': [],
        'k 2': {'0': 1},
    })) == [
        'name=m',
        'version="1.10"',
        'opt.adam.lr=0.001',
        'opt.adam.betas.0=0.9',
        'opt.adam.betas.1=0.99',
        'layers.0.name=enc',
        'layers.0.on=true',
        'layers.1.name=a b',
        'layers.1.on=false',
        'dropout=null',
        'extra={}',
        'tags=[]',
        '["k 2"].0=1',
    ]

    assert list(dump_overrides({})) == ['={}']
    assert list(dump_overrides([1, 'x'])) == ['[0]=1', '[1]=x']
    assert list(dump_overrides(5)) == ['=5']


def test_dump_quotes_only_as_shape_requires():
    s = ObjectShape({'a': STR, 'b': OptionalShape(STR), 'c': ScalarShape(int)}, open=True)
    tree = {'a': '1.10', 'b': '5', 'c': 5, 'd': '5'}
    assert list(dump_overrides(tree, s)) == ['a=1.10', 'b=5', 'c=5', 'd="5"']
    assert list(dump_overrides({'a': 'null', 'b': 'null'}, s)) == ['a=null', 'b="null"']
    assert list(dump_overrides({'a': 'true', 'b': ''}, s)) == ['a=true', 'b=""']


@pytest.mark.parametrize('shape', [None, SHAPE])
def test_dump_lines_are_no_op_overrides(shape):
    lines = list(dump_overrides(TREE, shape))
    assert len(lines) > 40

    def norm(v):
        return json.dumps(v, sort_keys=True)

    for line in lines:
        assert '\n' not in line
        assert norm(apply_overrides(TREE, [line], shape, guess_unknown=True)) == norm(TREE), line

    assert norm(apply_overrides(TREE, lines, shape, guess_unknown=True)) == norm(TREE)


def test_dump_tolerates_trees_at_odds_with_their_shape():
    s = ObjectShape({'a': ListShape(STR), 'b': ObjectShape({'x': STR})})
    assert list(dump_overrides({'a': {'k': '5'}, 'b': {'y': '5'}, 'c': '5'}, s)) == ['a.k="5"', 'b.y="5"', 'c="5"']


def test_dump_tree():
    tree = {'a': {'b': [1, 'x']}}
    assert dump_tree(tree) == 'a.b.0=1\na.b.1=x'
    assert dump_tree(tree, 'overrides', shape=ObjectShape({'a': MapShape(ListShape(STR))})) == 'a.b.0=1\na.b.1=x'
    assert json.loads(dump_tree(tree, 'json')) == tree

    with pytest.raises(ValueError):  # noqa
        dump_tree(tree, 'yaml')  # type: ignore[arg-type]
