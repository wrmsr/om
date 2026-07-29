import json

import pytest

from ..building import JsonValueBuilder
from ..errors import JsonStreamError
from ..events import BeginArray
from ..events import BeginObject
from ..events import EndArray
from ..events import EndObject
from ..lexing import JsonStreamLexer
from ..lexing import JsonStreamLexError
from ..parsing import JsonStreamParseError
from ..parsing import JsonStreamParser
from ..utils import stream_parse_one_value
from ..utils import stream_parse_values


##


def _parse_all(s, **lex_kwargs):
    vs: list = []
    with JsonStreamLexer(**lex_kwargs) as lex:
        with JsonStreamParser() as parse:
            with JsonValueBuilder() as build:
                for c in [*s, '']:
                    for t in lex(c):
                        for e in parse(t):
                            vs.extend(build(e))
    return vs


##


def test_strict_space_rejects_non_json_whitespace():
    for s in [
        '\x0b1',
        '\x0c1',
        '\x1c1',
        '\x851',
        '\xa01',
        '\u16801',
        '\u20281',
    ]:
        with pytest.raises(JsonStreamLexError):
            list(stream_parse_values(s))

    # Nested case may surface as a parse error from machinery close
    with pytest.raises(JsonStreamError):
        list(stream_parse_values('[1,\u2028 2]'))


def test_strict_space_accepts_json_whitespace():
    assert list(stream_parse_values(' \t\r\n1 \t\r\n')) == [1]


def test_extended_space():
    assert _parse_all('\xa0[\u30001,\ufeff2]\u2029', allow_extended_space=True) == [[1, 2]]

    with pytest.raises(JsonStreamLexError):
        _parse_all('\ufeff1')


##


def test_number_rejects_unicode_digits():
    # U+0664 is ARABIC-INDIC DIGIT FOUR, for which str.isdigit() is true and int()/float() silently accept
    for s in [
        '\u0664',
        '1\u0664',
        '-1\u0664',
        '1.\u0664',
        '1.5\u06642',
        '1e\u0664',
    ]:
        with pytest.raises(JsonStreamLexError):
            list(stream_parse_values(s))


def test_number_formats():
    src = '[0, -1, 10, 1.5, -0.25, 1e4, 1E-2, 2e+3, 0.0]'
    assert list(stream_parse_values(src)) == [json.loads(src)]


##


def test_string_escaped_quotes():
    for n in [1, 2, 3, 8, 100]:
        for tail in ['', '\\\\', '\\\\\\\\']:
            s = '"' + ('a\\"' * n) + tail + '"'
            x = json.loads(s)
            assert stream_parse_one_value([s]) == x
            assert stream_parse_one_value(s) == x

    s = '"' + ('a\\"' * 100_000) + '"'
    assert stream_parse_one_value([s]) == json.loads(s)


def test_string_chunk_splits():
    for s in [
        '"a\\"b\\\\" ',
        '"\\\\\\\\"',
        '"\\u0041\\\\\\"z"',
    ]:
        x = json.loads(s)
        for i in range(1, len(s)):
            assert stream_parse_one_value([s[:i], s[i:]]) == x


##


def test_builder_rejects_mismatched_events():
    b = JsonValueBuilder()
    b(BeginObject)
    with pytest.raises(JsonValueBuilder.StateError):
        b(EndArray)

    b = JsonValueBuilder()
    b(BeginArray)
    with pytest.raises(JsonValueBuilder.StateError):
        b(EndObject)


##


def test_empty_chunks_skipped():
    assert list(stream_parse_values(['', '[1', '', ',2]', ''])) == [[1, 2]]
    assert stream_parse_one_value(['', '{"a"', '', ': 1}']) == {'a': 1}


##


def test_eof_error_position():
    with pytest.raises(JsonStreamLexError) as ei:
        list(stream_parse_values('tru'))
    assert ei.value.pos.ofs == 3

    with pytest.raises(JsonStreamLexError) as ei:
        list(stream_parse_values('"ab'))
    assert ei.value.pos.ofs == 3


##


def test_single_quotes_require_string_literal_parser():
    with pytest.raises(TypeError):
        JsonStreamLexer(JsonStreamLexer.Config(
            allow_single_quotes=True,
        ))

    assert _parse_all(
        "'abc' ",
        allow_single_quotes=True,
        string_literal_parser=lambda s: s[1:-1],
    ) == ['abc']


##


def test_unbalanced_end_array():
    with pytest.raises(JsonStreamParseError) as ei:
        list(stream_parse_values(']'))
    assert ei.value.message == 'Unexpected end array'


def test_negative_infinity():
    assert list(stream_parse_values('-Infinity')) == [float('-inf')]

    with pytest.raises(JsonStreamLexError):
        list(stream_parse_values('-In'))
