from .. import _pcre2 as pcre2


##


def error_names():
    return [name for name in dir(pcre2) if name.startswith('ERROR_')]


def test_error_names():
    assert pcre2.ERROR_NOMATCH == -1
    assert pcre2.ERROR_PARTIAL == -2
    assert pcre2.ERROR_MISSING_CLOSING_PARENTHESIS == 114
    assert pcre2.ERROR_BADREPLACEMENT == -35

    # Compile errors are the positive codes, and everything else is negative.
    names = error_names()
    assert len(names) > 190
    assert all(getattr(pcre2, name) != 0 for name in names)


def test_every_error_has_a_message():
    for name in error_names():
        assert pcre2.get_error_message(getattr(pcre2, name)), name


def test_option_names():
    for prefix, count in [
        ('SUBSTITUTE_', 8),
        ('EXTRA_', 17),
        ('INFO_', 27),
        ('CONFIG_', 16),
        ('NEWLINE_', 6),
    ]:
        names = [name for name in dir(pcre2) if name.startswith(prefix)]
        assert len(names) == count, prefix
        assert all(isinstance(getattr(pcre2, name), int) for name in names)

    assert pcre2.OPTIMIZATION_NONE == 0
    assert pcre2.OPTIMIZATION_FULL == 1
    assert pcre2.AUTO_POSSESS_OFF == pcre2.AUTO_POSSESS + 1
    assert pcre2.DOTSTAR_ANCHOR_OFF == pcre2.DOTSTAR_ANCHOR + 1
    assert pcre2.START_OPTIMIZE_OFF == pcre2.START_OPTIMIZE + 1
