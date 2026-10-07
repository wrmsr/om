import re
import sys
import threading

import pytest

from .. import _pcre2 as pcre2


##


def matches(code, subject, md, **kwargs):
    rc = code.dfa_match(subject, md, **kwargs)
    ovector = md.ovector
    return [subject[ovector[2 * i]:ovector[2 * i + 1]] for i in range(max(rc, 0))]


def find_longest_spans(code, subject):
    """A global search with the DFA matcher, which the loop for the backtracking one serves for as it stands."""

    md = pcre2.MatchData.create(8)
    spans = []
    start_offset = 0
    options = 0
    while code.dfa_match(subject, md, start_offset, options) >= 0:
        ovector = md.ovector
        spans.append((ovector[0], ovector[1]))
        if (nxt := md.next_match()) is None:
            break
        start_offset, options = nxt
    return spans


def test_every_match_longest_first():
    code = pcre2.compile(rb'cat(er(pillar)?)?')
    md = pcre2.MatchData.create(8)
    subject = b'the caterpillar catchment'

    assert matches(code, subject, md) == [b'caterpillar', b'cater', b'cat']
    assert md.ovector[:6] == (4, 15, 4, 9, 4, 7)
    assert md.startchar == 4
    assert md.mark is None

    assert matches(code, subject, md, start_offset=5) == [b'cat']
    assert md.ovector[:2] == (16, 19)


def test_longest_not_first_alternative():
    # The backtracking matcher takes the first alternative which leads to a match, and this one all of them.
    code = pcre2.compile(rb'a|ab|abc')
    md = pcre2.MatchData.create(8)
    assert code.match(b'abcd', md) == 1
    assert md.ovector[:2] == (0, 1)
    assert matches(code, b'abcd', md) == [b'abc', b'ab', b'a']


def test_possessive_repeats_leave_one_match():
    # A repeat which nothing after it could give ground to is compiled as possessive, and so has just the one match.
    md = pcre2.MatchData.create(8)
    assert matches(pcre2.compile(rb'\w+'), b'abc', md) == [b'abc']
    assert matches(pcre2.compile(rb'\w+', pcre2.NO_AUTO_POSSESS), b'abc', md) == [b'abc', b'ab', b'a']


def test_shortest():
    code = pcre2.compile(rb'cat(er(pillar)?)?')
    md = pcre2.MatchData.create(8)
    assert matches(code, b'the caterpillar', md, options=pcre2.DFA_SHORTEST) == [b'cat']


def test_no_match():
    code = pcre2.compile(b'cat')
    md = pcre2.MatchData.create(8)
    assert code.dfa_match(b'dog', md) == pcre2.ERROR_NOMATCH
    assert md.next_match() is None


def test_more_matches_than_the_ovector_holds():
    code = pcre2.compile(rb'cat(er(pillar)?)?')
    md = pcre2.MatchData.create(2)
    assert code.dfa_match(b'the caterpillar', md) == 0
    assert md.ovector == (4, 15, 4, 9)


def test_anchoring():
    code = pcre2.compile(b'ab')
    md = pcre2.MatchData.create(2)
    assert code.dfa_match(b'xab', md) == 1
    assert code.dfa_match(b'xab', md, options=pcre2.ANCHORED) == pcre2.ERROR_NOMATCH
    assert code.dfa_match(b'abx', md, options=pcre2.ENDANCHORED) == pcre2.ERROR_NOMATCH
    assert code.dfa_match(b'xab', md, 1, pcre2.ANCHORED | pcre2.ENDANCHORED) == 1


@pytest.mark.parametrize(('pattern', 'subject'), [
    (rb'a+', b'baac a'),
    (rb'[a-c]+', b'abcabc xyz cab'),
    (rb'\d+', b'12ab345'),
    (rb'x*', b'axxb'),
    (rb'', b'abc'),
    (rb'\b', b'ab cd'),
])
def test_global_search_agrees_with_re_where_longest_is_what_re_finds(pattern, subject):
    assert find_longest_spans(pcre2.compile(pattern), subject) == [m.span() for m in re.finditer(pattern, subject)]


