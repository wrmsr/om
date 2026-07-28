import json

import pytest

from ....json5.stream import stream_parse_one_value as json5_stream_parse_one_value
from ..lexing import JsonStreamLexer
from ..lexing import JsonStreamLexError
from ..utils import stream_parse_one_value
from ..utils import stream_parse_values


##


def _lex_all(chunks, **kwargs):
    with JsonStreamLexer(**kwargs) as lex:
        ts: list = []
        for c in chunks:
            ts.extend(lex(c))
        return ts


##


def test_chunked_parsing_equivalence():
    s = (
        '\n{"a": [1, -2.5e3, true, false, null, '
        r'"x\n\"y\\"'
        '], "big": 12345678901234567890, "f": 1e-3, '
        '"inf": [-Infinity, Infinity, 0, -0.0, 7], "e": {}, "g": [[]]}\t'
    )
    x = json.loads(s)

    assert stream_parse_one_value([s]) == x
    assert stream_parse_one_value(s) == x
    assert stream_parse_one_value(iter(s)) == x

    for i in range(1, len(s)):
        assert stream_parse_one_value([s[:i], s[i:]]) == x

    for n in [2, 3, 7]:
        assert stream_parse_one_value([s[i:i + n] for i in range(0, len(s), n)]) == x


def test_chunked_lexing_matches_per_char():
    s = (
        ' {"a b": [1, true, null, '
        r'"c\td"'
        ', -Infinity, 2.5]}\n[3, "x"]\t'
    )

    for kwargs in [
        {},
        {'include_space': True},
        {'include_raw': True},
        {'include_space': True, 'include_raw': True},
    ]:
        base = _lex_all([*s, ''], **kwargs)
        assert _lex_all([s, ''], **kwargs) == base
        for i in range(1, len(s)):
            assert _lex_all([s[:i], s[i:], ''], **kwargs) == base


def test_chunked_extended_space():
    s = '\xa0[\u30001,\ufeff2]\u2029'
    base = _lex_all([*s, ''], allow_extended_space=True)
    for i in range(1, len(s)):
        assert _lex_all([s[:i], s[i:], ''], allow_extended_space=True) == base


def test_chunked_json5():
    s = "// hi\n{a: 0x10, 'b': [.5, +2, Infinity,], /* c */ c: 'd', d: 0,}\n"
    x = {'a': 16, 'b': [0.5, 2, float('inf')], 'c': 'd', 'd': 0}

    assert json5_stream_parse_one_value([s]) == x
    for i in range(1, len(s)):
        assert json5_stream_parse_one_value([s[:i], s[i:]]) == x


def test_str_input():
    assert list(stream_parse_values('1 2 true')) == [1, 2, True]
    assert stream_parse_one_value('{"a": 1} trailing garbage') == {'a': 1}


def test_values_before_error_are_delivered():
    # Values completed before a later lex error must still reach the consumer, even when batched within one chunk.
    for src in [
        '1 2 "bad\n"',
        ['1 2 "bad\n"'],
    ]:
        vs: list = []
        with pytest.raises(JsonStreamLexError):
            vs.extend(stream_parse_values(src))
        assert vs == [1, 2]
