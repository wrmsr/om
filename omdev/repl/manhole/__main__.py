"""
`python -m omdev.repl.manhole ADDRESS` connects to a manhole; `--serve ADDRESS` runs one in this otherwise idle process
until interrupted, for trying the thing out. ADDRESS is a unix socket path, or `host:port` / `:port` for tcp.
"""
import argparse
import sys
import time

from omcore import lang

from .asyncio import start_manhole
from .base import parse_address
from .client import run_client


##


def _main(argv: lang.SequenceNotStr[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog='python -m omdev.repl.manhole')
    parser.add_argument('address', help='unix socket path, or host:port / :port')
    parser.add_argument('--serve', action='store_true', help='serve a manhole here instead of connecting to one')
    args = parser.parse_args(argv)

    address = parse_address(args.address)

    if args.serve:
        with start_manhole(address) as manhole:
            print(f'serving manhole on {manhole.address}; ctrl+c stops', file=sys.stderr)
            try:
                while True:
                    time.sleep(3600.)
            except KeyboardInterrupt:
                pass
        return

    try:
        run_client(address)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    _main()
