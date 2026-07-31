import pytest

from ..bytes import make_bytes_encoding_codec
from ..registry import CodecRegistry
from ..registry import lookup


def test_registry():
    assert lookup('utf-8').new().encode('hi') == b'hi'


def test_registry_aliases_and_types():
    codec = make_bytes_encoding_codec(
        'test-bytes',
        ['test-alias'],
        bytes.upper,
        bytes.lower,
    )
    registry = CodecRegistry().register(codec)

    assert registry.lookup('test-bytes') is codec
    assert registry.lookup('test_alias') is codec
    assert registry.lookup_type(type(codec)) == [codec]
    assert registry.all() == frozenset({'test-bytes'})


def test_register_rejects_collisions_within_single_call_atomically():
    first = make_bytes_encoding_codec(
        'first',
        ['shared'],
        bytes.upper,
        bytes.lower,
    )
    second = make_bytes_encoding_codec(
        'second',
        ['shared'],
        bytes.upper,
        bytes.lower,
    )
    registry = CodecRegistry()

    with pytest.raises(KeyError, match='shared'):
        registry.register(first, second)

    assert registry.all() == frozenset()
