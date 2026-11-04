"""
A throughput benchmark: an asyncio client against an asyncio server in a separate process, over a socketpair. Each
scenario is run `--repeat` times and its median reported, in calls or notifications per second.

    ./python -m omcore.rpc.tests.bench [--config consolidate_flushes=true] [--payload 1024] [--only seq,conc64]

`--config` takes `RpcConfig` fields as JSON values, for both ends. Numbers vary a good deal from run to run on a shared
machine; pinning both processes (`taskset -c 2,4 ./python -m ...`) and interleaving the configurations being compared
steadies them.
"""
import argparse
import asyncio
import json
import socket
import statistics
import subprocess
import sys
import time
import typing as ta

from ..asyncio import AsyncioRpcConnections
from ..configs import RpcConfig
from ..connection import RpcConnection
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method


##


async def _serve(fd: int, config: RpcConfig) -> None:
    reader, writer = await asyncio.open_connection(sock=socket.socket(fileno=fd))

    received = 0

    def note(p: ta.Any) -> None:
        nonlocal received
        received += 1

    handler = RpcMethodTableHandler(
        {
            'echo': rpc_async_method(lambda p: p),
            'count': rpc_async_method(lambda p: received),
        },
        inline_notifications={'n': note},
    )
    conn = AsyncioRpcConnections.of_streams(reader, writer, config, handler=handler)
    async with conn:
        await conn.serve()


#


async def _requests(conn: RpcConnection, n: int, c: int, payload: ta.Any) -> float:
    """`n` requests from `c` concurrent callers, each awaiting its answer before its next."""

    per = n // c

    async def caller() -> None:
        for _ in range(per):
            await conn.request('echo', payload)

    t = time.perf_counter()
    await asyncio.gather(*[caller() for _ in range(c)])
    return per * c / (time.perf_counter() - t)


async def _notifications(conn: RpcConnection, n: int, c: int, payload: ta.Any) -> float:
    """`n` notifications from `c` concurrent senders, timed until the server has applied them all."""

    base = await conn.request('count')
    per = n // c

    async def sender() -> None:
        for _ in range(per):
            await conn.notify('n', payload)

    t = time.perf_counter()
    await asyncio.gather(*[sender() for _ in range(c)])
    got = await conn.request('count')  # a barrier: everything sent before it has been applied
    dt = time.perf_counter() - t
    if got - base != per * c:
        raise RuntimeError(f'server applied {got - base} notifications, not {per * c}')
    return per * c / dt


SCENARIOS: ta.Mapping[str, ta.Callable[[RpcConnection, ta.Any], ta.Awaitable[float]]] = {
    'seq': lambda conn, p: _requests(conn, 3_000, 1, p),
    'conc8': lambda conn, p: _requests(conn, 6_000, 8, p),
    'conc64': lambda conn, p: _requests(conn, 6_000, 64, p),
    'conc256': lambda conn, p: _requests(conn, 8_192, 256, p),
    'notify1': lambda conn, p: _notifications(conn, 20_000, 1, p),
    'notify64': lambda conn, p: _notifications(conn, 20_000, 64, p),
}


async def _run(
        sock: socket.socket,
        config: RpcConfig,
        *,
        only: ta.Sequence[str],
        repeat: int,
        payload: ta.Any,
) -> None:
    reader, writer = await asyncio.open_connection(sock=sock)
    conn = AsyncioRpcConnections.of_streams(reader, writer, config)
    async with conn:
        for _ in range(200):  # warm up
            await conn.request('echo', 0)

        for name in only:
            rs = [await SCENARIOS[name](conn, payload) for _ in range(repeat)]
            each = ', '.join(f'{r:.0f}' for r in rs)
            print(f'{name:10s} {statistics.median(rs):10.0f} /s   ({each})', flush=True)


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', action='append', default=[], help='an RpcConfig field, as name=json')
    parser.add_argument('--only', default='', help='comma-separated scenarios: ' + ', '.join(SCENARIOS))
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--payload', type=int, default=0, help='a string of this many bytes, else an int')
    parser.add_argument('--serve', type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()

    config = RpcConfig(**{k: json.loads(v) for k, _, v in (c.partition('=') for c in args.config)})

    if args.serve is not None:
        asyncio.run(_serve(args.serve, config))
        return

    a, b = socket.socketpair()
    proc = subprocess.Popen(
        [
            sys.executable, '-m', f'{__package__}.bench',
            '--serve', str(b.fileno()),
            *[x for c in args.config for x in ('--config', c)],
        ],
        pass_fds=[b.fileno()],
    )
    b.close()
    try:
        asyncio.run(_run(
            a,
            config,
            only=args.only.split(',') if args.only else list(SCENARIOS),
            repeat=args.repeat,
            payload='x' * args.payload if args.payload else 1,
        ))
    finally:
        proc.wait(10.)


if __name__ == '__main__':
    _main()
