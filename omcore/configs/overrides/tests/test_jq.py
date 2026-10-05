import typing as ta

import pytest

from ..applying import apply_overrides
from ..errors import OverrideJqError
from ..errors import OverridePathError
from ..errors import OverrideValueError
from ..jq import apply_jq_filter
from ..ops import JqOp
from ..shapes import AnyShape
from ..shapes import ListShape
from ..shapes import MapShape
from ..shapes import ObjectShape
from ..shapes import OptionalShape
from ..shapes import ScalarShape
from ..shapes import Shape
from ..shapes import TaggedShape
from ..shapes import TupleShape
from ..shapes import UnknownShape


STR = ScalarShape(str)
INT = ScalarShape(int)
FLOAT = ScalarShape(float)
BOOL = ScalarShape(bool)

OPT = TaggedShape({
    'adam': ObjectShape({'lr': FLOAT, 'betas': TupleShape([FLOAT, FLOAT])}),
    'sgd': ObjectShape({'lr': FLOAT, 'momentum': FLOAT}),
})

SHAPE = ObjectShape({
    'name': STR,
    'version': STR,
    'debug': BOOL,
    'dropout': OptionalShape(FLOAT),
    'opt': OPT,
    'opt2': OptionalShape(OPT),
    'sched': TaggedShape(
        {
            'cosine': ObjectShape({'t_max': INT}),
            'step': ObjectShape({'gamma': FLOAT, 'size': INT}),
        },
        tag_field='type',
    ),
    'layers': ListShape(ObjectShape({
        'name': STR,
        'dim': INT,
        'tags': ListShape(STR),
    })),
    'extra': MapShape(AnyShape()),
    'secret': UnknownShape('secret'),
})

TREE: ta.Any = {
    'name': 'm',
    'version': '1.0',
    'debug': False,
    'dropout': None,
    'opt': {'adam': {'lr': 0.001, 'betas': [0.9, 0.99]}},
    'opt2': None,
    'sched': {'type': 'cosine', 't_max': 10},
    'layers': [
        {'name': 'enc', 'dim': 8, 'tags': ['a']},
        {'name': 'dec', 'dim': 16, 'tags': []},
    ],
    'extra': {'k': None, 'n': 3},
    'secret': {'a': 1},
}


def jq(source, tree=TREE, shape: Shape | None = SHAPE):
    return apply_jq_filter(tree, source, shape if shape is not None else AnyShape())


def check_plain(v):
    assert type(v) in (dict, list, str, int, float, bool, type(None))
    for e in (v.values() if isinstance(v, dict) else v if isinstance(v, list) else ()):
        check_plain(e)


##


@pytest.mark.parametrize('source', [
    '.',
    '.name = "x"',
    '.opt.adam.lr = 1 | .name = "x"',
    '.opt |= (.adam.lr = 5)',
    '.layers |= map(.dim *= 2)',
    '.layers[0].dim += 1',
    '.layers += [{name: "new"}]',
    'del(.layers[0])',
    'del(.opt.adam.betas[0], .extra.k)',
    '.layers[] |= (.tags += ["t"])',
    '.extra.new.deep = 1',
    'setpath(["opt", "adam", "lr"]; 7)',
    '.layers |= map(select(.dim > 8))',
    'map_values(.)',
    '.layers |= sort_by(.dim) | .layers |= reverse',
    '.layers[1] = .layers[0]',
    '.extra = (. | del(.extra) | del(.secret))',
    '.dropout = (.layers | map(.dim) | add / 100)',
    '. * {name: "y"}',
    '. + {debug: true}',
    'with_entries(.)',
    'walk(.)',
    '.extra.e = [paths | tojson]',
    '.extra.e = [.. | numbers]',
    '.extra.e = (.layers | group_by(.dim > 8) | map(length))',
    '.extra.e = (tojson | fromjson | .layers[1:])',
])
def test_same_results_as_unshaped(source):
    shaped = jq(source)
    assert shaped == jq(source, shape=None)
    check_plain(shaped)


def test_input_is_untouched_and_output_shares_nothing():
    tree: ta.Any = {'layers': [{'name': 'a', 'dim': 1, 'tags': ['t']}], 'extra': {'k': [1]}}
    for source in ['.', '.layers[0].dim = 2', '.extra.j = .extra.k', '. * {extra: {z: 1}}', 'del(.nope)']:
        for shape in [SHAPE, None]:
            out = jq(source, tree, shape)
            assert tree == {'layers': [{'name': 'a', 'dim': 1, 'tags': ['t']}], 'extra': {'k': [1]}}
            assert out is not tree
            assert out['layers'] is not tree['layers']
            assert out['layers'][0]['tags'] is not tree['layers'][0]['tags']
            assert out['extra']['k'] is not tree['extra']['k']
            if 'j' in out['extra']:
                assert out['extra']['j'] is not out['extra']['k']


