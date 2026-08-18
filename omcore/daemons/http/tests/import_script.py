import sys

import omcore.daemons.http.asyncio  # noqa
import omcore.daemons.http.dispatch  # noqa
import omcore.daemons.http.pipelines  # noqa
import omcore.daemons.http.server  # noqa


if __name__ == '__main__':
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
