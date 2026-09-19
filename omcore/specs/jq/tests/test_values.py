import collections.abc
import typing as ta

import pytest

from ..errors import JqCycleError
from ..errors import JqTypeError
from ..options import JqValueOptions
from ..options import ObjectKeyPolicy
from ..values import JqValueOps


##


class CustomSequence(collections.abc.Sequence):
    def __init__(self, values):
        super().__init__()

        self._values = values

    def __getitem__(self, item):
        return self._values[item]

    def __len__(self):
        return len(self._values)


class CustomMapping(collections.abc.Mapping):
    def __init__(self, values):
        super().__init__()

        self._values = values

    def __getitem__(self, item):
        return self._values[item]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class ExplodingKeyMapping(CustomMapping):
    def items(self):
        raise AssertionError('mapping was eagerly traversed')


def test_truth_equality_and_order():
    ops = JqValueOps()
    assert not ops.truthy(None)
    assert not ops.truthy(False)
    values: tuple[ta.Any, ...] = (True, 0, 0.0, '', [], {})
    for value in values:
        assert ops.truthy(value)

    assert ops.equal(1, 1.0)
    assert not ops.equal(True, 1)
    assert ops.equal({'a': 1, 'b': [2]}, {'b': [2.0], 'a': 1.0})
    assert ops.sort([{}, [], 'x', 1, True, False, None]) == [None, False, True, 1, 'x', [], {}]


def test_custom_collections_and_key_policies():
    assert JqValueOps().equal(CustomSequence([1, 2]), [1.0, 2.0])
    assert JqValueOps().equal(CustomMapping({'x': 1}), {'x': 1.0})

    with pytest.raises(JqTypeError):
        JqValueOps().object_dict({1: 'x'})

    ignoring = JqValueOps(JqValueOptions(object_key_policy=ObjectKeyPolicy.IGNORE))
    assert ignoring.object_dict({1: 'x', 'a': 'y'}) == {'a': 'y'}

    def stringify(value):
        if not isinstance(value, int):
            raise TypeError(value)
        return str(value % 2)

    stringifying = JqValueOps(JqValueOptions(object_key_stringifier=stringify))
    assert stringifying.object_dict({1: 'first', 3: 'last'}) == {'1': 'last'}

    lazy = ExplodingKeyMapping({'wanted': 1, 2: 'invalid'})
    assert JqValueOps().index(lazy, 'wanted') == 1
    assert JqValueOps().has(lazy, 'wanted')


def test_copy_on_write_paths_and_sharing():
    ops = JqValueOps()
    shared = [{'n': index} for index in range(10)]
    root: dict[str, ta.Any] = {'items': shared, 'other': {'untouched': True}}

    changed = ops.setpath(root, ['items', 3, 'n'], 99)
    assert changed == {
        'items': [{'n': 0}, {'n': 1}, {'n': 2}, {'n': 99}, {'n': 4}, {'n': 5}, {'n': 6}, {'n': 7}, {'n': 8}, {'n': 9}],
        'other': {'untouched': True},
    }
    assert changed is not root
    assert changed['items'] is not shared
    assert changed['items'][2] is shared[2]
    assert changed['items'][3] is not shared[3]
    assert changed['other'] is root['other']
    assert root['items'][3]['n'] == 3

    assert ops.delpaths([0, 1, 2, 3], [[0], [2]]) == [1, 3]
    assert ops.setpath(None, ['a', 2], 'x') == {'a': [None, None, 'x']}


def test_cycles_are_rejected_when_traversed():
    value: list[ta.Any] = []
    value.append(value)
    with pytest.raises(JqCycleError):
        JqValueOps().validate(value)