def test_does_not_backtrack():
    # The pattern test_limits uses to exhaust a match limit, on a subject which takes the backtracking matcher about a
    # million times as long as this one.
    code = pcre2.compile(rb'(a+)+$')
    md = pcre2.MatchData.create(2)
    assert code.dfa_match(b'a' * 40 + b'b', md) == pcre2.ERROR_NOMATCH
    assert code.dfa_match(b'a' * 40, md) == 1


def test_unsupported_items():
    md = pcre2.MatchData.create(2)
    for pattern in [rb'(a)\1', rb'a(*COMMIT)b', rb'a\Kb']:
        with pytest.raises(pcre2.MatchError) as ei:
            pcre2.compile(pattern).dfa_match(b'aab', md)
        assert ei.value.code == pcre2.ERROR_DFA_UITEM
        assert md.next_match() is None

    with pytest.raises(pcre2.MatchError) as ei:
        pcre2.compile(b'a', pcre2.UTF | pcre2.MATCH_INVALID_UTF).dfa_match(b'a', md)
    assert ei.value.code == pcre2.ERROR_DFA_UINVALID_UTF


def test_workspace():
    code = pcre2.compile(rb'(a+)+$')
    md = pcre2.MatchData.create(2)
    subject = b'a' * 100 + b'b'

    # The workspace is what bounds this matcher's work: one too small for the paths it has to follow ends the match
    # there and then, and one large enough lets it go on to its answer.
    for wscount in [0, 19, 20, 1000]:
        with pytest.raises(pcre2.MatchError) as ei:
            code.dfa_match(subject, md, wscount=wscount)
        assert ei.value.code == pcre2.ERROR_DFA_WSSIZE
    assert code.dfa_match(subject, md, wscount=4000) == pcre2.ERROR_NOMATCH

    # It is the block's to keep, and to resize as asked.
    before = sys.getsizeof(pcre2.MatchData.create(2))
    assert sys.getsizeof(md) - before >= 4000 * 4
    assert pcre2.compile(b'a').dfa_match(b'a', md, wscount=100) == 1
    assert sys.getsizeof(md) - before < 4000 * 4


def test_partial_and_restart():
    code = pcre2.compile(rb'\d+-\d+')
    md = pcre2.MatchData.create(4)
    partial = pcre2.PARTIAL_HARD

    assert code.dfa_match(b'x 123-', md, options=partial) == pcre2.ERROR_PARTIAL
    assert md.ovector[:2] == (2, 6)
    assert md.next_match() is None

    # The rest of the match is in the next piece of the subject, where offsets start over.
    assert code.dfa_match(b'45', md, options=partial | pcre2.DFA_RESTART) == pcre2.ERROR_PARTIAL
    assert code.dfa_match(b'6 y', md, options=partial | pcre2.DFA_RESTART) == 1
    assert md.ovector[:2] == (0, 1)


def test_restart_needs_the_partial_match_it_carries_on_from():
    code = pcre2.compile(rb'\d+-\d+')
    other = pcre2.compile(rb'\d+')
    md = pcre2.MatchData.create(4)
    partial = pcre2.PARTIAL_HARD
    restart = partial | pcre2.DFA_RESTART

    def check_refused(c):
        with pytest.raises(pcre2.MatchError) as ei:
            c.dfa_match(b'45', md, options=restart)
        assert ei.value.code == pcre2.ERROR_DFA_BADRESTART

    # A block which has never been matched into.
    check_refused(code)

    # One whose last match did not end partially.
    assert code.dfa_match(b'1-2 ', md, options=partial) == 1
    check_refused(code)

    # One whose partial match was another pattern's: what is in the workspace would mean nothing to this one.
    assert code.dfa_match(b'x 123-', md, options=partial) == pcre2.ERROR_PARTIAL
    check_refused(other)

    # One which has been used for something else since - or for an attempt to restart which was refused.
    check_refused(code)
    assert code.dfa_match(b'x 123-', md, options=partial) == pcre2.ERROR_PARTIAL
    assert code.match(b'1-2', md) == 1
    check_refused(code)
    assert code.dfa_match(b'x 123-', md, options=partial) == pcre2.ERROR_PARTIAL
    assert code.substitute(b'1-2', b'x', match_data=md) == (b'x', 1)
    check_refused(code)

    assert code.dfa_match(b'x 123-', md, options=partial) == pcre2.ERROR_PARTIAL
    assert code.dfa_match(b'45 ', md, options=restart) == 1


