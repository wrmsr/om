import copy
import json
import os.path
import typing as ta

import pytest

from ..applying import OverrideApplier
from ..applying import apply_overrides
from ..errors import OverrideFileError
from ..errors import OverrideJqError
from ..errors import OverrideOpError
from ..errors import OverridePathError
from ..errors import OverrideSyntaxError
from ..errors import OverrideValueError
from ..ops import ConstOpValue
from ..ops import JqOp
from ..ops import MergeOp
from ..ops import SetOp
from ..parsing import parse_path
from ..shapes import ChoiceShape
from ..shapes import ListShape
from ..shapes import MapShape
from ..shapes import ObjectShape
from ..shapes import OptionalShape
from ..shapes import ScalarShape
from ..shapes import TaggedShape
from ..shapes import TupleShape
from ..shapes import UnknownShape


TREE: ta.Any = {
    'name': 'm',
    'opt': {'lr': 0.001, 'betas': [0.9, 0.99]},
    'layers': [
        {'name': 'enc', 'dim': 8, 'on': True},
        {'name': 'dec', 'dim': 16, 'on': False},
    ],
    'dropout': None,
}


def apply(*ops, tree=TREE, **kwargs):
    return apply_overrides(tree, ops, **kwargs)


##
# Shapeless


def test_input_is_untouched():
    tree = copy.deepcopy(TREE)
    out = apply('name=x', 'layers.0.dim=1', 'opt.betas.+=1', '/dropout', tree=tree)
    assert tree == TREE
    assert out != TREE
    assert apply() == TREE
    assert apply() is not TREE


def test_set():
    assert apply('name=x')['name'] == 'x'
    assert apply('name=5')['name'] == 5
    assert apply('name="5"')['name'] == '5'
    assert apply('opt.lr=3e-4')['opt'] == {'lr': 3e-4, 'betas': [0.9, 0.99]}
    assert apply('opt={lr: 1}')['opt'] == {'lr': 1}
    assert apply('opt=null')['opt'] is None
    assert apply('={a: 1}') == {'a': 1}
    assert apply('"name"=x')['name'] == 'x'


def test_set_creates_intermediates():
    assert apply('a.b.c=1')['a'] == {'b': {'c': 1}}
    assert apply('dropout.p=0.5')['dropout'] == {'p': 0.5}
    assert apply('xs[+]=1', 'xs.+=2')['xs'] == [1, 2]
    assert apply('xs[+].a=1', 'xs[+].a=2')['xs'] == [{'a': 1}, {'a': 2}]
    assert apply('a.0=x')['a'] == {'0': 'x'}

    with pytest.raises(OverridePathError, match="Cannot navigate into a scalar at 'name'"):
        apply('name.x=1')
    with pytest.raises(OverridePathError, match='out of range'):
        apply('xs[0]=1')


def test_indices():
    for s in ['layers[0].dim=1', 'layers.0.dim=1', 'layers[-2].dim=1', 'layers.-2.dim=1']:
        assert [l['dim'] for l in apply(s)['layers']] == [1, 16]

    assert apply('opt.betas[1]=0.5')['opt']['betas'] == [0.9, 0.5]
    assert apply('opt.betas[+]=0.5')['opt']['betas'] == [0.9, 0.99, 0.5]
    assert apply('layers.1=x')['layers'] == [TREE['layers'][0], 'x']

    for s in ['layers[2].dim=1', 'layers.-3.dim=1', 'layers.x=1', 'layers["0"].dim=1', 'opt[0]=1', 'opt[+]=1']:
        with pytest.raises(OverridePathError):
            apply(s)

    # An unquoted integer key is only an index when applied to a list.
    assert apply('opt.0=x')['opt']['0'] == 'x'


