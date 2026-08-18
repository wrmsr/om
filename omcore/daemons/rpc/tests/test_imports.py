import subprocess
import sys

from .... import lang
from ...tests.testing import TEST_TIMEOUT_S


def _script():
    import sys

    import omcore.daemons.rpc.client  # noqa
    import omcore.daemons.rpc.endpoints  # noqa
    import omcore.daemons.rpc.objects  # noqa
    import omcore.daemons.rpc.protocol  # noqa
    import omcore.daemons.rpc.server  # noqa
    import omcore.daemons.rpc.transports  # noqa

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


def test_rpc_core_imports_do_not_load_daemon_adapters():
    subprocess.run(
        [sys.executable, '-c', lang.get_function_body_source(_script)],
        check=True,
        timeout=TEST_TIMEOUT_S,
    )
