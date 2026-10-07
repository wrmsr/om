# @om-precheck-allow-any-unicode
"""
Runs the adapter and the standard library's `re` side by side - every operation, over a grid of patterns and subjects -
and requires that they agree. What they are known not to agree on is in test_divergences.
"""
import re
import warnings

import pytest

from ... import re as pre


##


PATTERNS = [
    # Literals, repeats, and alternation
    r'a', r'a*', r'a+?', r'a{2}', r'a{2,}', r'a{,2}', r'a{1,2}?', r'x{', r'a|ab|abc', r'(?:x|xy)+z', r'a++b', r'a*+a',
    r'(?>a+)b',

    # Groups, and which of them a match says closed last
    r'(a)(b)?', r'(a)|(b)', r'((a)(b))', r'(a)()', r'(a())', r'(?:(a)|(b))+', r'((a)|(b))+', r'(a(b)?)+',
    r'(a)(?:(b)|(c))*',
    r'(?P<x>a)(?P<y>b)?', r'(?P<a>.)(?P<b>.)?(?P<c>.)?', r'(a)\1', r'(?P<n>a)(?P=n)', r'(a)?(?(1)b|c)', r'(?=(a))a',
    r'(?<=(a))b',

    # Empty matches
    r'', r'()', r'x*', r'(x)*', r'(|a)+', r'(a|)+', r'(a*)*', r'(a*)+', r'\b', r'\B', r'^', r'$', r'(?m)^', r'(?m)$',
    r'(?=a)', r'a{0}',

    # Classes
    r'\w+', r'\W+', r'\s+', r'\S+', r'\d+', r'\D+', r'[a-c]+', r'[^a-c]+', r'[\w\s]+', r'[\d.]+', r'[]a]+', r'[^]a]+',
    r'[a\]]+',
    r'[[]', r'[[:alpha:]]', r'[a-]+', r'[\-a]+', r'[\b]', r'.', r'(?s).', r'.*', r'.*?', r'a[\s\S]c',

    # Anchors and assertions
    r'^a', r'a$', r'\Aa', r'a\Z', r'(?m)^a$', r'\bfoo\b', r'\b\w+\b', r'\B\w', r'(?!a)\w', r'(?<=a)b', r'(?<!a)b',
    r'(?<=\w)\b',

    # Flags within a pattern
    r'(?i)a', r'(?i)[a-z]+', r'(?i:a)b', r'(?s:.)x', r'(?-i:a)', r'(?x) a  b # c', r'(?a)\w+', r'(?u)\w', r'(?#x)a',

    # Escapes
    r'\.', r'\\', r'\/', r'\n', r'\t', r'\x41', r'\101', r'\0', r'\v', r'\f', r'\u00e9',
    r'\N{LATIN SMALL LETTER E WITH ACUTE}',

    # Beyond ASCII
    r'é+', r'[à-ÿ]+', r'(?i)é', r'中+', r'[中文]+',

    # The sort of thing patterns are written for
    r'(\w+)@(\w+)\.com', r'\d{2}-\d{2}', r'(\d+)(?:\.(\d+))?', r'\s*,\s*', r'(?i)(?:the|a)\s+(\w+)', r'^\s+|\s+$',
    r'(?m)^\s*#.*$', r'"[^"]*"', r"'(?:[^'\\]|\\.)*'",

    # Not patterns at all
    r'(a', r'a)', r'*a', r'a**', r'[a', r'\x', r'\8', r'(?P<1>a)', r'(?P<n>a)(?P<n>b)', r'\N{NOPE}', r'\u12', r'(?z)',
]

SUBJECTS = [
    '', 'a', 'b', 'ab', 'abc', 'aab', 'aaa', 'ba', 'A', 'xy', 'xxyxz', 'foo bar', 'foo_bar baz', ' a  b ', 'a\nb\n',
    '\n',
    'héllo wörld', 'É', 'ééé', '中文 text 中', 'a,b , c', 'user@host.com x@y.com', '12-34 5.67',
    "it's 'q\\'d'", '"a" "b"',
    '# c\n  # d\nx', 'The cat, a dog', '١٢٣ 123', 'a\x1cb\x0bc\x85d\u2028e', '😀a😀', 'ab]c-d[', '\\ / .',
    '\x00A\n\t\x0b\x0c',
]


def describe(m):
    if m is None:
        return None
    return (m.span(), m.group(), m.groups(), m.groupdict(), m.lastindex, m.lastgroup, m.regs, m.pos, m.endpos)


def run(module, pattern, subject, flags):
    try:
        compiled = module.compile(pattern, flags)
    except (re.PatternError, ValueError) as e:
        return type(e).__name__

    replacement = '<\\g<0>>' if isinstance(pattern, str) else b'<\\g<0>>'
    return {
        'flags': compiled.flags,
        'groups': compiled.groups,
        'groupindex': dict(compiled.groupindex),
        'search': describe(compiled.search(subject)),
        'match': describe(compiled.match(subject)),
        'fullmatch': describe(compiled.fullmatch(subject)),
        'search from 1': describe(compiled.search(subject, 1)),
        'search to the last': describe(compiled.search(subject, 0, max(len(subject) - 1, 0))),
        'match from 1 to 3': describe(compiled.match(subject, 1, 3)),
        'finditer': [describe(m) for m in compiled.finditer(subject)],
        'findall': compiled.findall(subject),
        'split': compiled.split(subject),
        'split twice': compiled.split(subject, 2),
        'subn': compiled.subn(replacement, subject),
        'sub once': compiled.sub(replacement, subject, 1),
        'sub with a function': compiled.sub(lambda m: m.group()[::-1], subject),
    }


def check_agrees(pattern, subjects, flags):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for subject in subjects:
            assert run(pre, pattern, subject, flags) == run(re, pattern, subject, flags), (pattern, subject, flags)


@pytest.mark.parametrize('pattern', PATTERNS)
def test_str(pattern):
    check_agrees(pattern, SUBJECTS, 0)


@pytest.mark.parametrize('flags', [re.IGNORECASE, re.MULTILINE | re.DOTALL, re.VERBOSE, re.ASCII])
def test_str_with_flags(flags):
    # Case is not folded past ASCII by `re` when it is told to match ASCII only, and is by PCRE2 - see
    # test_divergences - so no patterns are run for that in which there is any to fold.
    for pattern in PATTERNS:
        if flags & re.ASCII and not pattern.isascii():
            continue
        check_agrees(pattern, SUBJECTS[::3], flags)


def test_bytes():
    for pattern in PATTERNS:
        try:
            encoded = pattern.encode('latin-1')
        except UnicodeEncodeError:
            continue
        subjects = [s.encode('latin-1') for s in SUBJECTS if all(ord(c) < 256 for c in s)]
        check_agrees(encoded, subjects, 0)
        check_agrees(encoded, subjects[::4], re.IGNORECASE | re.MULTILINE)
