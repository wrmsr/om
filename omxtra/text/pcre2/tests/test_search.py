import re

import pytest

from .. import _pcre2 as pcre2
from .spans import find_spans


##


@pytest.mark.parametrize(('pattern', 'subject'), [
    (rb'a*', b'baac'),
    (rb'', b'abc'),
    (rb'x*', b''),
    (rb'\b', b'ab cd'),
    (rb'\d+|', b'12ab345'),
    (rb'(?=a)', b'aaa'),
    (rb'[a-c]+', b'abcabc xyz cab'),
    (rb'a|ab|abc', b'abc ab a'),
    (rb'\s*', b' a  b '),
])
def test_spans_agree_with_re(pattern, subject):
    assert find_spans(pcre2.compile(pattern), subject) == [m.span() for m in re.finditer(pattern, subject)]


def test_empty_matches_advance_by_character():
    subject = 'aé🙂'.encode()
    assert find_spans(pcre2.compile(b'', pcre2.UTF), subject) == [(0, 0), (1, 1), (3, 3), (7, 7)]
    assert find_spans(pcre2.compile(b''), subject) == [(i, i) for i in range(len(subject) + 1)]


def test_empty_matches_do_not_split_crlf():
    assert find_spans(pcre2.compile(b'(*CRLF)'), b'a\r\nb') == [(0, 0), (1, 1), (3, 3), (4, 4)]
    assert find_spans(pcre2.compile(b'(*LF)'), b'a\r\nb') == [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]


def test_caller_options_are_kept():
    code = pcre2.compile(b'a*')
    assert find_spans(code, b'baac', pcre2.NOTEMPTY) == [(1, 3)]


def test_next_match_without_a_match():
    assert pcre2.MatchData.create(1).next_match() is None
