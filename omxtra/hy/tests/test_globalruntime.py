"""Run global importer and inspection cases in a dedicated pytest interpreter."""
import subprocess

from omcore.subprocesses.wrap import subprocess_maybe_shell_wrap_exec

from .. import globalruntime
from .helpers import REPO_PYTHON
from .helpers import REPO_ROOT


##


def test_global_runtime_cases():
    assert not globalruntime.is_installed()

    paths = [
        'omxtra/hy/tests/globalruntime_cases.py',
        'omxtra/hy/tests/runtime_global_cases.py',
        'omxtra/hy/tests/readline_cases.py',
        'omxtra/hy/tests/native_tests/hy_inspect.hy',
        'omxtra/hy/tests/native_tests/repl.hy',
        'omxtra/hy/tests/native_tests/hy_misc.hy::test_hyI_mangle_chain',
        'omxtra/hy/tests/native_tests/import.hy::test_no_surprise_shadow',
        'omxtra/hy/tests/native_tests/other.hy::test_pydoc',
    ]
    result = subprocess.run(
        subprocess_maybe_shell_wrap_exec(REPO_PYTHON, '-m', 'pytest', '-q', '--hy-global-tests', *paths),
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not globalruntime.is_installed()
