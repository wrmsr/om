import subprocess
import sys

from .... import lang
from ...tests.testing import TEST_TIMEOUT_S


def test_child_process_core_imports_do_not_load_runtime_adapter() -> None:
    def script() -> None:
        import sys

        import omcore.daemons.children.configs  # noqa
        import omcore.daemons.children.processes  # noqa

        unexpected = {
            'omcore.daemons.children.services',
            'omcore.daemons.children.supervisors',
            'omcore.daemons.runtime',
            'omcore.daemons.services',
        } & sys.modules.keys()
        if unexpected:
            raise RuntimeError(f'Child process core loaded daemon adapters: {sorted(unexpected)!r}')

    subprocess.run(
        [sys.executable, '-c', lang.get_function_body_source(script)],
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
