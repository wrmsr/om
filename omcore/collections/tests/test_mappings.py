import typing as ta

import pytest

from ..mappings import MissingDict
from ..mappings import dict_factory
from ..mappings import guarded_map_update
from ..mappings import map_contains
from ..mappings import multikey_dict


def test_multikey_dict():
    assert multikey_dict({
        ('a', 'b'): 1,
        'c': 2,
    }) == {
        'a': 1,
        'b': 1,
        'c': 2,
    }

    assert multikey_dict({
        'outer': {
            ('a', 'b'): 1,
        },
    }, deep=True) == {
        'outer': {
            'a': 1,
            'b': 1,
        },
    }


def test_guarded_map_update():
    dst = {'a': 1}

    assert guarded_map_update(dst, {'b': 2}, {'c': 3}) is dst
    assert dst == {'a': 1, 'b': 2, 'c': 3}
    with pytest.raises(KeyError) as exc_info:
        guarded_map_update(dst, {'b': 4})
    assert exc_info.value.args == ('b',)


def test_map_contains():
    class GetitemOnly:
        def __getitem__(self, key):
            if key == 'present':
                return key
            raise KeyError(key)

    mapping = GetitemOnly()
    assert map_contains(mapping, 'present')  # type: ignore[arg-type]
    assert not map_contains(mapping, 'missing')  # type: ignore[arg-type]


def test_missing_dict():
    calls: list[str] = []

    def missing(key: str) -> str:
        calls.append(key)
        return key.upper()

    dct: MissingDict[str, str] = MissingDict(missing)

    assert dct['a'] == 'A'
    assert dct['a'] == 'A'
    assert calls == ['a']
    assert dct == {'a': 'A'}

    with pytest.raises(TypeError):
        MissingDict(None)  # type: ignore[arg-type]


def test_dict_factory():
    assert dict_factory() is dict

    a: list[int] = []
    b: list[int] = []
    identity_mapping: ta.MutableMapping[list[int], int] = dict_factory(identity=True)()
    identity_mapping[a] = 1
    identity_mapping[b] = 2
    assert identity_mapping[a] == 1
    assert identity_mapping[b] == 2
    assert list(identity_mapping.values()) == [1, 2]
