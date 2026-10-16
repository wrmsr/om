import sys

import omxtra.daemons.http.asyncio  # noqa
import omxtra.daemons.http.dispatch  # noqa
import omxtra.daemons.http.pipelines  # noqa
import omxtra.daemons.http.server  # noqa


if __name__ == '__main__':
    unexpected = {
        'omxtra.daemons.daemon',
        'omxtra.daemons.http.services',
        'omxtra.daemons.launching',
        'omxtra.daemons.lazy',
        'omxtra.daemons.runtime',
        'omxtra.daemons.services',
    } & sys.modules.keys()
    if unexpected:
        raise RuntimeError(f'HTTP core loaded daemon adapters: {sorted(unexpected)!r}')
