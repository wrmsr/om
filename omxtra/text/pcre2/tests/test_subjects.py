import array

import pytest

from .. import _pcre2 as pcre2
from .spans import find_spans


##


def test_utf_pattern_needs_an_immutable_subject():
    md = pcre2.MatchData.create(1)

    for code in [
        pcre2.compile(b'a', pcre2.UTF),
        pcre2.compile(b'(*UTF)a'),
        pcre2.compile(b'a', pcre2.UTF | pcre2.MATCH_INVALID_UTF),
    ]:
        for subject in [
            bytearray(b'a'),
            memoryview(bytearray(b'a')),
            memoryview(bytearray(b'a')).toreadonly(),
            array.array('B', b'a'),
        ]:
            with pytest.raises(BufferError, match='could change during the match'):
                code.match(subject, md)
            assert md.next_match() is None

        for subject in [
            b'a',
            memoryview(b'a'),
            memoryview(memoryview(b'xa'))[1:],
        ]:
            assert code.match(subject, md) == 1


def test_no_utf_check_vouches_for_a_subject():
    code = pcre2.compile(b'a', pcre2.UTF)
    md = pcre2.MatchData.create(1)

    subject = bytearray(b'ba')
    assert code.match(subject, md, options=pcre2.NO_UTF_CHECK) == 1
    assert md.ovector == (1, 2)
    assert md.next_match() == (2, 0)

    # The promise is made call by call.
    with pytest.raises(BufferError):
        code.match(subject, md)


def test_other_patterns_take_any_subject():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create(1)
    for subject in [
        b'a',
        bytearray(b'a'),
        memoryview(bytearray(b'a')),
        array.array('B', b'a'),
    ]:
        assert code.match(subject, md) == 1


def test_writable_subject_is_seen_as_it_is_now():
    code = pcre2.compile(b'b')
    md = pcre2.MatchData.create(1)

    subject = bytearray(b'ab')
    assert code.match(subject, md) == 1
    assert md.ovector == (1, 2)

    subject[0:2] = b'ba'
    assert code.match(subject, md) == 1
    assert md.ovector == (0, 1)


def test_writable_pattern():
    pattern = bytearray('é+'.encode())
    code = pcre2.compile(pattern, pcre2.UTF)
    pattern[:] = b'zzz'

    md = pcre2.MatchData.create(1)
    assert code.match('caféé'.encode(), md) == 1
    assert md.ovector == (3, 7)


def test_long_pattern():
    words = [f'word{i}'.encode() for i in range(2000)]
    code = pcre2.compile(b'|'.join(words) + b'|needle')
    md = pcre2.MatchData.create(1)
    assert code.match(b'hay needle hay', md) == 1
    assert md.ovector == (4, 10)

    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(b'|'.join(words) + b'|(needle')
    assert ei.value.code == 114


##


# A subject which has been matched once is not validated over again as a search moves through it, where that is safe.
# None of that may change an answer.


def test_offset_inside_a_character_is_still_refused():
    code = pcre2.compile(b'.', pcre2.UTF)
    md = pcre2.MatchData.create(1)
    subject = 'aéb'.encode()

    assert code.match(subject, md) == 1
    with pytest.raises(pcre2.MatchError) as ei:
        code.match(subject, md, 2)
    assert ei.value.code == pcre2.ERROR_BADUTFOFFSET

    assert code.match(subject, md) == 1
    assert code.match(subject, md, 1) == 1
    assert md.ovector == (1, 3)


def test_earlier_offsets_are_still_validated():
    code = pcre2.compile(b'b', pcre2.UTF)
    md = pcre2.MatchData.create(1)
    subject = b'\xffab'

    assert code.match(subject, md, 1) == 1
    assert code.match(subject, md, 2) == 1
    with pytest.raises(pcre2.MatchError) as ei:
        code.match(subject, md, 0)
    assert ei.value.offset == 0


def test_each_code_validates_for_itself():
    md = pcre2.MatchData.create(1)
    subject = b'a\xff'

    assert pcre2.compile(b'a').match(subject, md) == 1
    with pytest.raises(pcre2.MatchError) as ei:
        pcre2.compile(b'a', pcre2.UTF).match(subject, md)
    assert ei.value.offset == 1

    # A pattern matching invalid UTF succeeds without having found the subject valid.
    assert pcre2.compile(b'a', pcre2.UTF | pcre2.MATCH_INVALID_UTF).match(subject, md) == 1
    with pytest.raises(pcre2.MatchError) as ei:
        pcre2.compile(b'a', pcre2.UTF).match(subject, md)
    assert ei.value.offset == 1


def test_each_subject_is_validated():
    code = pcre2.compile(b'a', pcre2.UTF)
    md = pcre2.MatchData.create(1)

    assert code.match(b'aa', md) == 1
    with pytest.raises(pcre2.MatchError):
        code.match(b'a\xff', md, 0)
    with pytest.raises(pcre2.MatchError):
        code.match(memoryview(b'a\xff'), md, 0)


def test_invalid_utf_matching():
    code = pcre2.compile(rb'\w', pcre2.UTF | pcre2.MATCH_INVALID_UTF)
    assert find_spans(code, b'ab\xffcd') == [(0, 1), (1, 2), (3, 4), (4, 5)]


def test_spans_do_not_depend_on_the_kind_of_subject():
    code = pcre2.compile(rb'\p{L}+|\p{N}+', pcre2.UTF | pcre2.UCP)
    subject = 'héllo wörld 123 中文 '.encode() * 50
    expected = find_spans(code, subject)
    assert len(expected) == 200
    assert find_spans(code, memoryview(subject)) == expected
    assert find_spans(code, memoryview(b' ' + subject)[1:]) == expected
