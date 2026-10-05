import collections.abc
import typing as ta

import pytest

from ..errors import JqCycleError
from ..errors import JqTypeError
from ..options import JqValueOptions
from ..options import ObjectKeyPolicy
from ..program import compile_jq
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


def test_item_updates():
    ops = JqValueOps()

    assert ops.with_item(None, 'a', 1) == {'a': 1}
    assert ops.with_item(None, 2, 'x') == [None, None, 'x']
    assert ops.with_item(CustomMapping({'a': 1}), 'b', 2) == {'a': 1, 'b': 2}
    assert ops.with_item(CustomSequence([1, 2]), 0, 'x') == ['x', 2]
    assert ops.with_item([1], 3, 'x') == [1, None, None, 'x']

    assert ops.without_item(CustomMapping({'a': 1, 'b': 2}), 'a') == {'b': 2}
    assert ops.without_item(CustomSequence([1, 2, 3]), 1) == [1, 3]

    obj = {'a': 1}
    arr = [1, 2]
    assert ops.with_item(obj, 'a', 2) is not obj
    assert ops.without_item(arr, 0) is not arr
    assert (obj, arr) == ({'a': 1}, [1, 2])


def test_deleting_nothing_shares_everything():
    ops = JqValueOps()
    root: dict[str, ta.Any] = {'a': {'b': [1, 2]}, 'c': 1}
    assert ops.delpaths(root, [['nope'], ['a', 'nope'], ['a', 'b', 5], ['c', 'x']]) is root

    changed = ops.delpaths(root, [['a', 'b', 0], ['nope']])
    assert changed == {'a': {'b': [2]}, 'c': 1}
    assert root == {'a': {'b': [1, 2]}, 'c': 1}


class RecordingValueOps(JqValueOps):
    def __init__(self) -> None:
        super().__init__()

        self.calls: list[tuple[ta.Any, ...]] = []

    def with_item(self, container, key, item):
        self.calls.append(('with', key))
        return super().with_item(container, key, item)

    def without_item(self, container, key):
        self.calls.append(('without', key))
        return super().without_item(container, key)


@pytest.mark.parametrize(('source', 'calls'), [
    ('.a.b = 1', [('with', 'b'), ('with', 'a')]),
    ('.xs[1] += 1', [('with', 1), ('with', 'xs')]),
    ('.a |= (.b = 2)', [('with', 'b'), ('with', 'a')]),
    ('.xs |= map(. * 2)', [('with', 'xs')]),
    ('.new[1] = 1', [('with', 1), ('with', 'new')]),
    ('del(.a.b)', [('without', 'b'), ('with', 'a')]),
    ('del(.xs[0], .xs[2])', [('without', 2), ('without', 0), ('with', 'xs')]),
    ('.xs |= map(select(. > 1))', [('with', 'xs')]),
    ('.xs[] |= empty', None),
    ('setpath(["a", "b"]; 3)', [('with', 'b'), ('with', 'a')]),
    ('delpaths([["a", "b"]])', [('without', 'b'), ('with', 'a')]),
    ('to_entries | from_entries', None),
    ('.a.b', []),
    ('. + {c: 1}', []),
])
def test_path_updates_are_made_of_item_updates(source, calls):
    def new_tree():
        return {'a': {'b': 1}, 'xs': [1, 2, 3]}

    ops = RecordingValueOps()
    program = compile_jq(source, value_ops=ops)
    assert program.value_ops is ops
    assert program.value_options is ops.options

    assert list(program.evaluate(new_tree())) == list(compile_jq(source).evaluate(new_tree()))
    if calls is not None:
        assert ops.calls == calls