def test_utf():
    code = pcre2.compile(rb'\w+', pcre2.UTF | pcre2.UCP)
    md = pcre2.MatchData.create(8)
    subject = 'h\u00e9llo w\u00f6rld'.encode()

    assert matches(code, subject, md)[0] == 'h\u00e9llo'.encode()
    assert find_longest_spans(code, subject) == [(0, 6), (7, 13)]

    with pytest.raises(BufferError, match='could change during the match'):
        code.dfa_match(bytearray(subject), md)
    assert code.dfa_match(bytearray(subject), md, options=pcre2.NO_UTF_CHECK) == 1

    with pytest.raises(pcre2.MatchError) as ei:
        code.dfa_match(b'ab\xff', md)
    assert pcre2.ERROR_UTF8_ERR21 <= ei.value.code <= pcre2.ERROR_UTF8_ERR1
    assert ei.value.offset == 2


def test_limits():
    md = pcre2.MatchData.create(2)

    # For this matcher a match limit bounds how many places it starts a match from.
    code = pcre2.compile(rb'\d', pcre2.NO_START_OPTIMIZE)
    with pytest.raises(pcre2.MatchError) as ei:
        code.dfa_match(b'x' * 100, md, match_context=pcre2.MatchContext.create(match_limit=10))
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT
    assert code.dfa_match(b'x' * 100, md, match_context=pcre2.MatchContext.create(match_limit=1000)) == (
        pcre2.ERROR_NOMATCH
    )


def test_errors_and_arguments():
    code = pcre2.compile(b'a')
    md = pcre2.MatchData.create(2)

    with pytest.raises(pcre2.MatchError) as ei:
        code.dfa_match(b'a', md, options=pcre2.NO_JIT)
    assert ei.value.code == pcre2.ERROR_BADOPTION
    with pytest.raises(pcre2.MatchError) as ei:
        code.dfa_match(b'a', md, 2)
    assert ei.value.code == pcre2.ERROR_BADOFFSET

    with pytest.raises(ValueError):  # noqa
        code.dfa_match(b'a', md, -1)
    with pytest.raises(ValueError):  # noqa
        code.dfa_match(b'a', md, wscount=-1)
    with pytest.raises(OverflowError):
        code.dfa_match(b'a', md, wscount=1 << 40)
    with pytest.raises(TypeError):
        code.dfa_match('a', md)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        code.dfa_match(b'a')  # type: ignore[call-arg]
    with pytest.raises(TypeError, match='expected MatchContext or None'):
        code.dfa_match(b'a', md, match_context=md)  # type: ignore[arg-type]

    assert code.dfa_match(b'a', md, 0, 0, None, 100) == 1


def test_code_is_shared_between_threads():
    code = pcre2.compile(rb'\p{L}+|\p{N}+', pcre2.UTF | pcre2.UCP)
    subject = 'short h\u00e9llo 123 '.encode() * 50
    expected = find_longest_spans(code, subject)
    assert len(expected) == 150

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results: list = [None] * num_threads

    def run(i):
        barrier.wait()
        results[i] = [find_longest_spans(code, subject) for _ in range(5)]

    threads = [threading.Thread(target=run, args=(i,)) for i in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        assert result == [expected] * 5