def test_select():
    assert [l['dim'] for l in apply('layers[name=dec].dim=1')['layers']] == [8, 1]
    assert [l['dim'] for l in apply('layers[dim=8].dim=1')['layers']] == [1, 16]
    assert [l['dim'] for l in apply('layers[on=false].dim=1')['layers']] == [8, 1]
    assert [l['dim'] for l in apply('layers[name="enc"].dim=1')['layers']] == [1, 16]
    assert apply('layers[name=enc]={name: new}')['layers'][0] == {'name': 'new'}

    tree = {'xs': [{'spec': {'id': 1, 'v': None}}, {'spec': {'id': 2, 'v': 1.5}}, 'x', {'spec': 3}]}
    assert apply('xs[spec.id=2].hit=true', tree=tree)['xs'][1]['hit'] is True
    assert apply('xs[spec.v=null].hit=true', tree=tree)['xs'][0]['hit'] is True
    assert apply('xs[spec.v=1.5].hit=true', tree=tree)['xs'][1]['hit'] is True

    for s in [
        'layers[name=zzz].dim=1',
        'layers[dim="8"].dim=1',
        'layers[on=1].dim=1',
        'layers[nope=1].dim=1',
        'opt[lr=0.001]=1',
    ]:
        with pytest.raises(OverridePathError):
            apply(s)

    with pytest.raises(OverridePathError, match='found 2'):
        apply('xs[a=1].b=2', tree={'xs': [{'a': 1}, {'a': 1}]})


def test_merge():
    assert apply('opt+={lr: 1, eps: 2}')['opt'] == {'lr': 1, 'betas': [0.9, 0.99], 'eps': 2}
    assert apply('+={name: x, opt: {lr: 1}}') == {**TREE, 'name': 'x', 'opt': {'lr': 1, 'betas': [0.9, 0.99]}}

    # Lists extend at the top, but replace when nested in a merged map.
    assert apply('opt.betas+=[1, 2]')['opt']['betas'] == [0.9, 0.99, 1, 2]
    assert apply('opt+={betas: [1, 2]}')['opt']['betas'] == [1, 2]

    # Into nothing is just a set.
    assert apply('dropout+={p: 1}')['dropout'] == {'p': 1}
    assert apply('new.thing+=[1]')['new'] == {'thing': [1]}
    assert apply('layers.0+={sub: {a: 1}}', 'layers.0+={sub: {b: 2}}')['layers'][0]['sub'] == {'a': 1, 'b': 2}

    for s in ['name+=x', 'opt+=[1]', 'opt.betas+={a: 1}', 'opt.lr+=1', 'opt+=5']:
        with pytest.raises(OverrideOpError):
            apply(s)


def test_remove():
    assert 'dropout' not in apply('/dropout')
    assert apply('/opt.lr')['opt'] == {'betas': [0.9, 0.99]}
    assert apply('/layers.0')['layers'] == [TREE['layers'][1]]
    assert apply('/layers[-1]')['layers'] == [TREE['layers'][0]]
    assert apply('/layers[name=enc]')['layers'] == [TREE['layers'][1]]
    assert apply('/opt.betas.0', '/opt.betas.0')['opt']['betas'] == []

    for s in ['/nope', '/opt.nope', '/nope.x', '/layers.5', '/layers.+', '/name.x', '/dropout.x']:
        with pytest.raises(OverridePathError):
            apply(s)


def test_ops_apply_in_order():
    assert apply('a=1', 'a=2')['a'] == 2
    assert 'a' not in apply('a=1', '/a')
    assert apply('/name', 'name=z')['name'] == 'z'
    assert apply('xs=[]', 'xs.+=1', 'xs.+=2', '/xs.0', 'xs+=[3]')['xs'] == [2, 3]


def test_op_objects():
    assert apply(SetOp(parse_path('a.b'), ConstOpValue({'c': (1, 2)})))['a'] == {'b': {'c': [1, 2]}}
    assert apply(MergeOp(parse_path('opt'), ConstOpValue({'lr': '5'})))['opt']['lr'] == '5'

    v = {'c': [1]}
    out = apply(SetOp(parse_path('a'), ConstOpValue(v)), 'a.c.+=2')
    assert out['a'] == {'c': [1, 2]}
    assert v == {'c': [1]}

    with pytest.raises(OverrideSyntaxError):
        apply('a.b')


##
# Files


def test_files_injected():
    files: ta.Any = {
        'opt.json': {'lr': 5, 'betas': [1]},
        'layer.json': {'name': 'new'},
        'root.json': {'name': 'r', 'opt': {'eps': 1}},
    }
    kw = dict(file_loader=files.__getitem__)

    assert apply('opt=@opt.json', **kw)['opt'] == {'lr': 5, 'betas': [1]}
    assert apply('opt+=@opt.json', **kw)['opt'] == {'lr': 5, 'betas': [1]}
    assert apply('layers.+=@layer.json', **kw)['layers'][-1] == {'name': 'new'}
    assert apply('@root.json', **kw) == {**TREE, 'name': 'r', 'opt': {**TREE['opt'], 'eps': 1}}

    out = apply('a=@opt.json', 'a.betas.+=2', **kw)
    assert out['a']['betas'] == [1, 2]
    assert files['opt.json']['betas'] == [1]

    with pytest.raises(OverrideFileError, match=r'nope\.json'):
        apply('opt=@nope.json', **kw)


