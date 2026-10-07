import array
import gc

import pytest

from .. import _pcre2 as pcre2


##


def test_match():
    code = pcre2.compile(rb'(\w+)@(\w+)')
    md = pcre2.MatchData.create_from_pattern(code)
    assert md.ovector_count == 3
    assert md.ovector == (pcre2.UNSET,) * 6

    assert code.match(b'  bob@example ', md) == 3
    assert md.ovector == (2, 13, 2, 5, 6, 13)


def test_no_match():
    code = pcre2.compile(b'abc')
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'nope', md) == pcre2.ERROR_NOMATCH
    assert md.ovector == (pcre2.UNSET, pcre2.UNSET)
    assert md.next_match() is None


def test_unset_groups():
    assert pcre2.UNSET == -1

    code = pcre2.compile(b'(a)|(b)|(c)')
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'b', md) == 3
    assert md.ovector == (0, 1, -1, -1, 0, 1, -1, -1)


def test_small_ovector():
    code = pcre2.compile(b'(a)(b)(c)')
    md = pcre2.MatchData.create(2)
    assert md.ovector_count == 2
    assert code.match(b'abc', md) == 0
    assert md.ovector == (0, 3, 0, 1)


def test_start_offset_and_anchoring():
    code = pcre2.compile(b'ab')
    md = pcre2.MatchData.create_from_pattern(code)

    assert code.match(b'ab ab', md, 1) == 1
    assert md.ovector == (3, 5)

    assert code.match(b'ab ab', md, 1, pcre2.ANCHORED) == pcre2.ERROR_NOMATCH
    assert code.match(b'ab ab', md, start_offset=3, options=pcre2.ANCHORED | pcre2.ENDANCHORED) == 1

    assert code.match(b'ab ab', md, options=pcre2.ENDANCHORED) == 1
    assert md.ovector == (3, 5)


def test_partial():
    code = pcre2.compile(b'abc')
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'xab', md, options=pcre2.PARTIAL_SOFT) == pcre2.ERROR_PARTIAL
    assert md.ovector == (1, 3)
    assert md.next_match() is None


def test_utf_is_not_implied():
    subject = 'caféé!'.encode()

    code = pcre2.compile('é+'.encode(), pcre2.UTF)
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(subject, md) == 1
    assert md.ovector == (3, 7)

    # Without UTF the pattern is two one-byte characters, with the quantifier on the second alone.
    code = pcre2.compile('é+'.encode())
    assert code.match(subject, md) == 1
    assert md.ovector == (3, 5)


def test_invalid_utf():
    code = pcre2.compile(b'.', pcre2.UTF)
    md = pcre2.MatchData.create_from_pattern(code)

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(b'ab\xffcd', md)
    assert pcre2.ERROR_UTF8_ERR21 <= ei.value.code <= pcre2.ERROR_UTF8_ERR1
    assert ei.value.offset == 2
    assert md.next_match() is None

    code = pcre2.compile(b'c', pcre2.UTF | pcre2.MATCH_INVALID_UTF)
    assert code.match(b'ab\xffcd', md) == 1
    assert md.ovector == (3, 4)


def test_match_errors():
    code = pcre2.compile(b'abc')
    md = pcre2.MatchData.create_from_pattern(code)

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(b'abc', md, 4)
    assert ei.value.code == pcre2.ERROR_BADOFFSET
    assert ei.value.offset is None

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(b'abc', md, options=pcre2.UTF)
    assert ei.value.code == pcre2.ERROR_BADOPTION

    with pytest.raises(ValueError):  # noqa
        code.match(b'abc', md, -1)

    assert code.match(b'abc', md) == 1


def test_match_arguments():
    code = pcre2.compile(b'abc')
    md = pcre2.MatchData.create_from_pattern(code)

    with pytest.raises(TypeError):
        code.match('abc', md)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        code.match(b'abc', None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        code.match(b'abc')  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        pcre2.MatchData.create_from_pattern(b'abc')  # type: ignore[arg-type]
    with pytest.raises(OverflowError):
        code.match(b'abc', md, 0, -1)


def test_subjects():
    code = pcre2.compile(b'ab')
    md = pcre2.MatchData.create_from_pattern(code)

    for subject in [
        b'xxabxx',
        bytearray(b'xxabxx'),
        memoryview(b'xxabxx'),
        array.array('B', b'xxabxx'),
    ]:
        assert code.match(subject, md) == 1  # type: ignore[arg-type]
        assert md.ovector == (2, 4)

    assert code.match(memoryview(b'xxabxx')[:3], md) == pcre2.ERROR_NOMATCH
    assert code.match(memoryview(b'xxabxx')[1:], md) == 1
    assert md.ovector == (1, 3)

    with pytest.raises(BufferError):
        code.match(memoryview(b'xxabxx')[::2], md)


def test_long_subject():
    code = pcre2.compile(b'needle')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'hay ' * 100_000 + b'needle'
    assert code.match(subject, md) == 1
    assert md.ovector == (400_000, 400_006)


def test_subject_is_held_while_matched():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)

    subject = bytearray(b'aaa')
    assert code.match(subject, md) == 1
    with pytest.raises(BufferError):
        subject.extend(b'a')
    assert md.next_match() == (1, 0)

    assert code.match(b'b', md) == pcre2.ERROR_NOMATCH
    subject.extend(b'a')


def test_subject_and_code_outlive_their_references():
    md = pcre2.MatchData.create(1)
    assert pcre2.compile(b'a', pcre2.UTF).match(bytes(bytearray(b'a' * 1000)), md) == 1
    gc.collect()
    assert md.next_match() == (1, 0)


def test_match_data_is_not_reentrant():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)

    class Reentrant:
        def __buffer__(self, flags):
            code.match(b'a', md)
            raise NotImplementedError

    with pytest.raises(RuntimeError, match='already in use'):
        code.match(Reentrant(), md)

    assert code.match(b'a', md) == 1
