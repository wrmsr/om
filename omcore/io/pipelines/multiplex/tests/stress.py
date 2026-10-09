# @om-lite
"""Run the randomized integration sessions for a reproducible range of seeds."""
import argparse
import time
import unittest

from .randomized import run_churn
from .randomized import run_session


##


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--churn', action='store_true')
    parser.add_argument('--waves', type=int, default=16)
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    if args.waves < 1:
        parser.error('--waves must be positive')

    started = time.monotonic()
    cases = 0
    tc = unittest.TestCase()
    for seed in range(args.start, args.start + args.count):
        for protocol in (('h2',) if args.churn else ('ssh', 'h2')):
            for tls in (False, True):
                try:
                    if args.churn:
                        run_churn(tc, seed, waves=args.waves, tls=tls)
                    else:
                        run_session(tc, seed, protocol=protocol, tls=tls)
                except BaseException:
                    print(f'FAILED: seed={seed} protocol={protocol} tls={tls}', flush=True)
                    raise
                cases += 1
        if (seed - args.start + 1) % 25 == 0:
            print(f'seed={seed} sessions={cases} elapsed={time.monotonic() - started:.1f}s', flush=True)
    print(f'PASS: {cases} sessions in {time.monotonic() - started:.1f}s', flush=True)


if __name__ == '__main__':
    _main()
