import sys

import omxtra.daemons.rpc.client  # noqa
import omxtra.daemons.rpc.objects  # noqa
import omxtra.daemons.rpc.protocol  # noqa
import omxtra.daemons.rpc.server  # noqa


if __name__ == '__main__':
    unexpected = {
        'omxtra.daemons.lazy',
        'omxtra.daemons.rpc.lazy',
        'omxtra.daemons.rpc.services',
        'omxtra.daemons.rpc.waiting',
        'omxtra.daemons.runtime',
        'omxtra.daemons.services',
    } & sys.modules.keys()
    if unexpected:
        raise RuntimeError(f'RPC core loaded daemon adapters: {sorted(unexpected)!r}')
