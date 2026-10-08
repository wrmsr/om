import json
import os.path
import subprocess
import sys

import pytest

from ...tests.helpers import make_python_executable
from ..uv import _run_uv_ocr
from ..uv import _run_worker_process


##


def _echo_worker(png: bytes, *, prefix: str) -> str:
    print('worker diagnostics')
    return prefix + png.decode('utf-8')


def _failing_worker(png: bytes) -> str:
    raise RuntimeError('worker failed')


def _wrong_type_worker(png: bytes):
    return 42


def _make_uv(directory):
    record = os.path.join(str(directory), 'argv.json')
    executable = make_python_executable(directory, 'uv with spaces', f"""
        import json
        import os
        import sys
        with open({record!r}, 'w', encoding='utf-8') as f:
            json.dump(sys.argv[1:], f)
        separator = sys.argv.index('--')
        assert sys.argv[separator + 1] == 'python'
        os.execv(sys.executable, [sys.executable, *sys.argv[separator + 2:]])
    """)
    return executable, record


def test_transport_and_cleanup(tmp_path, capfd):
    executable, record = _make_uv(tmp_path)
    result = _run_uv_ocr(
        _echo_worker,
        'Résumé\r\n'.encode(),
        requirements=('pillow', 'example>=1,<2'),
        kwargs={'prefix': "quote'\n"},
        uv=executable,
        python='cpython@3.12',
        timeout=30.,
    )
    assert result == "quote'\nRésumé\r\n"
    captured = capfd.readouterr()
    assert captured.out == ''
    # assert 'worker diagnostics' in captured.err

    with open(record, encoding='utf-8') as f:
        args = json.load(f)
    assert args[:12] == [
        'run',
        '--no-project',
        '--isolated',
        '--no-config',
        '--python', 'cpython@3.12',
        '--with', 'pillow',
        '--with', 'example>=1,<2',
        '--',
        'python',
    ]
    assert args[12] == '-I'
    assert not os.path.exists(os.path.dirname(args[13]))


@pytest.mark.parametrize('worker', [_failing_worker, _wrong_type_worker])
def test_failure_and_cleanup(tmp_path, worker):
    executable, record = _make_uv(tmp_path)
    with pytest.raises(subprocess.CalledProcessError):
        _run_uv_ocr(worker, b'', requirements=(), kwargs={}, uv=executable, timeout=30.)

    with open(record, encoding='utf-8') as f:
        args = json.load(f)
    script = args[args.index('-I') + 1]
    assert not os.path.exists(os.path.dirname(script))


def test_process_timeout():
    # Blocks waiting for a signal, rather than relying on a sleep to arrange the timeout.
    with pytest.raises(subprocess.TimeoutExpired):
        _run_worker_process(
            [sys.executable, '-I', '-c', 'import signal; signal.pause()'],
            b'',
            timeout=.1,
        )
