import subprocess  # noqa: S404
from typing import TYPE_CHECKING

import pytest

from ..__main__ import main
from . import PACKAGE_NAME


if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockFixture


def test_main() -> None:
    result = subprocess.run(
        ['./python', '-m', PACKAGE_NAME, '--help'],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    assert result.stdout.startswith('usage: pipdeptree')
    assert not result.stderr


def test_main_log_resolved(tmp_path: Path, mocker: MockFixture, capsys: pytest.CaptureFixture[str]) -> None:
    mocker.patch('sys.argv', ['', '--python', 'auto'])
    mocker.patch(f'{PACKAGE_NAME}.__main__.detect_active_interpreter', return_value=str(tmp_path))
    mock_subprocess_run = mocker.patch('subprocess.run')
    valid_sys_path = str([str(tmp_path)])
    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=['python', '-c', 'import sys; print(sys.path)'],
        returncode=0,
        stdout=valid_sys_path,
        stderr='',
    )

    main()

    captured = capsys.readouterr()
    assert captured.err.startswith(f'(resolved python: {tmp_path!s}')


def test_main_include_and_exclude_overlap(mocker: MockFixture, capsys: pytest.CaptureFixture[str]) -> None:
    cmd = ['', '--packages', 'a,b,c', '--exclude', 'a']
    mocker.patch(f'{PACKAGE_NAME}.__main__.sys.argv', cmd)

    main()

    captured = capsys.readouterr()
    assert 'Cannot have --packages and --exclude contain the same entries' in captured.err
