import sys

import omxtra.daemons.children.configs  # noqa
import omxtra.daemons.children.processes  # noqa


if __name__ == '__main__':
    unexpected = {
        'omxtra.daemons.children.services',
        'omxtra.daemons.children.supervisors',
        'omxtra.daemons.runtime',
        'omxtra.daemons.services',
    } & sys.modules.keys()
    if unexpected:
        raise RuntimeError(f'Child process core loaded daemon adapters: {sorted(unexpected)!r}')
