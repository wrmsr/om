import os.path
import subprocess
import sys


def test_jq_is_not_imported_until_used():
    with open(os.path.join(os.path.dirname(__file__), 'import_script.py')) as f:
        script = f.read()

    subprocess.run(
        [sys.executable, '-c', script],
        check=True,
        timeout=60,
    )