##


def test_writes_conform():
    assert jq('.dropout = 1')['dropout'] == 1.
    assert type(jq('.dropout = 1')['dropout']) is float
    assert type(jq('.layers[0].dim = 4.0')['layers'][0]['dim']) is int
    assert type(jq('.layers |= map(.dim /= 2)')['layers'][0]['dim']) is int
    assert type(jq('.opt.adam.betas[0] = 1')['opt']['adam']['betas'][0]) is float
    assert jq('.dropout = 1 | .dropout = null')['dropout'] is None
    assert jq('.debug = (.layers | length > 1)')['debug'] is True
    assert jq('.layers += [{name: "new", dim: 2.0}]')['layers'][-1] == {'name': 'new', 'dim': 2}

    for source, match in [
        ('.version = 1.10', r"Expected str at 'version', got number 1\.1"),
        ('.debug = "false"', "Expected bool at 'debug', got string 'false'"),
        ('.name = null', "Expected str at 'name', got null"),
        ('.layers[0].dim = "8"', r"Expected int at 'layers\.0\.dim', got string '8'"),
        ('.layers |= map(.dim /= 3)', r"Expected int at 'layers\.0\.dim', got number"),
        ('.layers += [{name: "new", dim: "x"}]', r"Expected int at 'layers\.2\.dim'"),
        ('.layers[0] = "x"', r"Expected map at 'layers\.0'"),
        ('.layers = {}', "Expected list at 'layers', got a map"),
        ('.layers[0].tags += [1]', r"Expected str at 'layers\.0\.tags\.1'"),
        ('.opt.adam.betas = [1]', 'exactly 2 elements'),
        ('.layers[0] |= (.dim = "x")', r"Expected int at 'layers\.0\.dim'"),
        ('.layers[] |= (.tags = "x")', r"Expected list at 'layers\.0\.tags'"),
        ('.layers[0] += {nmae: "x"}', r"Unknown key 'nmae' at 'layers\.0' - did you mean 'name'"),
        ('.layers[3].name = "pad"', r"Expected map at 'layers\.2', got null"),
    ]:
        with pytest.raises(OverrideValueError, match=match):
            jq(source)


def test_writes_reject_unknown_keys():
    for source, match in [
        ('.vresion = "2"', "Unknown key 'vresion' at the root - did you mean 'version'"),
        ('.layers[0].nmae = "x"', r"Unknown key 'nmae' at 'layers\.0' - did you mean 'name'"),
        ('.layers[] |= (.dmi = 1)', r"Unknown key 'dmi' at 'layers\.0'"),
        ('.opt.adam.momentum = 1', r"Unknown key 'momentum' at 'opt\.adam'"),
        ('.opt.sdg.lr = 1', "Unknown tag 'sdg' at 'opt' - did you mean 'sgd'"),
        ('.name.x = 1', None),
    ]:
        with pytest.raises((OverridePathError, OverrideJqError), match=match):
            jq(source)

    # Not something a filter gets to shrug off.
    with pytest.raises(OverridePathError):
        jq('(.vresion = "2")?')
    with pytest.raises(OverrideValueError):
        jq('try (.version = 1) catch .')


def test_writes_displace_wrapper_tags():
    assert jq('.opt.sgd.lr = 1')['opt'] == {'sgd': {'lr': 1.}}
    assert jq('.opt |= (.sgd.momentum = 1)')['opt'] == {'sgd': {'momentum': 1.}}
    assert jq('.opt.sgd = {}')['opt'] == {'sgd': {}}
    assert jq('.opt = {sgd: {lr: 1}}')['opt'] == {'sgd': {'lr': 1.}}
    assert jq('.opt.sgd.lr = 1 | .opt.sgd.momentum = 2 | .opt.adam.lr = 3')['opt'] == {'adam': {'lr': 3.}}
    assert jq('.opt.adam.lr = 5')['opt'] == {'adam': {'lr': 5., 'betas': [0.9, 0.99]}}
    assert jq('.opt2.sgd.lr = 1')['opt2'] == {'sgd': {'lr': 1.}}
    assert jq('.opt2 = .opt | .opt2.sgd.lr = 1') == {**TREE, 'opt2': {'sgd': {'lr': 1.}}}

    with pytest.raises(OverrideValueError, match=r"exactly one tag at 'opt', got \['adam', 'sgd'\]"):
        jq('.opt += {sgd: {lr: 1}}')

    # Without the shape there is nothing to say they can't coexist.
    assert jq('.opt.sgd.lr = 1', shape=None)['opt'] == {**TREE['opt'], 'sgd': {'lr': 1}}


