import pytest

from .. import _pcre2 as pcre2


##


def parse_name_table(code):
    table = code.pattern_info(pcre2.INFO_NAMETABLE)
    entry_size = code.pattern_info(pcre2.INFO_NAMEENTRYSIZE)
    names = {}
    for i in range(code.pattern_info(pcre2.INFO_NAMECOUNT)):
        entry = table[i * entry_size:(i + 1) * entry_size]
        names[entry[2:entry.index(b'\0', 2)]] = int.from_bytes(entry[:2], 'big')
    return names


def test_version():
    assert pcre2.MAJOR == 10
    assert pcre2.MINOR >= 47
    assert pcre2.config(pcre2.CONFIG_VERSION).startswith(f'{pcre2.MAJOR}.{pcre2.MINOR}')


def test_config():
    assert pcre2.config(pcre2.CONFIG_UNICODE) == 1
    assert pcre2.config(pcre2.CONFIG_UNICODE_VERSION)[0].isdigit()

    with pytest.raises(pcre2.Error) as ei:
        pcre2.config(0xFFFF)
    assert ei.value.code == pcre2.ERROR_BADOPTION
    assert ei.value.offset is None


def test_get_error_message():
    assert pcre2.get_error_message(pcre2.ERROR_NOMATCH) == 'no match'

    with pytest.raises(pcre2.Error) as ei:
        pcre2.get_error_message(99999)
    assert ei.value.code == pcre2.ERROR_BADDATA


def test_compile_error():
    with pytest.raises(pcre2.CompileError) as ei:
        pcre2.compile(b'(abc')

    e = ei.value
    assert isinstance(e, pcre2.Error)
    assert e.code == pcre2.ERROR_MISSING_CLOSING_PARENTHESIS == 114
    assert e.offset == 4
    assert pcre2.get_error_message(e.code) in str(e)


def test_compile_arguments():
    with pytest.raises(TypeError):
        pcre2.compile('abc')  # type: ignore[arg-type]
    with pytest.raises(OverflowError):
        pcre2.compile(b'abc', -1)
    with pytest.raises(OverflowError):
        pcre2.compile(b'abc', 1 << 32)
    with pytest.raises(TypeError, match='expected CompileContext or None'):
        pcre2.compile(b'abc', 0, pcre2.EXTRA_MATCH_WORD)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='expected CompileContext or None'):
        pcre2.compile(b'abc', compile_context=pcre2.MatchContext.create())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pcre2.compile(b'abc', extra_options=pcre2.EXTRA_MATCH_WORD)  # type: ignore[call-arg]

    assert pcre2.compile(b'abc', compile_context=None).pattern_info(pcre2.INFO_SIZE) > 0


def test_types_are_not_instantiable():
    for cls in [pcre2.Code, pcre2.CompileContext, pcre2.MatchContext, pcre2.MatchData]:
        with pytest.raises(TypeError):
            cls()


def test_pattern_info():
    code = pcre2.compile(rb'(?<year>\d{4})-(?<month>\d\d)|(x)', pcre2.UTF | pcre2.CASELESS)
    assert code.pattern_info(pcre2.INFO_CAPTURECOUNT) == 3
    assert code.pattern_info(pcre2.INFO_ARGOPTIONS) == pcre2.UTF | pcre2.CASELESS
    assert code.pattern_info(pcre2.INFO_SIZE) > 0
    assert parse_name_table(code) == {b'year': 1, b'month': 2}

    assert pcre2.compile(b'abc').pattern_info(pcre2.INFO_NAMETABLE) == b''


def test_pattern_info_first_bitmap():
    assert pcre2.compile(b'abc').pattern_info(pcre2.INFO_FIRSTBITMAP) is None

    bitmap = pcre2.compile(b'[ab]x').pattern_info(pcre2.INFO_FIRSTBITMAP)
    assert len(bitmap) == 32
    assert {c for c in range(256) if bitmap[c // 8] & (1 << (c % 8))} == set(b'ab')


def test_pattern_info_errors():
    code = pcre2.compile(b'abc')

    with pytest.raises(pcre2.Error) as ei:
        code.pattern_info(0xFFFF)
    assert ei.value.code == pcre2.ERROR_BADOPTION

    with pytest.raises(pcre2.Error) as ei:
        code.pattern_info(pcre2.INFO_HEAPLIMIT)
    assert ei.value.code == pcre2.ERROR_UNSET

    assert pcre2.compile(b'(*LIMIT_HEAP=1234)abc').pattern_info(pcre2.INFO_HEAPLIMIT) == 1234
