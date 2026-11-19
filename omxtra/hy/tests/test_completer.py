import types

import pytest

from omcore import check

from .. import completer
from .. import mangle


##


@pytest.mark.skipif(completer.init_readline() is None, reason="Module 'readline' is not available.")
def test_history_custom_location(tmp_path):
    readline = check.not_none(completer.init_readline())

    expected_entry = '(print "Hy, custom history file!")'

    history_location = tmp_path / '.hy-custom-history'

    with completer.completion(history_file=str(history_location)):
        readline.clear_history()
        readline.add_history(expected_entry)

    actual_entry = history_location.read_text()

    # yes, this is recommended way to check GNU readline vs libedit
    # see https://docs.python.org/3.11/library/readline.html
    if 'libedit' in (readline.__doc__ or ''):
        # libedit saves spaces as octal escapes, so convert them back
        actual_entry = actual_entry.replace('\\040', ' ')

    assert expected_entry in actual_entry


def test_completion():
    completer_ = completer.Completer(
        {
            'hy': None,
            'simple_pythonic_var_name': None,
            mangle('complicated->@#%!name'): types.SimpleNamespace(
                **{mangle('another$^@#$name'): None},
            ),
            'hyx_XaXaXaX': types.SimpleNamespace(hyx_XbXbX=None),
        },
    )
    assert completer_.complete('hy.', 0) is not None
    for test in [
        ('simple_pyth', 'simple-pythonic-var-name'),
        ('compli', 'complicated->@#%!name'),
        ('complicated->@#', 'complicated->@#%!name'),
        ('complicated->@#%!name', 'complicated->@#%!name'),
        ('complicated->@#%!name.ano', 'complicated->@#%!name.another$^@#$name'),
        ('complicated->@#%!name.another$^@', 'complicated->@#%!name.another$^@#$name'),
        ('hyx_XaX', 'hyx_XaXaXaX'),
        ('hyx_XaXaXaX.hyx_Xb', 'hyx_XaXaXaX.hyx_XbXbX'),
    ]:
        assert completer_.complete(test[0], 0) == test[1]
