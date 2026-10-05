import argparse

import pytest

from ..applying import apply_overrides
from ..args import add_override_arguments
from ..ops import JqOp
from ..ops import RemoveOp
from ..ops import SetOp
from ..parsing import parse_override


def new_parser(**kwargs):
    p = argparse.ArgumentParser(exit_on_error=False)
    p.add_argument('cmd', nargs='?')
    add_override_arguments(p, **kwargs)
    return p


def test_ops_interleave_in_order():
    args = new_parser().parse_args([
        '-s', 'a.b=1',
        '--jq', '.a.b += 1',
        'run',
        '--set', 'a.c=x',
        '-s', '/a.b',
        '--jq=.n = (.a | length)',
        '-s=xs.+=1',
    ])

    assert args.cmd == 'run'
    assert args.overrides == [
        parse_override('a.b=1'),
        JqOp('.a.b += 1'),
        parse_override('a.c=x'),
        parse_override('/a.b'),
        JqOp('.n = (.a | length)'),
        parse_override('xs.+=1'),
    ]
    assert isinstance(args.overrides[0], SetOp)
    assert isinstance(args.overrides[3], RemoveOp)

    assert apply_overrides({}, args.overrides) == {'a': {'c': 'x'}, 'n': 1, 'xs': [1]}


def test_defaults():
    args = new_parser().parse_args([])
    assert args.overrides is None
    assert args.dump is None
    assert apply_overrides({'a': 1}, args.overrides or []) == {'a': 1}


def test_dump_flag():
    assert new_parser().parse_args(['--dump']).dump == 'overrides'
    assert new_parser().parse_args(['--dump=json']).dump == 'json'
    assert new_parser().parse_args(['--dump', 'overrides', 'run']).cmd == 'run'

    with pytest.raises(argparse.ArgumentError):
        new_parser().parse_args(['--dump=yaml'])


def test_syntax_errors_are_argument_errors():
    with pytest.raises(argparse.ArgumentError, match="expected '=' or"):
        new_parser().parse_args(['-s', 'a.b'])


def test_custom_flags():
    p = new_parser(set_flags=['-o'], jq_flags=[], dump_flags=[], dest='ops')
    args = p.parse_args(['-o', 'a=1'])
    assert args.ops == [parse_override('a=1')]
    assert not hasattr(args, 'dump')

    with pytest.raises(argparse.ArgumentError):
        p.parse_args(['--jq', '.'])
    with pytest.raises(argparse.ArgumentError):
        p.parse_args(['-s', 'a=1'])
