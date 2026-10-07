import os.path
import subprocess
import sys

from ..asyncio import start_manhole


##


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..'] * 4)))


def test_client_subprocess(tmp_path):
    path = str(tmp_path / 'client.sock')
    with start_manhole(path, seed={'answer': 42}, banner='hi'):
        proc = subprocess.run(
            [sys.executable, '-m', 'omdev.repl.manhole', path],
            input=b'answer + 1\nprint("from client")\n',
            capture_output=True,
            cwd=_REPO_ROOT,
            timeout=60.,
            check=False,
        )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == b'hi\n>>> 43\n>>> from client\n>>> '
