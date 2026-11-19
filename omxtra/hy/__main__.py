import sys

from .cli import hy_main


##


# Running hy as a module (e.g. `python -m <package>`) is equivalent to running the main `hy` command.
if __name__ == '__main__':
    sys.exit(hy_main())
