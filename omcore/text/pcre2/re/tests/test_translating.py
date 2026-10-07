import re

import pytest

from ..translating import translate_pattern


##


def translate(pattern, **kwargs):
    return translate_pattern(pattern, is_str=True, **kwargs)


@pytest.mark.parametrize(('pattern', 'translated'), [
    (r'abc', r'abc'),
    (r'a\Z', r'a\z'),
    (r'a\\Z', r'a\\Z'),
    (r'[\Z]', r'[\Z]'),
    (r'\v[\v]', r'\x0b[\x0b]'),
    (r'\u00e9[\U0001F600]', r'\x{00e9}[\x{0001F600}]'),
    (r'\N{LATIN SMALL LETTER A}', r'\x{61}'),
    (r'[[:alpha:]]', r'[\[:alpha:]]'),
    (r'[]a[]', r'[]a\[]'),
    (r'[^]a]', r'[^]a]'),
    (r'(?u)a(?iu:b)(?u:c)', r'a(?i:b)(?:c)'),
    (r'(?P<n>a)(?P=n)(?#(x))\(', r'(?P<n>a)(?P=n)(?#(x))\('),
])
def test_translation(pattern, translated):
    assert translate(pattern).pattern == translated


def test_untouched_for_bytes():
    assert translate_pattern(r'\u00e9\N{X}', is_str=False).pattern == r'\u00e9\N{X}'


def test_unicode_classes():
    assert translate(r'\w\s\b').pattern == r'\w\s\b'

    translated = translate(r'\w[\w.]\W', unicode_classes=True).pattern
    assert translated == r'[\p{L}\p{N}_][\p{L}\p{N}_.][^\p{L}\p{N}_]'

    # Within a class a negated class has no spelling of its own, and so stays as it is.
    assert translate(r'[^\W\d]', unicode_classes=True).pattern == r'[^\W\d]'

    # A pattern which turns ASCII matching on for part of itself is left to PCRE2 to follow.
    assert translate(r'(?a:\w)\w', unicode_classes=True).pattern == r'(?a:\w)\w'

    assert translate(r'[\b]', unicode_classes=True).pattern == r'[\b]'
    assert translate(r'\b', unicode_classes=True).pattern.startswith('(?:(?<=[')


def test_verbose_comments_are_left_alone():
    assert translate('a # not (a group \\Z\nb\\Z', verbose=True).pattern == 'a # not (a group \\Z\nb\\z'
    assert translate('a # b\\Z').pattern == 'a # b\\z'


@pytest.mark.parametrize(('pattern', 'ranks'), [
    (r'a', []),
    (r'(a)(b)', [0, 1]),
    (r'((a)(b))', [2, 0, 1]),
    (r'(a(b(c)))', [2, 1, 0]),
    (r'(?:a)(?=b)(?!c)(?<=d)(?<!e)(?>f)(?i:g)(h)', [0]),
    (r'(?P<x>a)(?<y>b)', [0, 1]),
    (r'(a)(?(1)(b)|(c))', [0, 1, 2]),
    (r'(a(*COMMIT)b)(c)', [0, 1]),
    (r'\((a)[(](?#()(b)', [0, 1]),
])
def test_group_close_ranks(pattern, ranks):
    assert list(translate(pattern).group_close_ranks) == ranks


def test_inline_flags():
    assert translate(r'(?im)a').inline_flags == re.IGNORECASE | re.MULTILINE
    assert translate(r'(?s-i)a').inline_flags == re.DOTALL
    assert translate(r'(?i:a)').inline_flags == 0
    assert translate(r'(?ux)a').inline_flags == re.UNICODE | re.VERBOSE


@pytest.mark.parametrize('pattern', [
    r'\u12',
    r'\U0001',
    r'\N{NOT A CHARACTER NAME}',
    r'\N{unterminated',
    r'[abc',
    r'(?L)a',
    r'(?#unterminated',
])
def test_errors(pattern):
    with pytest.raises(re.PatternError):
        translate(pattern)
