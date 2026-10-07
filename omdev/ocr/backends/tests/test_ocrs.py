import subprocess

import pytest

from ...tests.helpers import PngImage
from ...tests.helpers import make_python_executable
from ..ocrs import OcrsOcrBackend


##


def test_stdio(tmp_path):
    executable = make_python_executable(tmp_path, 'ocrs with spaces', """
        import sys
        assert sys.stdin.buffer.read() == b'\\x89PNG\\r\\n\\x1a\\n'
        sys.stdout.buffer.write('Open\\nRésumé\\n'.encode('utf-8'))
    """)
    assert OcrsOcrBackend(executable=executable).ocr(PngImage()) == 'Open\nRésumé\n'  # type: ignore


def test_failure(tmp_path):
    executable = make_python_executable(tmp_path, 'ocrs', """
        import sys
        sys.stdin.buffer.read()
        raise SystemExit(7)
    """)
    with pytest.raises(subprocess.CalledProcessError) as exc:
        OcrsOcrBackend(executable=executable).ocr(PngImage())  # type: ignore
    assert exc.value.returncode == 7