def test_field_tags():
    assert jq('.sched.t_max = 5.0')['sched'] == {'type': 'cosine', 't_max': 5}
    assert jq('.sched = {type: "step", size: 1}')['sched'] == {'type': 'step', 'size': 1}
    assert jq('.sched |= (del(.t_max) | .type = "step") | .sched.gamma = 1')['sched'] == {'type': 'step', 'gamma': 1.}

    with pytest.raises(OverridePathError, match="Unknown key 'gamma' at 'sched'"):
        jq('.sched.gamma = 1')
    with pytest.raises(OverrideValueError, match=r"Expected one of 'cosine', 'step' at 'sched\.type'"):
        jq('.sched.type = "stp"')
    with pytest.raises(OverrideValueError, match="Unknown tag 'stp' at 'sched'"):
        jq('.sched = {type: "stp"}')


def test_rebuilt_roots_are_conformed_whole():
    assert jq('. * {opt: {adam: {lr: 9}}, version: "2"}') == {
        **TREE,
        'version': '2',
        'opt': {'adam': {'lr': 9., 'betas': [0.9, 0.99]}},
    }
    assert type(jq('. + {dropout: 1}')['dropout']) is float
    assert jq('to_entries | from_entries') == TREE

    for source, match in [
        ('. * {vresion: "2"}', "Unknown key 'vresion' at the root - did you mean 'version'"),
        ('. + {version: 2}', "Expected str at 'version', got number 2"),
        ('. * {opt: {sgd: {lr: 1}}}', "exactly one tag at 'opt'"),
        ('.opt', "Unknown key 'adam' at the root"),
        ('{name}', None),
        ('.layers', 'Expected map at the root, got a list'),
        ('5', 'Expected map at the root, got number 5'),
    ]:
        if match is None:
            assert jq(source) == {'name': 'm'}
        else:
            with pytest.raises(OverrideValueError, match=match):
                jq(source)


def test_nothing_is_demanded_of_anything_or_unknown():
    out = jq('.extra.a = {b: [1, "x", 1.5]} | .extra.n = 1.10 | .secret.a = "s" | .secret.new = [1.0]')
    assert out['extra'] == {'k': None, 'n': 1.1, 'a': {'b': [1, 'x', 1.5]}}
    assert out['secret'] == {'a': 's', 'new': [1.]}

    assert jq('.a.b = 1.0', {}, UnknownShape())['a'] == {'b': 1.}
    assert jq('.a.b = 1.0', {}, None)['a'] == {'b': 1.}


def test_reads_tolerate_trees_at_odds_with_their_shape():
    tree = {'name': 5, 'layers': {'not': ['a', 'list']}, 'nope': {'x': 1}, 'opt': {'zzz': {'lr': 'x'}}}

    assert jq('.', tree) == tree
    assert jq('.name = (.layers.not | join("-"))', tree)['name'] == 'a-list'
    assert jq('.version = (.nope.x | tostring)', tree)['version'] == '1'
    assert jq('del(.nope) | del(.layers) | del(.opt.zzz)', tree) == {'name': 5, 'opt': {}}

    with pytest.raises(OverridePathError):
        jq('.nope.x = 2', tree)
    with pytest.raises(OverrideValueError, match="Unknown key 'not' at the root"):
        jq('.layers', tree)


def test_output_count():
    for source in ['empty', '.layers[]', '., .']:
        for shape in [SHAPE, None]:
            with pytest.raises(OverrideJqError, match='exactly one output'):
                jq(source, shape=shape)
    for source in ['.name |', '.name | error("x")', '.layers | keys | .[0] | .x']:
        for shape in [SHAPE, None]:
            with pytest.raises(OverrideJqError, match='failed'):
                jq(source, shape=shape)


##


def test_ops_interleave():
    out = apply_overrides(
        TREE,
        [
            'layers.0.dim=1',
            JqOp('.layers |= map(.dim *= 2)'),
            'opt.sgd.lr=1',
            JqOp('.opt.sgd.momentum = (.layers | length)'),
            'layers.+={name: 5}',
            JqOp('.layers[-1].tags = [.name]'),
            '/layers.0',
        ],
        SHAPE,
    )
    assert out['opt'] == {'sgd': {'lr': 1., 'momentum': 2.}}
    assert out['layers'] == [
        {'name': 'dec', 'dim': 32, 'tags': []},
        {'name': '5', 'tags': ['m']},
    ]
