# @om-precheck-allow-any-unicode
import copy
import mmap
import pickle
import re
import threading

import pytest

from ... import _pcre2 as pcre2
from ... import re as pre
from .helpers import found


##


def test_surface_is_that_of_re():
    for name in [
        'compile', 'search', 'match', 'fullmatch', 'finditer', 'findall', 'split', 'sub', 'subn', 'escape', 'purge',
        'Pattern', 'Match', 'error', 'PatternError', 'RegexFlag',
        'A', 'ASCII', 'DEBUG', 'DOTALL', 'I', 'IGNORECASE', 'L', 'LOCALE', 'M', 'MULTILINE', 'NOFLAG', 'S', 'U',
        'UNICODE', 'VERBOSE', 'X',
    ]:
        assert hasattr(pre, name), name

    # The flags and the exception are the standard library's own, so code written for one works with the other.
    assert pre.IGNORECASE is re.IGNORECASE
    assert pre.error is re.error is pre.PatternError


def test_compile():
    pattern = pre.compile(r'(?P<user>\w+)@(?P<host>\w+)', pre.I)
    assert isinstance(pattern, pre.Pattern)
    assert pattern.pattern == r'(?P<user>\w+)@(?P<host>\w+)'
    assert pattern.flags == re.IGNORECASE | re.UNICODE
    assert pattern.groups == 2
    assert pattern.groupindex == {'user': 1, 'host': 2}

    assert pre.compile(pattern) is pattern
    with pytest.raises(ValueError):  # noqa
        pre.compile(pattern, pre.I)

    with pytest.raises(TypeError):
        pre.compile(1)  # type: ignore[type-var]
    with pytest.raises(TypeError):
        pre.compile(bytearray(b'a'))  # type: ignore[type-var]


def test_compile_is_cached():
    pre.purge()
    assert pre.compile('a+') is pre.compile('a+')
    assert pre.compile('a+') is not pre.compile('a+', pre.I)
    assert pre.compile('a+') is not pre.compile(b'a+')

    before = pre.compile('a+')
    pre.purge()
    assert pre.compile('a+') is not before
    assert pre.compile('a+') == before


def test_errors_are_res():
    with pytest.raises(re.PatternError) as ei:
        pre.compile('ab(c')
    assert ei.value.pattern == 'ab(c'
    assert ei.value.pos == 4
    assert ei.value.msg == 'missing closing parenthesis'
    assert isinstance(ei.value.__cause__, pcre2.CompileError)

    # Where the pattern PCRE2 was given is not the one that was written, where in it is not passed on.
    with pytest.raises(re.PatternError) as ei:
        pre.compile(r'\w(c')
    assert ei.value.pos is None

    with pytest.raises(re.PatternError):
        pre.sub('a', r'\q', 'a')
    with pytest.raises(IndexError):
        pre.sub('a', r'\g<nope>', 'a')


def test_flags():
    assert pre.compile('a').flags == re.compile('a').flags == re.UNICODE
    assert pre.compile('a', pre.A).flags == re.compile('a', re.ASCII).flags
    assert pre.compile(b'a').flags == re.compile(b'a').flags == 0
    assert pre.compile('(?ims)a').flags == re.compile('(?ims)a').flags
    assert pre.compile('a', pre.X).flags == re.VERBOSE | re.UNICODE

    with pytest.raises(ValueError, match='LOCALE'):
        pre.compile(b'a', pre.L)
    with pytest.raises(ValueError, match='incompatible'):
        pre.compile('a', pre.A | pre.U)
    with pytest.raises(ValueError, match='bytes pattern'):
        pre.compile(b'a', pre.U)


def test_str_and_bytes_do_not_mix():
    with pytest.raises(TypeError, match='cannot use a string pattern on a bytes-like object'):
        pre.search('a', b'a')  # type: ignore[type-var]
    with pytest.raises(TypeError, match='cannot use a bytes pattern on a string-like object'):
        pre.search(b'a', 'a')  # type: ignore[type-var]
    with pytest.raises(TypeError, match='expected str'):
        pre.sub('a', b'x', 'a')
    with pytest.raises(TypeError, match='expected a bytes-like object'):
        pre.sub(b'a', 'x', b'a')


def test_bytes_like_subjects():
    pattern = pre.compile(rb'(\d+)-(\d+)')
    for subject in [b'x 12-34 y', bytearray(b'x 12-34 y'), memoryview(b'x 12-34 y')]:
        m = pattern.search(subject)  # type: ignore[arg-type]
        assert m is not None
        assert m.group() == b'12-34'
        assert type(m.group()) is bytes
        assert m.span(2) == (5, 7)
        assert pattern.findall(subject) == [(b'12', b'34')]  # type: ignore[arg-type]
        assert pattern.sub(rb'\2-\1', subject) == b'x 34-12 y'  # type: ignore[arg-type]

    with mmap.mmap(-1, 16) as mapped:
        mapped.write(b'x 12-34 y')
        assert found(pattern.search(mapped)).span() == (2, 7)  # type: ignore[arg-type]


