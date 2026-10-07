import gc
import sys
import threading
import time

import pytest

from .. import _pcre2 as pcre2


##


# A match with little subject ahead of it is first tried attached to the interpreter under a small match limit, and run
# again detached under its real one only if that runs out. Neither that nor which of the two finished it may show.


# Short enough to be tried attached, and needs a match limit of 1005: some backtracking for every character, so more
# than a probe allows, but nowhere near PCRE2's default limit.
DEEP_PATTERN = rb'(a|b)*$'
DEEP_SUBJECT = b'ab' * 200


def test_match_which_outlasts_the_probe():
    code = pcre2.compile(DEEP_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)

    assert code.match(DEEP_SUBJECT, md) == 2
    assert md.ovector == (0, 400, 399, 400)
    assert md.next_match() == (400, 0)

    assert code.match(DEEP_SUBJECT[:-1] + b'c', md) == 1
    assert md.ovector == (400, 400, pcre2.UNSET, pcre2.UNSET)


@pytest.mark.parametrize(('match_limit', 'matches'), [
    (10, False),
    (255, False),
    (256, False),
    (257, False),
    (1004, False),
    (1005, True),
    (100_000, True),
])
def test_match_limits_either_side_of_the_probe(match_limit, matches):
    code = pcre2.compile(DEEP_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)
    context = pcre2.MatchContext.create(match_limit=match_limit)

    if matches:
        assert code.match(DEEP_SUBJECT, md, match_context=context) == 2
    else:
        with pytest.raises(pcre2.MatchError) as ei:
            code.match(DEEP_SUBJECT, md, match_context=context)
        assert ei.value.code == pcre2.ERROR_MATCHLIMIT

    assert code.match(b'ab', md, match_context=context) == 2


def test_other_limits_apply_under_the_probe():
    code = pcre2.compile(DEEP_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(DEEP_SUBJECT, md, match_context=pcre2.MatchContext.create(depth_limit=50))
    assert ei.value.code == pcre2.ERROR_DEPTHLIMIT

    with pytest.raises(pcre2.MatchError) as ei:
        code.match(DEEP_SUBJECT, md, match_context=pcre2.MatchContext.create(match_limit=100_000, depth_limit=300))
    assert ei.value.code == pcre2.ERROR_DEPTHLIMIT

    assert code.match(DEEP_SUBJECT, md, match_context=pcre2.MatchContext.create(depth_limit=5000)) == 2


def test_pattern_which_limits_itself():
    code = pcre2.compile(b'(*LIMIT_MATCH=100)' + DEEP_PATTERN)
    md = pcre2.MatchData.create_from_pattern(code)
    with pytest.raises(pcre2.MatchError) as ei:
        code.match(DEEP_SUBJECT, md)
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT


##


def measure_slow_match(subject):
    """
    Runs a match which backtracks until PCRE2's default limit stops it, and returns how long it took along with the
    longest that another thread was held up meanwhile: under the GIL from running at all, and free-threaded from
    stopping the world to collect.
    """

    code = pcre2.compile(rb'(a+)+$')
    md = pcre2.MatchData.create_from_pattern(code)
    gil_enabled = sys._is_gil_enabled()  # noqa

    started = threading.Event()
    stop = False
    held_up = 0.

    def other():
        nonlocal held_up
        last = time.perf_counter()
        started.set()
        while not stop:
            if not gil_enabled:
                gc.collect()
            now = time.perf_counter()
            held_up = max(held_up, now - last)
            last = now

    thread = threading.Thread(target=other)
    thread.start()
    started.wait()
    held_up = 0.

    start = time.perf_counter()
    with pytest.raises(pcre2.MatchError) as ei:
        code.match(subject, md)
    elapsed = time.perf_counter() - start

    stop = True
    thread.join()

    assert ei.value.code == pcre2.ERROR_MATCHLIMIT
    return elapsed, held_up


@pytest.mark.parametrize('subject', [
    b'a' * 40 + b'b',
    b'x' * 5000 + b'a' * 40 + b'b',
])
def test_slow_match_does_not_hold_up_other_threads(subject):
    # The short subject is tried attached first, and the long one is detached from the start.
    #
    # Timing-dependent, so given three attempts: a match which holds the interpreter holds another thread up for all
    # of its duration every time, while one which does not only holds it up for as long as the OS happens to.
    for _ in range(3):
        elapsed, held_up = measure_slow_match(subject)
        if held_up < elapsed / 2:
            return
    pytest.fail(f'another thread was held up for {held_up:.3f}s of a {elapsed:.3f}s match')
