import random

import pytest

from ..subjects import Subject
from ..subjects import Utf8Offsets


##


STRING = 'a\u00e9\U0001f642x\u4e2d'


def test_offsets_in_any_order():
    data = STRING.encode()
    byte_offsets = [len(STRING[:i].encode()) for i in range(len(STRING) + 1)]

    offsets = Utf8Offsets(data)
    assert [offsets.to_char(b) for b in byte_offsets] == list(range(len(STRING) + 1))

    offsets = Utf8Offsets(data)
    assert [offsets.to_char(b) for b in reversed(byte_offsets)] == list(reversed(range(len(STRING) + 1)))

    rng = random.Random(0)
    offsets = Utf8Offsets(data)
    for _ in range(100):
        i = rng.randrange(len(STRING) + 1)
        assert offsets.to_char(byte_offsets[i]) == i


def test_str_subject():
    subject = Subject(STRING, is_str=True)
    assert len(subject) == 5
    assert subject.data == STRING.encode()
    assert subject.to_byte(3) == 7
    assert subject.to_offset(7) == 3
    assert subject.slice(1, 7) == '\u00e9\U0001f642'

    ascii_subject = Subject('abc', is_str=True)
    assert ascii_subject.to_byte(2) == ascii_subject.to_offset(2) == 2


def test_bytes_subject():
    for string in [b'abc', bytearray(b'abc'), memoryview(b'abc')]:
        subject = Subject(string, is_str=False)
        assert subject.data is string
        assert subject.to_byte(2) == subject.to_offset(2) == 2
        assert subject.slice(1, 3) == b'bc'
        assert type(subject.slice(1, 3)) is bytes


def test_mismatched_subject():
    with pytest.raises(TypeError, match='cannot use a string pattern on a bytes-like object'):
        Subject(b'abc', is_str=True)
    with pytest.raises(TypeError, match='cannot use a bytes pattern on a string-like object'):
        Subject('abc', is_str=False)