def test_files(tmp_path):
    jp = os.path.join(tmp_path, 'o.json')
    with open(jp, 'w') as f:
        json.dump({'lr': 5}, f)
    tp = os.path.join(tmp_path, 'o.toml')
    with open(tp, 'w') as f:
        f.write('name = "t"\n[opt]\neps = 1\n')

    assert apply(f'opt=@{jp}')['opt'] == {'lr': 5}
    assert apply(f'@{tp}') == {**TREE, 'name': 't', 'opt': {**TREE['opt'], 'eps': 1}}

    with pytest.raises(OverrideFileError):
        apply(f'opt=@{os.path.join(tmp_path, "nope.json")}')


##
# Jq


def test_jq():
    assert apply(JqOp('.opt.lr *= 2'))['opt']['lr'] == 0.002
    assert apply(JqOp('del(.layers[0])'))['layers'] == [TREE['layers'][1]]

    out = apply('opt.lr=1', JqOp('.opt.lr += 1'), 'opt.lr2=x', JqOp('.n = (.layers | length)'))
    assert out['opt'] == {'lr': 2, 'betas': [0.9, 0.99], 'lr2': 'x'}
    assert out['n'] == 2

    # Outputs may alias - within themselves and with their input - and must not continue to.
    out = apply(JqOp('.a = .opt | .b = .opt'), 'a.lr=1', 'b.betas.+=1')
    assert out['a']['lr'] == 1
    assert out['b']['lr'] == 0.001
    assert out['opt'] == TREE['opt']
    assert out['a']['betas'] == [0.9, 0.99]

    for f in ['empty', '.layers[]', '.name |', '.name | error("x")']:
        with pytest.raises(OverrideJqError):
            apply(JqOp(f))


##
# Shaped


STR = ScalarShape(str)
INT = ScalarShape(int)
FLOAT = ScalarShape(float)

SHAPE = ObjectShape({
    'name': STR,
    'version': STR,
    'opt': ObjectShape({
        'lr': FLOAT,
        'betas': TupleShape([FLOAT, FLOAT]),
    }),
    'layers': ListShape(ObjectShape({
        'name': STR,
        'dim': INT,
        'on': ScalarShape(bool),
    })),
    'dropout': OptionalShape(FLOAT),
    'sub': OptionalShape(ObjectShape({'xs': ListShape(INT), 'm': MapShape(INT)})),
    'secret': UnknownShape('secret'),
})


def test_shaped_values():
    out = apply('name=123', 'version=1.10', 'opt.lr=1', 'dropout=5', 'layers.0.name=true', shape=SHAPE)
    assert out['name'] == '123'
    assert out['version'] == '1.10'
    assert type(out['opt']['lr']) is float
    assert type(out['dropout']) is float
    assert out['layers'][0]['name'] == 'true'

    assert apply('dropout=null', shape=SHAPE)['dropout'] is None
    assert apply('layers.+={name: 5, dim: 5}', shape=SHAPE)['layers'][-1] == {'name': '5', 'dim': 5}
    assert apply('opt+={lr: 5, betas: [1, 2]}', shape=SHAPE)['opt'] == {'lr': 5., 'betas': [1., 2.]}

    for s in ['opt.lr=x', 'layers.0.dim=1.5', 'layers.0.on=1', 'opt.betas=[1]', 'opt+={lr: x}', 'opt.betas.+=1']:
        with pytest.raises((OverrideValueError, OverridePathError)):
            apply(s, shape=SHAPE)


