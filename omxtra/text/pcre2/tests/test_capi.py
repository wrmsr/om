import array
import collections
import os
import subprocess
import sys
import types

import pytest

from .. import _pcre2 as pcre2
from . import _capiclient
from .patterns import GPT4_PATTERN
from .spans import find_spans


##


TEXTS = [
    b"Hello world! I'm fine, you're not.",
    '中文123abc４５６７ héllo wörld'.encode(),
    b'line one\r\n\r\n  line two   \n',
    b'',
    b'the quick brown fox jumps over the lazy dog ' * 50,
]


def test_capsule():
    assert isinstance(pcre2.capi, types.CapsuleType)


def test_client_imports_before_the_binding():
    # Everything else here imports _pcre2 before the client, which hides a client that depends on that order.
    subprocess.run(
        [sys.executable, '-c', f'import {_capiclient.__name__}'],
        env={**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)},
        check=True,
        timeout=60,
    )


def test_find_spans():
    code = pcre2.compile(GPT4_PATTERN.encode(), pcre2.UTF | pcre2.UCP)
    for text in TEXTS:
        assert _capiclient.find_spans(code, text) == find_spans(code, text)

    code = pcre2.compile(b'a*')
    assert _capiclient.find_spans(code, b'baac') == [(0, 0), (1, 3), (3, 3), (4, 4)]


@pytest.mark.parametrize('num_threads', [1, 2, 8])
def test_count_chunks(num_threads):
    code = pcre2.compile(GPT4_PATTERN.encode(), pcre2.UTF | pcre2.UCP)
    texts = TEXTS * 40

    expected = collections.Counter(
        bytes(text[s:e])
        for text in texts
        for s, e in find_spans(code, text)
    )

    assert _capiclient.count_chunks(code, texts, num_threads) == expected
    assert _capiclient.count_chunks(code, iter(texts), num_threads) == expected
    assert _capiclient.count_chunks(code, [memoryview(text) for text in texts], num_threads) == expected


def test_only_a_code_is_accepted():
    for obj in [object(), b'a', pcre2.MatchData.create(1), pcre2.Code]:
        with pytest.raises(TypeError, match='expected Code'):
            _capiclient.find_spans(obj, b'a')


def test_match_errors_surface():
    code = pcre2.compile(b'.', pcre2.UTF)
    with pytest.raises(RuntimeError, match='UTF-8'):
        _capiclient.find_spans(code, b'\xff')
    with pytest.raises(RuntimeError, match='UTF-8'):
        _capiclient.count_chunks(code, [b'ok', b'\xff', b'ok'], 4)


def test_match_context():
    code = pcre2.compile(rb'(a+)+$')
    subject = b'a' * 40 + b'b'
    context = pcre2.MatchContext.create(match_limit=1000)

    with pytest.raises(RuntimeError, match='match limit exceeded'):
        _capiclient.find_spans(code, subject, context)
    with pytest.raises(RuntimeError, match='match limit exceeded'):
        _capiclient.count_chunks(code, [b'aaa', subject] * 20, 4, context)

    assert _capiclient.find_spans(code, b'aaa', context) == [(0, 3)]
    assert _capiclient.find_spans(code, b'aaa', None) == [(0, 3)]
    assert _capiclient.count_chunks(code, [b'aaa'] * 20, 4, context) == {b'aaa': 20}


def test_only_a_match_context_is_accepted():
    code = pcre2.compile(b'a')
    for obj in [object(), 1000, code, pcre2.MatchData.create(1), pcre2.MatchContext]:
        with pytest.raises(TypeError, match='expected MatchContext'):
            _capiclient.find_spans(code, b'a', obj)
        with pytest.raises(TypeError, match='expected MatchContext'):
            _capiclient.count_chunks(code, [b'a'], 1, obj)


def test_only_immutable_buffers_are_accepted():
    code = pcre2.compile(b'a')
    for obj in [
        bytearray(b'a'),
        memoryview(bytearray(b'a')),
        memoryview(bytearray(b'a')).toreadonly(),
        array.array('B', b'a'),
    ]:
        with pytest.raises(BufferError, match='expected bytes'):
            _capiclient.find_spans(code, obj)
        with pytest.raises(BufferError, match='expected bytes'):
            _capiclient.count_chunks(code, [b'a', obj])

    assert _capiclient.find_spans(code, memoryview(b'xa')[1:]) == [(0, 1)]


def test_invalid_utf_matching():
    code = pcre2.compile(rb'\w', pcre2.UTF | pcre2.MATCH_INVALID_UTF)
    subject = b'ab\xffcd'
    assert _capiclient.find_spans(code, subject) == find_spans(code, subject) == [(0, 1), (1, 2), (3, 4), (4, 5)]
