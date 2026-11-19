import pytest

from .. import completer


##


def test_history_custom_location(tmp_path):
    readline = completer.init_readline()
    if readline is None:
        pytest.skip("Module 'readline' is not available.")

    expected_entry = '(print "Hy, custom history file!")'
    history_location = tmp_path / '.hy-custom-history'

    with completer.completion(history_file=str(history_location)):
        readline.clear_history()
        readline.add_history(expected_entry)

    actual_entry = history_location.read_text()

    # GNU readline and libedit save spaces differently.
    if 'libedit' in (readline.__doc__ or ''):
        actual_entry = actual_entry.replace('\\040', ' ')

    assert expected_entry in actual_entry
