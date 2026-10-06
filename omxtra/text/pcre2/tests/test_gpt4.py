# @om-precheck-allow-any-unicode
import pytest

from .. import _pcre2 as pcre2
from .patterns import GPT4_PATTERN
from .spans import find_spans


##


def split(text):
    code = pcre2.compile(GPT4_PATTERN.encode(), pcre2.UTF | pcre2.UCP)
    subject = text.encode()
    return [subject[s:e].decode() for s, e in find_spans(code, subject)]


# Expected chunks are those rustbpe 0.1.0 itself produces.
@pytest.mark.parametrize(('text', 'chunks'), [
    (
        "Hello world! I'm fine, you're not.",
        ['Hello', ' world', '!', ' I', "'m", ' fine', ',', ' you', "'re", ' not', '.'],
    ),
    ("THEY'LL'VE 'S 'x", ['THEY', "'LL", "'VE", " '", 'S', " '", 'x']),
    (
        '12345 3.14159 and 1,000,000',
        ['123', '45', ' ', '3', '.', '141', '59', ' and', ' ', '1', ',', '000', ',', '000'],
    ),
    ('line one\r\n\r\n  line two   \n', ['line', ' one', '\r\n\r\n', ' ', ' line', ' two', '   \n']),
    ('x   y\t\tz ', ['x', '  ', ' y', '\t', '\tz', ' ']),
    ('中文123abc４５６７ héllo wörld', ['中文', '123', 'abc', '４５６', '７', ' héllo', ' wörld']),
    ('a\xa0b\u3000c  d', ['a', '\xa0b', '\u3000c', ' ', ' d']),
    ('foo(bar) -> $baz!!!\n', ['foo', '(bar', ')', ' ->', ' $', 'baz', '!!!\n']),
    ('🇺🇸 👍🏽 ok', ['🇺🇸', ' 👍🏽', ' ok']),
    ('', []),
])
def test_gpt4_pattern(text, chunks):
    assert split(text) == chunks


def test_caseless_matching_is_unicode_aware():
    # U+017F LATIN SMALL LETTER LONG S case-folds to 's', so takes the contraction branch here just as it does in Rust.
    assert split("'\u017fx can't") == ["'\u017f", 'x', ' can', "'t"]


def test_mongolian_vowel_separator_is_whitespace():
    # The one known divergence from Rust's regex: PCRE2's \s still includes U+180E, which left White_Space in Unicode
    # 6.3. rustbpe keeps this subject as a single chunk.
    assert split('!\u180e!') == ['!', '\u180e', '!']
