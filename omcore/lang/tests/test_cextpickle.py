import operator
import os
import pickle
import subprocess
import sys
import typing as ta

import pytest

from ...diag._pycharm import runhack as pycharm_runhack
from .. import comparison
from .. import functions


##


_PURE_SCRIPT = r"""
import importlib.abc
import operator
import pickle
import sys


class CextBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'omcore.lang._comparison', 'omcore.lang._functions'}:
            raise ModuleNotFoundError(fullname)
        return None


sys.meta_path.insert(0, CextBlocker())

from omcore.lang import comparison
from omcore.lang import functions


def make_objects():
    return {
        'key_default': comparison.key_cmp(),
        'key_cmp': comparison.key_cmp(comparison.cmp),
        'key_hash_eq_id_cmp': comparison.key_cmp(comparison.hash_eq_id_cmp),
        'key_custom': comparison.key_cmp(operator.sub),
        'attr_unbound': functions.attrsetter('value'),
        'attr_none': functions.attrsetter('value', None),
        'item_unbound': functions.itemsetter('value'),
        'item_none': functions.itemsetter('value', None),
    }


def check_objects(objects):
    assert objects['key_default']((1, 'a'), (2, 'b')) == -1
    assert objects['key_cmp']((1, 'a'), (2, 'b')) == -1
    assert objects['key_hash_eq_id_cmp']((1, 'a'), (2, 'b')) == -1
    assert objects['key_custom']((1, 'a'), (2, 'b')) == -1

    class Target:
        value: object

    target = Target()
    objects['attr_unbound'](target, 420)
    assert target.value == 420
    objects['attr_none'](target)
    assert target.value is None

    target_dict: dict[str, object] = {}
    objects['item_unbound'](target_dict, 420)
    assert target_dict['value'] == 420
    objects['item_none'](target_dict)
    assert target_dict['value'] is None


assert comparison._comparison is None
assert functions._functions is None

if sys.argv[1] == 'load':
    objects = pickle.loads(sys.stdin.buffer.read())
    check_objects(objects)
    assert type(objects['key_default']).__module__ == 'omcore.lang.comparison'
    assert type(objects['attr_unbound']).__module__ == 'omcore.lang.functions'
elif sys.argv[1] == 'dump':
    objects = make_objects()
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        round_tripped = pickle.loads(pickle.dumps(objects, protocol))
        check_objects(round_tripped)
    sys.stdout.buffer.write(pickle.dumps(objects))
else:
    raise RuntimeError(sys.argv[1])
"""


def _make_objects():
    return {
        'key_default': comparison.key_cmp(),
        'key_cmp': comparison.key_cmp(comparison.cmp),
        'key_hash_eq_id_cmp': comparison.key_cmp(comparison.hash_eq_id_cmp),
        'key_custom': comparison.key_cmp(operator.sub),
        'attr_unbound': functions.attrsetter('value'),
        'attr_none': functions.attrsetter('value', None),
        'item_unbound': functions.itemsetter('value'),
        'item_none': functions.itemsetter('value', None),
    }


def _check_objects(objects) -> None:
    assert objects['key_default']((1, 'a'), (2, 'b')) == -1
    assert objects['key_cmp']((1, 'a'), (2, 'b')) == -1
    assert objects['key_hash_eq_id_cmp']((1, 'a'), (2, 'b')) == -1
    assert objects['key_custom']((1, 'a'), (2, 'b')) == -1

    class Target:
        value: object

    target: ta.Any = Target()
    objects['attr_unbound'](target, 420)
    assert target.value == 420
    objects['attr_none'](target)
    assert target.value is None

    target_dict: ta.Any = {}
    objects['item_unbound'](target_dict, 420)
    assert target_dict['value'] == 420
    objects['item_none'](target_dict)
    assert target_dict['value'] is None


@pytest.mark.skipif(
    comparison._comparison is None or functions._functions is None,  # noqa: SLF001
    reason='C extensions are not available',
)
def test_pickle_across_cext_and_pure_python() -> None:
    cext_payload = pickle.dumps(_make_objects())
    assert b'omcore.lang._comparison' not in cext_payload
    assert b'omcore.lang._functions' not in cext_payload

    subprocess.run(
        [sys.executable, '-c', _PURE_SCRIPT, 'load'],
        env={**os.environ, pycharm_runhack.ENABLED_ENV_VAR: '0'},
        input=cext_payload,
        check=True,
    )

    pure_proc = subprocess.run(
        [sys.executable, '-c', _PURE_SCRIPT, 'dump'],
        env={**os.environ, pycharm_runhack.ENABLED_ENV_VAR: '0'},
        check=True,
        stdout=subprocess.PIPE,
    )
    assert b'omcore.lang._comparison' not in pure_proc.stdout
    assert b'omcore.lang._functions' not in pure_proc.stdout

    pure_objects = pickle.loads(pure_proc.stdout)  # noqa: S301
    _check_objects(pure_objects)
    assert type(pure_objects['key_default']).__module__ == 'omcore.lang._comparison'
    assert type(pure_objects['attr_unbound']).__module__ == 'omcore.lang._functions'
