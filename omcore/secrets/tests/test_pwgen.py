import string
import sys

from .. import pwgen


def test_cli_character_class_selection(monkeypatch, capsys) -> None:
    seen = []

    def generate_password(char_classes, length):
        seen.append((char_classes, length))
        return 'password'

    monkeypatch.setattr(pwgen, 'generate_password', generate_password)

    monkeypatch.setattr(sys, 'argv', ['pwgen'])
    pwgen._main()  # noqa
    assert seen.pop() == (pwgen.ALL_CHAR_CLASSES, pwgen.DEFAULT_LENGTH)
    assert capsys.readouterr().out == 'password\n'

    monkeypatch.setattr(sys, 'argv', ['pwgen', '8', '--lower'])
    pwgen._main()  # noqa
    assert seen.pop() == ((string.ascii_lowercase,), 8)
    assert capsys.readouterr().out == 'password\n'