def test_shaped_keys():
    with pytest.raises(OverridePathError, match="Unknown key 'nmae' at the root - did you mean 'name'"):
        apply('nmae=x', shape=SHAPE)
    with pytest.raises(OverridePathError, match="Unknown key 'l' at 'opt' - did you mean 'lr'"):
        apply('opt.l=1', shape=SHAPE)
    with pytest.raises(OverridePathError, match=r"Unknown key 'dmi' at 'layers\.0'"):
        apply('layers.0.dmi=1', shape=SHAPE)
    with pytest.raises(OverridePathError, match="Unknown key 'eps' at 'opt'"):
        apply('opt+={eps: 1}', shape=SHAPE)
    with pytest.raises(OverrideValueError, match="Unknown key 'eps' at 'opt'"):
        apply('opt={lr: 1, eps: 1}', shape=SHAPE)
    with pytest.raises(OverridePathError, match='Cannot navigate into str'):
        apply('name.x=1', tree={}, shape=SHAPE)
    with pytest.raises(OverridePathError, match='Expected list but found map'):
        apply('layers.x=1', tree={'layers': {}}, shape=SHAPE)


def test_shaped_creation():
    # Shapes decide what gets created where the path alone can't.
    assert apply('sub.xs.+=1', tree={}, shape=SHAPE) == {'sub': {'xs': [1]}}
    assert apply('sub.m.0=1', tree={}, shape=SHAPE) == {'sub': {'m': {'0': 1}}}
    assert apply('layers.+.name=x', tree={}, shape=SHAPE) == {'layers': [{'name': 'x'}]}
    assert apply('sub.xs+=[1, 2]', tree={'sub': None}, shape=SHAPE) == {'sub': {'xs': [1, 2]}}


def test_shaped_remove():
    # Something declared but absent is already at its default.
    assert apply('/dropout', '/dropout', shape=SHAPE) == {k: v for k, v in TREE.items() if k != 'dropout'}
    assert apply('/opt.lr', tree={'opt': {}}, shape=SHAPE) == {'opt': {}}

    with pytest.raises(OverridePathError, match="Unknown key 'nope'"):
        apply('/nope', shape=SHAPE)
    with pytest.raises(OverridePathError, match="Nothing at 'sub'"):
        apply('/sub.xs', shape=SHAPE)
    with pytest.raises(OverridePathError, match=r"Nothing at 'sub\.m\.k'"):
        apply('/sub.m.k', tree={'sub': {'m': {}}}, shape=SHAPE)


def test_shaped_unknown():
    tree = {**TREE, 'secret': {'a': 1, 'b': [1]}}

    # Coexisting with, removing, and passing concrete values through something not understood is all fine.
    assert apply('name=x', '/secret.a', '/secret', tree=tree, shape=SHAPE)['name'] == 'x'
    assert apply(SetOp(parse_path('secret.a'), ConstOpValue(2)), tree=tree, shape=SHAPE)['secret']['a'] == 2
    assert apply('+=@f', tree=tree, shape=SHAPE, file_loader=lambda _: {'secret': {'a': 3}})['secret']['a'] == 3
    assert apply(JqOp('.secret.a = 4'), tree=tree, shape=SHAPE)['secret']['a'] == 4

    # Having to produce a value for it is not - unless guessing.
    for s in ['secret=x', 'secret.a=5', 'secret.b.+=5', 'secret+={c: 1}', '+={secret: {a: 5}}']:
        with pytest.raises(Exception) as ei:  # noqa
            apply(s, tree=tree, shape=SHAPE)
        assert type(ei.value).__name__ == 'UnhandledOverrideShapeError'

    out = apply('secret.a=5', 'secret.b.+=x', 'secret+={c: 1.5}', tree=tree, shape=SHAPE, guess_unknown=True)
    assert out['secret'] == {'a': 5, 'b': [1, 'x'], 'c': 1.5}


WRAPPED_SHAPE = ObjectShape({
    'opt': OptionalShape(TaggedShape({
        'adam': ObjectShape({'lr': FLOAT, 'betas': ListShape(FLOAT)}),
        'sgd': ObjectShape({'lr': FLOAT, 'momentum': FLOAT}),
    })),
})


