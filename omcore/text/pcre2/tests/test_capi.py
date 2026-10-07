# @om-precheck-allow-any-unicode
import array
import collections
import importlib
import os.path
import subprocess
import sys
import types

import pytest

from .. import _pcre2 as pcre2
from . import capiclients
from .patterns import GPT4_PATTERN
from .spans import find_spans


##


# The client is compiled when the first of these asks for it, which is only worth doing once: this keeps them all on the
# one xdist worker.
pytestmark = pytest.mark.xdist_group('pcre2-capiclient')


TEXTS = [
    b"Hello world! I'm fine, you're not.",
    '中文123abc４５６７ héllo wörld'.encode(),
    b'line one\r\n\r\n  line two   \n',
    b'',
    b'the quick brown fox jumps over the lazy dog ' * 50,
]


def test_capsule():
    assert isinstance(pcre2.capi, types.CapsuleType)


def test_client_is_not_importable(capiclient):
    # It is loaded from where it was built, by path, and is no part of the package.
    assert capiclient.__name__ == capiclients.CAPICLIENT_NAME
    assert capiclients.CAPICLIENT_NAME not in sys.modules
    assert not capiclient.__file__.startswith(os.path.dirname(__file__) + os.sep)
    with pytest.raises(ImportError):
        importlib.import_module(capiclients.CAPICLIENT_NAME)


def test_client_loads_before_the_binding(capiclient_file):
    # Everything else here imports _pcre2 before the client, which hides a client that depends on that order.
    subprocess.run(
        [sys.executable, '-m', capiclients.__name__, capiclient_file],
        env={**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)},
        check=True,
        timeout=60,
    )


def test_find_spans(capiclient):
    code = pcre2.compile(GPT4_PATTERN.encode(), pcre2.UTF | pcre2.UCP)
    for text in TEXTS:
        assert capiclient.find_spans(code, text) == find_spans(code, text)

    code = pcre2.compile(b'a*')
    assert capiclient.find_spans(code, b'baac') == [(0, 0), (1, 3), (3, 3), (4, 4)]


@pytest.mark.parametrize('num_threads', [1, 2, 8])
def test_count_chunks(capiclient, num_threads):
    code = pcre2.compile(GPT4_PATTERN.encode(), pcre2.UTF | pcre2.UCP)
    texts = TEXTS * 40

    expected = collections.Counter(
        bytes(text[s:e])
        for text in texts
        for s, e in find_spans(code, text)
    )

    assert capiclient.count_chunks(code, texts, num_threads) == expected
    assert capiclient.count_chunks(code, iter(texts), num_threads) == expected
    assert capiclient.count_chunks(code, [memoryview(text) for text in texts], num_threads) == expected


def test_only_a_code_is_accepted(capiclient):
    for obj in [object(), b'a', pcre2.MatchData.create(1), pcre2.Code]:
        with pytest.raises(TypeError, match='expected Code'):
            capiclient.find_spans(obj, b'a')


def test_match_errors_surface(capiclient):
    code = pcre2.compile(b'.', pcre2.UTF)
    with pytest.raises(RuntimeError, match='UTF-8'):
        capiclient.find_spans(code, b'\xff')
    with pytest.raises(RuntimeError, match='UTF-8'):
        capiclient.count_chunks(code, [b'ok', b'\xff', b'ok'], 4)


def test_match_context(capiclient):
    code = pcre2.compile(rb'(a+)+$')
    subject = b'a' * 40 + b'b'
    context = pcre2.MatchContext.create(match_limit=1000)

    with pytest.raises(RuntimeError, match='match limit exceeded'):
        capiclient.find_spans(code, subject, context)
    with pytest.raises(RuntimeError, match='match limit exceeded'):
        capiclient.count_chunks(code, [b'aaa', subject] * 20, 4, context)

    assert capiclient.find_spans(code, b'aaa', context) == [(0, 3)]
    assert capiclient.find_spans(code, b'aaa', None) == [(0, 3)]
    assert capiclient.count_chunks(code, [b'aaa'] * 20, 4, context) == {b'aaa': 20}


def test_only_a_match_context_is_accepted(capiclient):
    code = pcre2.compile(b'a')
    for obj in [object(), 1000, code, pcre2.MatchData.create(1), pcre2.MatchContext]:
        with pytest.raises(TypeError, match='expected MatchContext'):
            capiclient.find_spans(code, b'a', obj)
        with pytest.raises(TypeError, match='expected MatchContext'):
            capiclient.count_chunks(code, [b'a'], 1, obj)


def test_only_immutable_buffers_are_accepted(capiclient):
    code = pcre2.compile(b'a')
    for obj in [
        bytearray(b'a'),
        memoryview(bytearray(b'a')),
        memoryview(bytearray(b'a')).toreadonly(),
        array.array('B', b'a'),
    ]:
        with pytest.raises(BufferError, match='expected bytes'):
            capiclient.find_spans(code, obj)
        with pytest.raises(BufferError, match='expected bytes'):
            capiclient.count_chunks(code, [b'a', obj])

    assert capiclient.find_spans(code, memoryview(b'xa')[1:]) == [(0, 1)]


def test_invalid_utf_matching(capiclient):
    code = pcre2.compile(rb'\w', pcre2.UTF | pcre2.MATCH_INVALID_UTF)
    subject = b'ab\xffcd'
    assert capiclient.find_spans(code, subject) == find_spans(code, subject) == [(0, 1), (1, 2), (3, 4), (4, 5)]


def test_substitute(capiclient):
    # Through entries appended to the capsule's table after its first version.
    code = pcre2.compile(rb'(\w+)@(\w+)', pcre2.UTF | pcre2.UCP)
    subject = 'a@b çé@d'.encode()

    for replacement, options in [
        (b'$2@$1', 0),
        (b'$2@$1', pcre2.SUBSTITUTE_GLOBAL),
        (b'<$1>' * 100, pcre2.SUBSTITUTE_GLOBAL),
        (b'', pcre2.SUBSTITUTE_GLOBAL),
    ]:
        assert capiclient.substitute(code, subject, replacement, options) == (
            code.substitute(subject, replacement, options=options)
        )

    with pytest.raises(RuntimeError, match='invalid replacement string'):
        capiclient.substitute(code, subject, b'$')
    with pytest.raises(BufferError, match='expected bytes'):
        capiclient.substitute(code, bytearray(subject), b'x')

    slow = pcre2.compile(rb'(a+)+$')
    with pytest.raises(RuntimeError, match='match limit exceeded'):
        capiclient.substitute(slow, b'a' * 40 + b'b', b'x', 0, pcre2.MatchContext.create(match_limit=1000))


def test_dfa_match(capiclient):
    # Through the entry appended to the capsule's table after the others.
    code = pcre2.compile(rb'cat(er(pillar)?)?')
    assert capiclient.dfa_match_lengths(code, b'the caterpillar') == [11, 5, 3]
    assert capiclient.dfa_match_lengths(code, b'the dog') == []

    with pytest.raises(RuntimeError, match='workspace size exceeded'):
        capiclient.dfa_match_lengths(code, b'the caterpillar', 20)
    with pytest.raises(RuntimeError, match='not supported for DFA matching'):
        capiclient.dfa_match_lengths(pcre2.compile(rb'(a)\1'), b'aa')
