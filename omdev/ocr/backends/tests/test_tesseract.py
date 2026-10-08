# @om-precheck-allow-any-unicode
import json
import os
import os.path
import subprocess

import pytest

from ...tests.helpers import PngImage
from ...tests.helpers import make_python_executable
from ..tesseract import TesseractOcrBackend


##


def _make_tesseract(directory, *, output='Open\nSave\n', returncode=0):
    record = os.path.join(str(directory), 'argv.json')
    image = os.path.join(str(directory), 'input.png')
    executable = make_python_executable(directory, 'tesseract with spaces', f"""
        import json
        import sys
        with open({record!r}, 'w', encoding='utf-8') as f:
            json.dump(sys.argv[1:], f)
        with open({image!r}, 'wb') as f:
            f.write(sys.stdin.buffer.read())
        sys.stdout.buffer.write({output.encode('utf-8')!r})
        print('tesseract diagnostics', file=sys.stderr)
        sys.exit({returncode!r})
    """)
    return executable, record, image


@pytest.mark.parametrize('output', ['Open\nSave\n', '', '  résumé\t文件\r\n\n'])
def test_defaults(tmp_path, capfd, output):
    executable, record, image_file = _make_tesseract(tmp_path, output=output)
    backend = TesseractOcrBackend(executable=executable, timeout=30.)
    image = PngImage(b'\x89PNG\r\n\x1a\n\x00\xff')
    assert backend.ocr(image) == output  # type: ignore

    with open(record, encoding='utf-8') as f:
        assert json.load(f) == ['stdin', 'stdout', '--oem', '1', '--psm', '6', 'txt']
    with open(image_file, 'rb') as f:
        assert f.read() == image.data

    captured = capfd.readouterr()
    assert captured.out == ''
    # assert 'tesseract diagnostics' in captured.err


def test_options(tmp_path):
    executable, record, _ = _make_tesseract(tmp_path)
    backend = TesseractOcrBackend(
        executable=executable,
        config='--psm 7 --tessdata-dir "/models/tessdata best" -c "tessedit_char_whitelist=a b;$HOME"',
        language='eng+fra',
        timeout=30.,
    )
    assert backend.ocr(PngImage()) == 'Open\nSave\n'  # type: ignore
    with open(record, encoding='utf-8') as f:
        assert json.load(f) == [
            'stdin',
            'stdout',
            '-l',
            'eng+fra',
            '--psm',
            '7',
            '--tessdata-dir',
            '/models/tessdata best',
            '-c',
            'tessedit_char_whitelist=a b;$HOME',
            'txt',
        ]


def test_empty_config(tmp_path):
    executable, record, _ = _make_tesseract(tmp_path)
    TesseractOcrBackend(executable=executable, config='').ocr(PngImage())  # type: ignore
    with open(record, encoding='utf-8') as f:
        assert json.load(f) == ['stdin', 'stdout', 'txt']


def test_availability(tmp_path):
    missing = os.path.join(str(tmp_path), 'missing executable')
    assert not TesseractOcrBackend(executable=missing).is_available()
    executable, _, _ = _make_tesseract(tmp_path)
    assert TesseractOcrBackend(executable=executable).is_available()
    os.chmod(executable, 0o644)
    assert not TesseractOcrBackend(executable=executable).is_available()


@pytest.mark.parametrize('backend_type', [TesseractOcrBackend])
@pytest.mark.parametrize('timeout', [0., -1.])
def test_timeout_validation(backend_type, timeout):
    with pytest.raises(ValueError):  # noqa
        backend_type(timeout=timeout)


def test_missing_executable(tmp_path):
    backend = TesseractOcrBackend(executable=os.path.join(str(tmp_path), 'missing executable'))
    with pytest.raises(FileNotFoundError):
        backend.ocr(PngImage())  # type: ignore


def test_nonzero_exit(tmp_path):
    executable, _, _ = _make_tesseract(tmp_path, output='partial\n', returncode=7)
    backend = TesseractOcrBackend(executable=executable, timeout=30.)
    with pytest.raises(subprocess.CalledProcessError) as exc:
        backend.ocr(PngImage())  # type: ignore
    assert exc.value.returncode == 7
    assert exc.value.stdout == b'partial\n'
    assert 'tesseract diagnostics' in exc.value.stderr.decode()


def test_timeout(tmp_path):
    executable = make_python_executable(tmp_path, 'blocked tesseract', """
        import signal
        signal.pause()
    """)
    backend = TesseractOcrBackend(executable=executable, timeout=.1)
    with pytest.raises(subprocess.TimeoutExpired):
        backend.ocr(PngImage())  # type: ignore


def test_invalid_config(tmp_path):
    backend = TesseractOcrBackend(executable=os.path.join(str(tmp_path), 'missing executable'), config='--psm "')
    with pytest.raises(ValueError):  # noqa
        backend.ocr(PngImage())  # type: ignore
