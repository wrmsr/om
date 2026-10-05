import dataclasses as dc
import datetime
import enum
import typing as ta
import uuid

import pytest

from .... import lang
from .... import marshal as msh
from ..errors import OverridePathError
from ..errors import OverrideValueError
from ..errors import UnhandledOverrideShapeError
from ..marshal import ConfigOverrider
from ..marshal import get_unmarshaler_shape
from ..marshal import override_config
from ..ops import JqOp
from ..shapes import AnyShape
from ..shapes import ChoiceShape
from ..shapes import ListShape
from ..shapes import MapShape
from ..shapes import ObjectShape
from ..shapes import OptionalShape
from ..shapes import ScalarShape
from ..shapes import TaggedShape
from ..shapes import TupleShape
from ..shapes import UnionShape
from ..shapes import UnknownShape
from ..shapes import unlazy_shape


##


class Color(enum.Enum):
    RED = 1
    BLUE = 2


@msh.set_polymorphic()
class Opt(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class Adam(Opt):
    lr: float = 1e-3
    betas: tuple[float, float] = (0.9, 0.99)


@dc.dataclass(frozen=True)
class Sgd(Opt):
    lr: float = 1e-2
    momentum: float = 0.


@msh.set_polymorphic(type_tagging=msh.FieldTypeTagging('type'))
class Sched(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class Cosine(Sched):
    t_max: int = 10


@dc.dataclass(frozen=True)
class Step(Sched):
    gamma: float = .1
    size: int = 1


@dc.dataclass(frozen=True)
class Layer:
    name: str
    dim: int = 8
    kids: ta.Sequence[Layer] = ()


UserId = ta.NewType('UserId', int)


@dc.dataclass(frozen=True)
class Model:
    name: str = 'm'
    version: str = '1.0'
    debug: bool = False
    dropout: float | None = None

    opt: Opt = Adam()
    opt2: Adam | Sgd | None = None
    sched: Sched = Cosine()

    layers: ta.Sequence[Layer] = (Layer('enc'), Layer('dec'))
    by_name: ta.Mapping[str, Layer] = dc.field(default_factory=dict)
    extra: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)

    tag: int | str = 0
    ratio: float | str = 0.
    mixed: int | Layer | None = None
    mode: ta.Literal['a', 'b'] = 'a'
    mode2: ta.Literal['auto'] | int = 'auto'
    color: Color = Color.RED
    uid: UserId = UserId(0)
    tags: frozenset[str] = frozenset()
    sizes: tuple[int, ...] = ()

    # Not understood
    when: datetime.datetime = datetime.datetime(2026, 1, 1)  # noqa
    id: uuid.UUID | None = None
    by_id: ta.Mapping[int, str] = dc.field(default_factory=dict)


def override(*ops, obj=None, **kwargs):
    return override_config(obj if obj is not None else Model(), ops, **kwargs)


##


def test_shapes():
    root = ConfigOverrider(Model).shape
    assert isinstance(root, ObjectShape)
    assert not root.open
    assert list(root.fields) == [f.name for f in dc.fields(Model)]

    def get(*ks):
        s: ta.Any = root
        for k in ks:
            s = unlazy_shape(s)
            if isinstance(s, ObjectShape):
                s = s.fields[k]
            elif isinstance(s, TaggedShape):
                s = s.by_tag[k]
            else:
                s = getattr(s, k)
        return unlazy_shape(s)

    assert get('name') == ScalarShape(str)
    assert get('debug') == ScalarShape(bool)
    assert get('uid') == ScalarShape(int)
    assert isinstance(get('dropout'), OptionalShape)
    assert get('dropout', 'inner') == ScalarShape(float)

    opt = get('opt')
    assert isinstance(opt, TaggedShape)
    assert opt.tag_field is None
    assert set(opt.by_tag) == {'Adam', 'Sgd'}
    assert get('opt', 'Adam', 'lr') == ScalarShape(float)
    betas = get('opt', 'Adam', 'betas')
    assert isinstance(betas, TupleShape)
    assert [unlazy_shape(e) for e in betas.elements] == [ScalarShape(float)] * 2

    assert set(get('opt2', 'inner').by_tag) == {'Adam', 'Sgd'}

    sched = get('sched')
    assert isinstance(sched, TaggedShape)
    assert sched.tag_field == 'type'
    assert get('sched', 'Step', 'gamma') == ScalarShape(float)

    assert isinstance(get('layers'), ListShape)
    assert get('layers', 'element', 'dim') == ScalarShape(int)
    # Recursion, by way of the proxy.
    assert get('layers', 'element', 'kids', 'element', 'kids', 'element', 'name') == ScalarShape(str)

    assert isinstance(get('by_name'), MapShape)
    assert get('by_name', 'value', 'name') == ScalarShape(str)
    assert isinstance(get('extra'), MapShape)
    assert get('extra', 'value') == AnyShape()

    tag = get('tag')
    assert isinstance(tag, UnionShape)
    assert [unlazy_shape(a) for a in tag.alternatives] == [ScalarShape(int), ScalarShape(str)]
    mixed = get('mixed', 'inner')
    assert isinstance(mixed, UnionShape)
    assert unlazy_shape(mixed.alternatives[0]) == ScalarShape(int)
    assert isinstance(unlazy_shape(mixed.alternatives[1]), ObjectShape)

    assert get('mode') == ChoiceShape(['a', 'b'])
    mode2 = get('mode2')
    assert isinstance(mode2, UnionShape)
    assert [unlazy_shape(a) for a in mode2.alternatives] == [ChoiceShape(['auto']), ScalarShape(int)]
    assert get('color') == ChoiceShape(['RED', 'BLUE'])

    assert get('tags', 'element') == ScalarShape(str)
    assert isinstance(get('sizes'), ListShape)

    for k in ['when', 'by_id']:
        assert isinstance(get(k), UnknownShape)
    assert isinstance(get('id', 'inner'), UnknownShape)


def test_shape_derivation_is_lazy():
    @dc.dataclass(frozen=True)
    class Outer:
        when: datetime.datetime | None = None

    u = msh.global_marshaling().new_unmarshal_factory_context().make_unmarshaler(Outer)
    s = get_unmarshaler_shape(u)
    assert isinstance(s, ObjectShape)
    assert not isinstance(s.fields['when'], (OptionalShape, UnknownShape))
    assert isinstance(unlazy_shape(s.fields['when']), OptionalShape)


def test_subclassed_handlers_are_not_understood():
    class MyOptionalUnmarshaler(msh.OptionalUnmarshaler):
        pass

    assert isinstance(get_unmarshaler_shape(msh.OptionalUnmarshaler(msh.NOP_MARSHALER_UNMARSHALER)), OptionalShape)
    assert isinstance(get_unmarshaler_shape(MyOptionalUnmarshaler(msh.NOP_MARSHALER_UNMARSHALER)), UnknownShape)


##


def test_scalars():
    m = override('name=123', 'version=1.10', 'debug=true', 'dropout=3e-4', 'uid=7')
    assert m == dc.replace(Model(), name='123', version='1.10', debug=True, dropout=3e-4, uid=UserId(7))
    assert type(m.uid) is int

    assert override('dropout=5').dropout == 5.
    assert type(override('dropout=5').dropout) is float
    assert override('dropout=1', 'dropout=null').dropout is None
    assert override('name=null').name == 'null'
    assert override('name=').name == ''
    assert override('name="quoted"').name == 'quoted'
    assert override('name={a}').name == '{a}'

    # A string takes whatever it is given.
    assert override('name=[').name == '['
    assert override('name=[a-z]+').name == '[a-z]+'

    for s in ['debug=1', 'debug="true"', 'dropout=x', 'dropout="1"', 'uid=1.5', 'uid=x']:
        with pytest.raises(OverrideValueError):
            override(s)
    with pytest.raises(OverrideValueError, match="Expected bool at 'debug', got 'yes'"):
        override('debug=yes')
    with pytest.raises(OverridePathError, match="Unknown key 'nmae' at the root - did you mean 'name'"):
        override('nmae=x')


def test_choices_and_unions():
    assert override('mode=b').mode == 'b'
    assert override('color=BLUE').color is Color.BLUE
    assert override('mode2=5').mode2 == 5
    assert override('mode2=5', 'mode2=auto').mode2 == 'auto'

    assert override('tag=5').tag == 5
    assert override('tag="5"').tag == '5'
    assert override('tag=five').tag == 'five'
    assert override('tag=1.5').tag == '1.5'
    assert override('tag=true').tag == 'true'

    # The union unmarshaler won't coerce an int to a float, so it has to arrive as one.
    assert type(override('ratio=5').ratio) is float
    assert override('ratio=half').ratio == 'half'

    assert override('mixed=5').mixed == 5
    assert override('mixed={name: 5}').mixed == Layer('5')
    assert override('mixed.name=x', 'mixed.dim=2').mixed == Layer('x', 2)
    assert override('mixed=5', 'mixed=null').mixed is None

    with pytest.raises(OverrideValueError, match="did you mean 'BLUE'"):
        override('color=BLEU')
    with pytest.raises(OverrideValueError):
        override('color=2')
    with pytest.raises(OverrideValueError):
        override('mode=c')
    with pytest.raises(OverrideValueError):
        override('mode2=x')


def test_collections():
    assert override('layers.0.dim=3', 'layers[name=dec].dim=4').layers == (Layer('enc', 3), Layer('dec', 4))
    assert override('layers.+={name: 5}').layers[-1] == Layer('5')
    assert override('layers+=[{name: a}, {name: b, dim: 1}]').layers[2:] == (Layer('a'), Layer('b', 1))
    assert override('layers=[]').layers == ()
    assert override('/layers[name=enc]').layers == (Layer('dec'),)
    assert override('/layers.-1').layers == (Layer('enc'),)

    assert override('layers.0.kids.+={name: k}', 'layers.0.kids.0.kids.+.name=kk').layers[0] == Layer(
        'enc',
        kids=(Layer('k', kids=(Layer('kk'),)),),
    )

    assert override('by_name.a.name=x', 'by_name.b={name: 5, dim: 5}').by_name == {
        'a': Layer('x'),
        'b': Layer('5', 5),
    }
    assert override('by_name.0.name=x').by_name == {'0': Layer('x')}

    assert override('tags=[a, 5]').tags == frozenset(['a', '5'])
    assert override('sizes=[1, 2]', 'sizes.+=3').sizes == (1, 2, 3)

    assert override('extra.a.b=5', 'extra.c=[1, x, "2", null]', 'extra.d=1.10').extra == {
        'a': {'b': 5},
        'c': [1, 'x', '2', None],
        'd': 1.1,
    }

    for s in ['layers.0.dmi=1', 'layers.+={nam: x}', 'layers.5.dim=1', 'layers[name=zzz].dim=1', 'sizes.+=x']:
        with pytest.raises((OverridePathError, OverrideValueError)):
            override(s)


def test_wrapper_polymorphism():
    assert override('opt.Adam.lr=1', 'opt.Adam.betas.0=0.5').opt == Adam(1., (0.5, 0.99))
    assert override('opt+={Adam: {lr: 1}}').opt == Adam(1.)

    assert override('opt.Sgd.momentum=1').opt == Sgd(momentum=1.)
    assert override('opt.Sgd={}').opt == Sgd()
    assert override('opt={Sgd: {lr: 1}}').opt == Sgd(1.)
    assert override('opt+={Sgd: {lr: 1}}').opt == Sgd(1.)
    assert override('opt.Sgd.lr=1', 'opt.Adam.lr=2').opt == Adam(2.)

    assert override('opt2.Sgd.lr=1').opt2 == Sgd(1.)
    assert override('opt2.Sgd.lr=1', 'opt2=null').opt2 is None

    with pytest.raises(OverridePathError, match="Unknown tag 'Sdg' at 'opt' - did you mean 'Sgd'"):
        override('opt.Sdg.lr=1')
    with pytest.raises(OverridePathError, match=r"Unknown key 'momentum' at 'opt\.Adam'"):
        override('opt.Adam.momentum=1')
    with pytest.raises(OverrideValueError, match='exactly 2 elements'):
        override('opt.Adam.betas=[1]')


def test_field_polymorphism():
    assert override('sched.t_max=5').sched == Cosine(5)
    assert override('sched={type: Step, gamma: 1}').sched == Step(1.)
    assert override('sched.type=Step', '/sched.t_max', 'sched.size=5').sched == Step(size=5)
    assert override('/sched.t_max', 'sched+={type: Step, size: 5}').sched == Step(size=5)

    with pytest.raises(OverridePathError, match="Unknown key 'gamma' at 'sched'"):
        override('sched.gamma=1')
    with pytest.raises(OverrideValueError, match="did you mean 'Step'"):
        override('sched.type=Stp')


def test_remove_resets_to_default():
    m = Model(name='x', dropout=.5, opt=Sgd(), layers=())
    assert override('/name', '/dropout', '/opt', '/layers', obj=m) == Model()
    assert override('/opt.Sgd.lr', obj=dc.replace(m, opt=Sgd(5., 5.))).opt == Sgd(momentum=5.)
    assert override('/name', '/name', obj=m).name == 'm'

    with pytest.raises(OverridePathError):
        override('/nope')


def test_jq():
    m = override('layers.0.dim=2', JqOp('.layers |= map(.dim *= 2)'), 'layers.1.dim=1')
    assert [l.dim for l in m.layers] == [4, 1]


def test_files():
    files = {'e.json': {'name': 'e', 'opt': {'Sgd': {'lr': 1}}, 'layers': [{'name': 'only'}]}}
    kw = dict(file_loader=files.__getitem__)

    assert override('@e.json', 'opt.Sgd.momentum=1', **kw) == dc.replace(
        Model(),
        name='e',
        opt=Sgd(1., 1.),
        layers=(Layer('only'),),
    )
    assert override('by_name.x=@e.json', file_loader=lambda _: {'name': 'f'}).by_name == {'x': Layer('f')}


##


def test_not_understood():
    # None of which gets in the way of anything else.
    assert override('name=x').name == 'x'

    for s in [
        'when=2026-02-03T04:05:06',
        'id=01234567-89ab-cdef-0123-456789abcdef',
        'by_id.5=x',
        'by_id={5: x}',
        '+={when: 2026-02-03T04:05:06}',
    ]:
        with pytest.raises(UnhandledOverrideShapeError):
            override(s)

    # Null for something optional is understood, whatever it is optionally.
    assert override('id=null', obj=Model(id=uuid.UUID(int=1))).id is None

    m = override(
        'when=2026-02-03T04:05:06',
        'id=01234567-89ab-cdef-0123-456789abcdef',
        'by_id.5=x',
        'name=y',
        guess_unknown=True,
    )
    assert m.when == datetime.datetime(2026, 2, 3, 4, 5, 6)  # noqa
    assert m.id == uuid.UUID('01234567-89ab-cdef-0123-456789abcdef')
    assert m.by_id == {5: 'x'}
    assert m.name == 'y'

    # No value needs producing to remove something, or to have jq or a file produce it.
    m = Model(when=datetime.datetime(2020, 1, 1), by_id={1: 'a'})  # noqa
    assert override('/when', '/by_id', obj=m) == Model()
    assert override(JqOp('.when = "2026-02-03T04:05:06"')).when == datetime.datetime(2026, 2, 3, 4, 5, 6)  # noqa
    assert override('+=@f', file_loader=lambda _: {'when': '2026-02-03T04:05:06'}).when.month == 2


##


def test_overrider():
    o = ConfigOverrider[Model](Model)

    tree = o.marshal(Model())
    assert tree['opt'] == {'Adam': {'lr': 0.001, 'betas': [0.9, 0.99]}}
    assert o.unmarshal(tree) == Model()

    tree2 = o.apply(tree, ['version=2.0', 'opt.Sgd.lr=1'])
    assert tree['version'] == '1.0'
    assert tree2['version'] == '2.0'
    assert tree2['opt'] == {'Sgd': {'lr': 1.}}

    assert o.override(Model(), ['version=2.0']).version == '2.0'
    assert o.override(Model(name='a'), ['version=2.0']) == Model(name='a', version='2.0')


def test_dump_round_trips():
    m = Model(
        name='5',
        version='1.10',
        dropout=.5,
        opt=Sgd(),
        opt2=Adam(),
        sched=Step(),
        by_name={'a b': Layer('x', kids=(Layer('null'),))},
        extra={'s': '5', 'n': 5, 'l': [None, 'true', {}], '0': 'zero'},
        tag='5',
        mixed=Layer('true'),
        tags=frozenset(['t']),
        sizes=(1, 2),
    )

    o = ConfigOverrider[Model](Model, guess_unknown=True)
    tree = o.marshal(m)
    lines = o.dump(tree).splitlines()

    assert 'name=5' in lines
    assert 'version=1.10' in lines
    assert 'opt.Sgd.lr=0.01' in lines
    assert 'sched.type=Step' in lines
    assert 'layers.0.name=enc' in lines
    assert 'by_name["a b"].kids.0.name=null' in lines
    assert 'extra.s="5"' in lines
    assert 'extra.n=5' in lines
    assert 'tag="5"' in lines
    assert 'mixed.name=true' in lines
    assert 'dropout=0.5' in lines
    assert 'opt2.Adam.betas.1=0.99' in lines

    for line in lines:
        assert o.unmarshal(o.apply(tree, [line])) == m, line
    assert o.override(m, lines) == m

    assert o.unmarshal(msh.unmarshal(msh.marshal(tree), ta.Any)) == m
    assert o.dump(tree, 'json').startswith('{\n')


def test_private_marshaling():
    @dc.dataclass(frozen=True)
    class Pt:
        x: int = 0
        y: int = 0

    mi = msh.SimpleMarshaling(
        marshaler_factory=msh.StandardMarshalerFactory(),
        unmarshaler_factory=msh.StandardUnmarshalerFactory(),
    )
    assert override_config(Pt(), ['x=5'], marshaling=mi) == Pt(5)
    assert override_config(Pt(1, 2), ['/x', 'y=3'], Pt, marshaling=mi) == Pt(0, 3)