def test_offsets_are_characters():
    subject = 'héllo wörld, 中文 and 😀 too'
    for m, expected in zip(pre.finditer(r'\w+', subject), re.finditer(r'\w+', subject), strict=True):
        assert m.span() == expected.span()
        assert subject[m.start():m.end()] == m.group() == expected.group()

    behind = found(pre.compile(r'(?<=中)文').search(subject, 8, 20))
    assert (behind.span(), behind.pos, behind.endpos, behind.string) == ((14, 15), 8, 20, subject)


def test_pos_and_endpos():
    # Starting further in does not make that the start of the subject, and stopping short does make that the end.
    pattern = pre.compile(r'^b|c$')
    assert found(pattern.search('bc', 0)).span() == (0, 1)
    assert found(pattern.search('abc', 1)).span() == (2, 3)
    assert pattern.search('abc', 0, 2) is None
    assert found(pattern.search('abcd', 0, 3)).span() == (2, 3)

    pattern = pre.compile('a')
    assert found(pattern.search('a', -5, 100)).span() == (0, 1)
    assert pattern.search('a', 1) is None
    assert pattern.search('aa', 2, 1) is None
    assert list(pattern.finditer('aa', 2, 1)) == []
    assert pattern.findall('aaa', 1, 2) == ['a']


def test_match_object():
    m = pre.search(r'(?P<user>\w+)@(?P<host>\w+)(\.com)?', 'mail bób@exämple now')
    assert m is not None
    assert m.group() == m[0] == 'bób@exämple'
    assert m.group(1, 'host') == ('bób', 'exämple')
    assert m['user'] == 'bób'
    assert m.groups() == ('bób', 'exämple', None)
    assert m.groups('') == ('bób', 'exämple', '')
    assert m.groupdict() == {'user': 'bób', 'host': 'exämple'}
    assert m.start('host') == 9
    assert m.span(3) == (-1, -1)
    assert m.regs == ((5, 16), (5, 8), (9, 16), (-1, -1))
    assert (m.lastindex, m.lastgroup) == (2, 'host')
    assert m.expand(r'\g<host>!\1\3') == 'exämple!bób'
    assert m.re.pattern == r'(?P<user>\w+)@(?P<host>\w+)(\.com)?'
    assert repr(m).endswith("Match object; span=(5, 16), match='bób@exämple'>")
    assert copy.copy(m) is m
    assert bool(m)

    for bad in ['nope', 4, -1, 1.5, b'user']:
        with pytest.raises(IndexError, match='no such group'):
            m.group(bad)


def test_callable_replacement():
    assert pre.sub(r'(\w)(\w*)', lambda m: m.group(1).upper() + m.group(2), 'héllo wörld') == 'Héllo Wörld'
    assert pre.subn(rb'\d', lambda m: bytes([m.group()[0] + 1]), b'a1b2') == (b'a2b3', 2)

    seen = []

    def note(m):
        seen.append((m.span(), m.string, m.pos, m.endpos))
        return ''

    assert pre.sub(r'b', note, 'abcb') == 'ac'
    assert seen == [((1, 2), 'abcb', 0, 4), ((3, 4), 'abcb', 0, 4)]


def test_pattern_object():
    pattern = pre.compile(r'a\Z', pre.I | pre.M)
    assert repr(pattern).endswith(".compile('a\\\\Z', re.IGNORECASE|re.MULTILINE)")
    assert repr(pre.compile(b'a')).endswith(".compile(b'a')")

    assert pattern == pre.Pattern(r'a\Z', pre.I | pre.M)
    assert hash(pattern) == hash(pre.Pattern(r'a\Z', pre.I | pre.M))
    assert pattern != pre.compile(r'a\Z')
    assert pattern != pre.compile(rb'a\Z', pre.I | pre.M)
    assert pattern != re.compile(r'a\Z', pre.I | pre.M)

    assert copy.deepcopy(pattern) is pattern
    restored = pickle.loads(pickle.dumps(pattern))  # noqa
    assert restored == pattern
    assert found(restored.search('xA')).span() == (1, 2)


def test_match_context():
    # The one thing here `re` has nothing like: limits, without which a pattern such as this takes as long as it takes.
    limited = pre.Pattern(r'(a+)+$', match_context=pcre2.MatchContext.create(match_limit=1000))
    assert found(limited.search('aaa')).span() == (0, 3)
    with pytest.raises(pcre2.MatchError) as ei:
        limited.search('a' * 40 + 'b')
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT

    assert limited != pre.Pattern(r'(a+)+$')
    with pytest.raises(TypeError):
        pickle.dumps(limited)


def test_escape():
    for text in ['a.b*c', 'a b', r'\d[x]', 'é-中', '']:
        assert pre.escape(text) == re.escape(text)
        assert pre.fullmatch(pre.escape(text), text)
    assert pre.fullmatch(pre.escape(b'a.b[c]\xff'), b'a.b[c]\xff')


def test_pattern_is_shared_between_threads():
    pattern = pre.compile(r'(\w+)@(\w+)')
    subject = 'bób@exämple, a@b, ' * 50
    expected = [m.span() for m in re.finditer(r'(\w+)@(\w+)', subject)]

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results: list = [None] * num_threads

    def run(i):
        barrier.wait()
        out: list = []
        for _ in range(5):
            out.append([m.span() for m in pattern.finditer(subject)])
            out.append(pattern.sub(r'\2@\1', subject) == re.sub(r'(\w+)@(\w+)', r'\2@\1', subject))
        results[i] = out

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [expected, True] * 5
