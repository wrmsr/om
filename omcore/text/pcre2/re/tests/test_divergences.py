"""
Where the adapter is known not to do what the standard library's `re` does, pinned so that a change to any of it is
noticed. Each is something of PCRE2's which there is no translating away - or, for the last few, more than `re` has.
"""
import re

import pytest

from ... import _pcre2 as pcre2
from ... import re as pre
from .helpers import found


##


def test_case_is_folded_past_ascii_under_the_ascii_flag():
    # Told to match ASCII only, `re` folds the case of ASCII letters alone. PCRE2 has no way of being told that.
    assert re.search('é', 'É', re.IGNORECASE | re.ASCII) is None
    assert pre.search('é', 'É', pre.I | pre.A) is not None

    theirs = found(re.search('k', 'K', re.IGNORECASE | re.ASCII))
    assert found(pre.search('k', 'K', pre.I | pre.A)).span() == theirs.span()


def test_negated_classes_within_a_class_are_pcre2s():
    # `\w` is written out as the letters, numbers, and underscore `re` means by it, and `\s` likewise - but there is no
    # writing `\W` or `\S` out as members of another class, so there they still mean what PCRE2 means: to it a
    # combining mark is a word character, and to `re` it is not.
    subject = 'a\u0301b'
    assert found(re.search(r'\w+', subject)).group() == found(pre.search(r'\w+', subject)).group() == 'a'
    assert found(re.search(r'\W', subject)).group() == found(pre.search(r'\W', subject)).group() == '\u0301'

    assert found(re.search(r'[^\W\d]+', subject)).group() == 'a'
    assert found(pre.search(r'[^\W\d]+', subject)).group() == subject


def test_repeats_of_what_can_match_nothing():
    # The two engines have their own rules for a repeated group which gets round without consuming anything, and can
    # leave different things in it - or, more rarely, find different matches.
    pattern = r'((?:^|b)|(?:c|a)){,2}|[ab]{2}'
    theirs = [m.span() for m in re.finditer(pattern, 'ab')]
    ours = [m.span() for m in pre.finditer(pattern, 'ab')]
    assert theirs == [(0, 0), (0, 2), (2, 2)]
    assert ours == [(0, 0), (0, 1), (1, 2), (2, 2)]


def test_no_locale():
    with pytest.raises(ValueError, match='LOCALE'):
        pre.compile(b'a', pre.L)
    with pytest.raises(re.PatternError, match='LOCALE'):
        pre.compile(b'(?L)a')


def test_error_messages_are_pcre2s():
    with pytest.raises(re.PatternError) as theirs:
        re.compile('a**')
    with pytest.raises(re.PatternError) as ours:
        pre.compile('a**')
    assert theirs.value.msg == 'multiple repeat'
    assert ours.value.msg == 'quantifier does not follow a repeatable item'


def test_lone_surrogates_cannot_be_matched():
    # A str is matched as its UTF-8, which a surrogate on its own has none of.
    assert re.search('a', '\ud800a') is not None
    with pytest.raises(UnicodeEncodeError):
        pre.search('a', '\ud800a')


def test_patterns_which_run_away_are_stopped():
    # PCRE2 gives up on a match which backtracks past its limit, where `re` carries on - here, for some seconds.
    with pytest.raises(pcre2.MatchError) as ei:
        pre.search(r'(a+)+$', 'a' * 24 + 'b')
    assert ei.value.code == pcre2.ERROR_MATCHLIMIT


@pytest.mark.parametrize(('pattern', 'subject', 'span'), [
    (r'\h+', 'a \tb', (1, 3)),
    (r'\p{Lu}', 'aÉb', (1, 2)),
    (r'(?<=a|bc)d', 'bcd', (2, 3)),
    (r'a\Kb', 'ab', (1, 2)),
    (r'(?|(a)|(b))\1', 'bb', (0, 2)),
    (r'\((?:[^()]|(?R))*\)', 'x(a(b)c)y', (1, 8)),
    (r'a(?i)b', 'aB', (0, 2)),
])
def test_more_than_re_accepts(pattern, subject, span):
    # PCRE2's syntax is a superset of `re`'s, and nothing stops a pattern using the rest of it.
    with pytest.raises(re.PatternError):
        re.compile(pattern)
    assert found(pre.search(pattern, subject)).span() == span
