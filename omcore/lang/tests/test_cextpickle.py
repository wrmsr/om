import operator
import os.path
import pickle
import subprocess
import sys
import typing as ta

import pytest

from ...diag._pycharm import runhack as pycharm_runhack
from .. import comparison
from .. import functions


##


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

    with open(os.path.join(os.path.dirname(__file__), 'cextpickle_script.py')) as f:
        pure_script = f.read()

    subprocess.run(
        [sys.executable, '-c', pure_script, 'load'],
        env={**os.environ, pycharm_runhack.ENABLED_ENV_VAR: '0'},
        input=cext_payload,
        check=True,
    )

    pure_proc = subprocess.run(
        [sys.executable, '-c', pure_script, 'dump'],
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
