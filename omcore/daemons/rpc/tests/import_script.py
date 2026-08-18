import sys

import omcore.daemons.rpc.client  # noqa
import omcore.daemons.rpc.endpoints  # noqa
import omcore.daemons.rpc.objects  # noqa
import omcore.daemons.rpc.protocol  # noqa
import omcore.daemons.rpc.server  # noqa
import omcore.daemons.rpc.transports  # noqa


if __name__ == '__main__':
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
