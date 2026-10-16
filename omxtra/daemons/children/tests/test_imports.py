import os.path
import subprocess
import sys

from ...tests.testing import TEST_TIMEOUT_S


def test_child_process_core_imports_do_not_load_runtime_adapter() -> None:
    with open(os.path.join(os.path.dirname(__file__), 'import_script.py')) as f:
        script = f.read()

    subprocess.run(
        [sys.executable, '-c', script],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )


def test_child_process_api_is_exported_from_daemons_package() -> None:
    from ... import ChildProcessConfig
    from ... import ChildProcessService
    from ... import ChildProcessSupervisor

    assert ChildProcessConfig.__name__ == 'ChildProcessConfig'
    assert ChildProcessService.__name__ == 'ChildProcessService'
    assert ChildProcessSupervisor.__name__ == 'ChildProcessSupervisor'