def test_shaped_wrapper_tags():
    tree = {'opt': {'adam': {'lr': 1., 'betas': [1.]}}}

    def apply_wrapped(*ops, tree=tree):
        return apply(*ops, tree=tree, shape=WRAPPED_SHAPE)['opt']

    assert apply_wrapped('opt.adam.lr=5') == {'adam': {'lr': 5., 'betas': [1.]}}
    assert apply_wrapped('opt+={adam: {lr: 5}}') == {'adam': {'lr': 5., 'betas': [1.]}}

    # A different tag displaces the present one rather than joining it.
    assert apply_wrapped('opt.sgd.lr=5') == {'sgd': {'lr': 5.}}
    assert apply_wrapped('opt.sgd={}') == {'sgd': {}}
    assert apply_wrapped('opt+={sgd: {momentum: 5}}') == {'sgd': {'momentum': 5.}}
    assert apply_wrapped('opt={sgd: {lr: 5}}') == {'sgd': {'lr': 5.}}
    assert apply_wrapped('opt.sgd.lr=5', 'opt.sgd.momentum=1', 'opt.adam.lr=2') == {'adam': {'lr': 2.}}
    assert apply_wrapped('opt.sgd.lr=5', tree={'opt': None}) == {'sgd': {'lr': 5.}}
    assert apply_wrapped('opt.sgd.lr=5', tree={}) == {'sgd': {'lr': 5.}}

    with pytest.raises(OverridePathError, match="Unknown tag 'sdg' at 'opt' - did you mean 'sgd'"):
        apply_wrapped('opt.sdg.lr=1')
    with pytest.raises(OverridePathError, match=r"Unknown key 'momentum' at 'opt\.adam'"):
        apply_wrapped('opt.adam.momentum=1')
    with pytest.raises(OverridePathError, match=r"Nothing at 'opt\.sgd'"):
        apply_wrapped('/opt.sgd.lr')

    # Without the shape there is nothing to say they can't coexist.
    assert apply('opt.sgd.lr=5', tree=tree)['opt'] == {**tree['opt'], 'sgd': {'lr': 5}}


FIELD_TAGGED_SHAPE = ObjectShape({
    'opt': TaggedShape(
        {
            'adam': ObjectShape({'lr': FLOAT, 'betas': ListShape(FLOAT)}),
            'sgd': ObjectShape({'lr': FLOAT, 'momentum': INT}),
        },
        tag_field='type',
    ),
})


def test_shaped_field_tags():
    tree = {'opt': {'type': 'sgd', 'lr': 1., 'momentum': 1}}

    def apply_tagged(*ops, tree=tree):
        return apply(*ops, tree=tree, shape=FIELD_TAGGED_SHAPE)['opt']

    assert apply_tagged('opt.lr=5', 'opt.momentum=5') == {'type': 'sgd', 'lr': 5., 'momentum': 5}
    assert apply_tagged('opt+={momentum: 5}') == {'type': 'sgd', 'lr': 1., 'momentum': 5}
    assert apply_tagged('opt={type: adam, betas: [1]}') == {'type': 'adam', 'betas': [1.]}

    # Switching the tag strands the fields of the old alternative, which can still be removed.
    assert apply_tagged('opt.type=adam', '/opt.momentum', 'opt.betas=[1]') == {'type': 'adam', 'lr': 1., 'betas': [1.]}
    assert apply_tagged('/opt.momentum', 'opt.type=adam') == {'type': 'adam', 'lr': 1.}
    with pytest.raises(OverridePathError, match="Unknown key 'momentum' at 'opt'"):
        apply_tagged('opt.type=adam', '/opt.momentum', '/opt.momentum')
    assert apply_tagged('opt.type=sgd', 'opt.momentum=5', tree={}) == {'type': 'sgd', 'momentum': 5}

    with pytest.raises(OverridePathError, match="Unknown key 'betas' at 'opt'"):
        apply_tagged('opt.betas=[1]')
    with pytest.raises(OverrideValueError, match="did you mean 'adam'"):
        apply_tagged('opt.type=adm')
    with pytest.raises(OverridePathError, match="No 'type' tag set at 'opt'"):
        apply_tagged('opt.lr=1', tree={})
    with pytest.raises(OverridePathError, match="Unknown tag 'nope' at 'opt'"):
        apply_tagged('opt.lr=1', tree={'opt': {'type': 'nope'}})


def test_applier_is_reusable():
    a = OverrideApplier(ObjectShape({'x': ChoiceShape(['a', 'b'])}))
    assert a.apply({}, ['x=a']) == {'x': 'a'}
    assert a.apply({'x': 'a'}, ['x=b']) == {'x': 'b'}
    with pytest.raises(OverrideValueError):
        a.apply({}, ['x=c'])
