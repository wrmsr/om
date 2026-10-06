import threading

import pytest

from .. import _pcre2 as pcre2


##


# Backtracks exponentially in the length of a run of a's which is not followed by the end of the subject.
EXPLOSIVE_PATTERN = rb'(a+)+$'
EXPLOSIVE_SUBJECT = b'a' * 40 + b'b'


def test_match_limit():
    code = pcre2.compile(EXPLOSIVE_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)
    context = pcre2.MatchContext.create(match_limit=1000)

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(EXPLOSIVE_SUBJECT, md, match_context=context)
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT
    assert ei.value.offset is None
    assert md.next_match() is None

    assert code.match(b'aaa', md, match_context=context) == 2
    assert code.match(b'aab', md, match_context=context) == pcre2.ERROR_NOMATCH


def test_depth_limit():
    code = pcre2.compile(rb'(a)*$')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'a' * 1000

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(subject, md, match_context=pcre2.MatchContext.create(depth_limit=50))
    assert ei.value.code == pcre2.ERROR_DEPTHLIMIT

    assert code.match(subject, md, match_context=pcre2.MatchContext.create(depth_limit=5000)) == 2


def test_heap_limit():
    code = pcre2.compile(rb'(a)*$')
    md = pcre2.MatchData.create_from_pattern(code)
    subject = b'a' * 100_000

    # The limit is in kibibytes.
    with pytest.raises(pcre2.MatchError) as ei:
        code.match(subject, md, match_context=pcre2.MatchContext.create(heap_limit=1))
    assert ei.value.code == pcre2.ERROR_HEAPLIMIT

    assert code.match(subject, md, match_context=pcre2.MatchContext.create(heap_limit=1 << 20)) == 2
    assert code.match(b'a' * 100, md, match_context=pcre2.MatchContext.create(heap_limit=1)) == 2


def test_offset_limit():
    code = pcre2.compile(b'b', pcre2.USE_OFFSET_LIMIT)
    md = pcre2.MatchData.create_from_pattern(code)

    assert code.match(b'aaab', md, match_context=pcre2.MatchContext.create(offset_limit=2)) == pcre2.ERROR_NOMATCH
    assert code.match(b'aaab', md, match_context=pcre2.MatchContext.create(offset_limit=3)) == 1
    assert md.ovector == (3, 4)

    with pytest.raises(pcre2.MatchError) as ei:
        pcre2.compile(b'b').match(b'aaab', md, match_context=pcre2.MatchContext.create(offset_limit=2))
    assert ei.value.code == pcre2.ERROR_BADOFFSETLIMIT


def test_limits_combine():
    code = pcre2.compile(EXPLOSIVE_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)
    context = pcre2.MatchContext.create(match_limit=1000, depth_limit=1000, heap_limit=1024)

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(EXPLOSIVE_SUBJECT, md, match_context=context)
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT


def test_no_limits_given():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'a', md, match_context=pcre2.MatchContext.create()) == 1
    assert code.match(b'a', md, match_context=None) == 1
    assert code.match(b'a', md, 0, 0, pcre2.MatchContext.create()) == 1


def test_arguments():
    with pytest.raises(TypeError):
        pcre2.MatchContext()
    with pytest.raises(TypeError):
        pcre2.MatchContext.create(1000)
    with pytest.raises(TypeError):
        pcre2.MatchContext.create(heap_limit='1')
    with pytest.raises(OverflowError):
        pcre2.MatchContext.create(match_limit=-1)
    with pytest.raises(OverflowError):
        pcre2.MatchContext.create(depth_limit=1 << 32)
    with pytest.raises(OverflowError):
        pcre2.MatchContext.create(offset_limit=-1)

    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create_from_pattern(code)
    for obj in [md, code, 1000, object()]:
        with pytest.raises(TypeError, match='expected MatchContext or None'):
            code.match(b'a', md, match_context=obj)


def test_context_is_shared_between_threads():
    code = pcre2.compile(EXPLOSIVE_PATTERN)
    context = pcre2.MatchContext.create(match_limit=1000)

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results = [None] * num_threads

    def run(i):
        md = pcre2.MatchData.create_from_pattern(code)
        codes = []
        barrier.wait()
        for _ in range(200):
            try:
                code.match(EXPLOSIVE_SUBJECT, md, match_context=context)
            except pcre2.MatchError as e:
                codes.append(e.code)
            codes.append(code.match(b'aaa', md, match_context=context))
        results[i] = codes

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [pcre2.ERROR_MATCHLIMIT, 2] * 200
