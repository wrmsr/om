import re

import pytest

from ..templates import expand_template
from ..templates import parse_template
from .helpers import found


##


PATTERN = re.compile(r'(?P<a>x)(y)?(z)')
MATCH = found(PATTERN.search('xz'))


def expand(template):
    parsed = parse_template(template, num_groups=PATTERN.groups, group_index=PATTERN.groupindex)
    return expand_template(parsed, MATCH.group, is_str=True)


@pytest.mark.parametrize('template', [
    '',
    'plain',
    r'\1-\3',
    r'\g<a>\g<1>\g<3>\g<0>',
    r'\2|',
    r'\0',
    r'\012',
    r'\101',
    r'\1x',
    r'\08',
    r'a\nb\tc\\d\a\b\f\r\v',
    r'\&\.\ \\1',
])
def test_expands_as_re_does(template):
    assert expand(template) == MATCH.expand(template)


@pytest.mark.parametrize('template', [
    '\\',
    r'\q',
    r'\x41',
    r'\g',
    r'\g<a',
    r'\g<>',
    r'\g<1a>',
    r'\g< 1>',
    r'\g<4>',
    r'\g<nope>',
    r'\4',
    r'\10',
    r'\18',
    r'\99',
    r'\400',
    r'\777',
])
def test_fails_as_re_does(template):
    with pytest.raises((re.PatternError, IndexError)) as theirs:
        MATCH.expand(template)
    with pytest.raises(type(theirs.value)) as ours:
        expand(template)
    assert str(ours.value) == str(theirs.value)


def test_literal():
    assert parse_template('plain', num_groups=0, group_index={}).is_literal
    assert parse_template(r'a\nb', num_groups=0, group_index={}).is_literal
    assert not parse_template(r'\1', num_groups=1, group_index={}).is_literal


def test_bytes():
    parsed = parse_template(r'<\1\xff>'.replace(r'\xff', '\xff'), num_groups=1, group_index={})
    assert expand_template(parsed, lambda number: b'g', is_str=False) == b'<g\xff>'
    assert expand_template(parsed, lambda number: None, is_str=False) == b'<\xff>'
