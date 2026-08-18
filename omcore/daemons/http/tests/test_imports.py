import os.path
import subprocess
import sys

from ...tests.testing import TEST_TIMEOUT_S


def test_http_core_imports_do_not_load_daemon_adapters():
    with open(os.path.join(os.path.dirname(__file__), 'import_script.py')) as f:
        script = f.read()

    subprocess.run(
        [sys.executable, '-c', script],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )
