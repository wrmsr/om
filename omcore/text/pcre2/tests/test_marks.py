import gc

import pytest

from .. import _pcre2 as pcre2
from .spans import find_spans


##


MARKED_PATTERN = rb'(*MARK:first)a|(*MARK:second)b|(*MARK:third)c'


def test_mark():
    code = pcre2.compile(MARKED_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)

    for subject, mark in [
        (b'a', b'first'),
        (b'b', b'second'),
        (b'zzc', b'third'),
    ]:
        assert code.match(subject, md) == 1
        assert md.mark == mark


def test_no_mark():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)
    assert md.mark is None

    assert code.match(b'a', md) == 1
    assert md.mark is None


def test_mark_of_a_failed_match():
    code = pcre2.compile(MARKED_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)

    # A failed match reports the last mark it passed.
    assert code.match(b'q', md) == pcre2.ERROR_NOMATCH
    assert md.mark == b'third'
    assert md.next_match() is None

    assert pcre2.compile(b'a').match(b'q', md) == pcre2.ERROR_NOMATCH
    assert md.mark is None


def test_mark_of_a_partial_match():
    code = pcre2.compile(rb'(*MARK:here)abc')
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'xab', md, options=pcre2.PARTIAL_HARD) == pcre2.ERROR_PARTIAL
    assert md.mark == b'here'
    assert md.startchar == 1


def test_mark_is_dropped_when_a_match_raises():
    code = pcre2.compile(MARKED_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'a', md) == 1
    assert md.mark == b'first'

    with pytest.raises(pcre2.MatchError):
        code.match(b'a', md, 5)
    assert (md.mark, md.startchar) == (None, 0)


def test_mark_outlives_other_references_to_its_code():
    # A mark is a pointer into the compiled pattern, which the block has to keep alive - matched or not.
    md = pcre2.MatchData.create(1)

    assert pcre2.compile(b'(*MARK:' + b'm' * 200 + b')a').match(b'a', md) == 1
    gc.collect()
    assert md.mark == b'm' * 200

    mark = b'n' * 200
    assert pcre2.compile(b'(*MARK:' + mark + b')a|(*MARK:' + mark + b')b').match(b'c', md) == pcre2.ERROR_NOMATCH
    gc.collect()
    assert md.mark == mark


def test_marks_through_a_search():
    code = pcre2.compile(rb'(*MARK:word)[a-z]+|(*MARK:number)[0-9]+|(*MARK:other)\S')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'abc 123 + de'

    marks = []
    start_offset = 0
    options = 0
    while code.match(subject, md, start_offset, options) >= 0:
        marks.append(md.mark)
        if (nxt := md.next_match()) is None:
            break
        start_offset, options = nxt
    assert marks == [b'word', b'number', b'other', b'word']
    assert len(find_spans(code, subject)) == 4


def test_startchar():
    md = pcre2.MatchData.create(1)
    assert md.startchar == 0

    code = pcre2.compile(b'b')
    assert code.match(b'aab', md) == 1
    assert md.ovector == (2, 3)
    assert md.startchar == 2

    # \K moves the reported start of a match on from where the match began.
    code = pcre2.compile(rb'a\Kb')
    assert code.match(b'xxab', md) == 1
    assert md.ovector == (3, 4)
    assert md.startchar == 2

    assert code.match(b'xx', md) == pcre2.ERROR_NOMATCH
    assert md.startchar == 0
