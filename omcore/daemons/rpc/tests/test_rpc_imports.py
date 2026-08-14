import subprocess
import sys

from ...tests.testing import TEST_TIMEOUT_S


def test_rpc_core_imports_do_not_load_daemon_adapters():
    code = """
import sys

import omcore.daemons.rpc.client
import omcore.daemons.rpc.objects
import omcore.daemons.rpc.protocol
import omcore.daemons.rpc.server

unexpected = {
    'omcore.daemons.lazy',
    'omcore.daemons.rpc.lazy',
    'omcore.daemons.rpc.services',
    'omcore.daemons.rpc.waiting',
    'omcore.daemons.runtime',
    'omcore.daemons.services',
} & sys.modules.keys()
if unexpected:
    raise RuntimeError(f'RPC core loaded daemon adapters: {sorted(unexpected)!r}')
"""

    subprocess.run(
        [sys.executable, '-c', code],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )
