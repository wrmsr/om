import subprocess
import sys

from .testing import TEST_TIMEOUT_S


def test_http_core_imports_do_not_load_daemon_adapters():
    code = """
import sys

import omcore.daemons.http.asyncio
import omcore.daemons.http.dispatch
import omcore.daemons.http.pipelines
import omcore.daemons.http.server

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
"""

    subprocess.run(
        [sys.executable, '-c', code],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )
