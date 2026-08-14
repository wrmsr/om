import subprocess
import sys

from .... import lang
from ...tests.testing import TEST_TIMEOUT_S


def test_http_core_imports_do_not_load_daemon_adapters():
    def script():
        import sys

        import omcore.daemons.http.asyncio  # noqa
        import omcore.daemons.http.dispatch  # noqa
        import omcore.daemons.http.pipelines  # noqa
        import omcore.daemons.http.server  # noqa

        unexpected = {
            'omcore.daemons.daemon',
            'omcore.daemons.http.services',
            'omcore.daemons.launching',
            'omcore.daemons.lazy',
            'omcore.daemons.runtime',
            'omcore.daemons.services',
        } & sys.modules.keys()
        if unexpected:
            raise RuntimeError(f'HTTP core loaded daemon adapters: {sorted(unexpected)!r}')

    subprocess.run(
        [sys.executable, '-c', lang.get_function_body_source(script)],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )
