import sys

import omcore.daemons.children.configs  # noqa
import omcore.daemons.children.processes  # noqa


if __name__ == '__main__':
    unexpected = {
        'omcore.daemons.children.services',
        'omcore.daemons.children.supervisors',
        'omcore.daemons.runtime',
        'omcore.daemons.services',
    } & sys.modules.keys()
    if unexpected:
        raise RuntimeError(f'Child process core loaded daemon adapters: {sorted(unexpected)!r}')
