import pytest

from .. import _pcre2 as pcre2


##


def test_substring_number_from_name():
    code = pcre2.compile(rb'(?<year>\d{4})-(?<month>\d\d)|(x)')
    assert code.substring_number_from_name(b'year') == 1
    assert code.substring_number_from_name(b'month') == 2

    with pytest.raises(pcre2.Error) as ei:
        code.substring_number_from_name(b'day')
    assert ei.value.code == pcre2.ERROR_NOSUBSTRING


def test_substring_nametable_scan():
    code = pcre2.compile(rb'(?<year>\d{4})-(?<month>\d\d)|(x)')
    assert code.substring_nametable_scan(b'year') == (1,)
    assert code.substring_nametable_scan(b'month') == (2,)

    with pytest.raises(pcre2.Error) as ei:
        code.substring_nametable_scan(b'day')
    assert ei.value.code == pcre2.ERROR_NOSUBSTRING


def test_duplicate_names():
    code = pcre2.compile(rb'(?<n>a)(?<m>b)|(?<n>c)|(?<n>d)', pcre2.DUPNAMES)
    assert code.substring_nametable_scan(b'n') == (1, 3, 4)
    assert code.substring_nametable_scan(b'm') == (2,)
    assert code.substring_number_from_name(b'm') == 2

    with pytest.raises(pcre2.Error) as ei:
        code.substring_number_from_name(b'n')
    assert ei.value.code == pcre2.ERROR_NOUNIQUESUBSTRING

    # Which of the groups sharing a name took part is for the ovector to say.
    md = pcre2.MatchData.create_from_pattern(code)
    assert code.match(b'd', md) == 5
    ovector = md.ovector
    assert [n for n in code.substring_nametable_scan(b'n') if ovector[2 * n] != pcre2.UNSET] == [4]


def test_no_names():
    code = pcre2.compile(b'(a)')
    for fn in [code.substring_number_from_name, code.substring_nametable_scan]:
        with pytest.raises(pcre2.Error) as ei:
            fn(b'a')
        assert ei.value.code == pcre2.ERROR_NOSUBSTRING


def test_names_are_bytes():
    code = pcre2.compile(rb'(?<year>\d+)')
    for fn in [code.substring_number_from_name, code.substring_nametable_scan]:
        with pytest.raises(TypeError):
            fn('year')  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            fn(bytearray(b'year'))  # type: ignore[arg-type]
        with pytest.raises(ValueError):  # noqa
            fn(b'ye\0ar')
        with pytest.raises(pcre2.Error):
            fn(b'')
