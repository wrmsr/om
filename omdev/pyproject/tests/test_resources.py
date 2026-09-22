import os
import subprocess


def test_python_launcher_fallback_is_quiet() -> None:
    launcher = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'python.sh'))
    env = dict(os.environ)
    env['VENV'] = '__om_pyproject_test_missing__'

    proc = subprocess.run(
        [launcher, '-c', 'pass'],
        check=True,
        stdout=subprocess.PIPE,
        env=env,
    )
    assert proc.stdout == b''
