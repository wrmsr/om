"""
A ROUTER answering several DEALERs, by default over a private IPC path.

    ./python -m omxtra.zmq.examples.directed --backend pipelines --clients 3 --requests 5
    ./python -m omxtra.zmq.examples.directed --backend pyzmq --address tcp://127.0.0.1:*
"""
import argparse
import asyncio
import contextlib
import os
import shutil
import tempfile
import typing as ta

from ..api.backends import Backend
from ..api.messages import Message
from ..api.sockets import Router
from ..backends.selection import BACKEND_NAMES
from ..backends.selection import new_backend


##


async def serve(router: Router, n: int) -> None:
    for _ in range(n):
        rm = await router.recv()
        # Routed sends never wait: a peer without room would raise WouldBlockError, for the application to handle.
        await router.send(rm.route, (b'reply', *rm.message[1:]))


async def run(
        backend: Backend,
        address: str,
        *,
        clients: int = 3,
        requests: int = 3,
) -> dict[bytes, list[Message]]:
    router = backend.create_router()
    bound = await router.bind(address)

    dealers = {b'client-%d' % i: backend.create_dealer(routing_id=b'client-%d' % i) for i in range(clients)}
    for d in dealers.values():
        await d.connect(bound.address)

    server = asyncio.create_task(serve(router, clients * requests))

    # Every client sends all its requests before reading any reply: nothing depends on alternation.
    for name, d in dealers.items():
        for j in range(requests):
            await d.send((b'request', name + b'/%d' % j))

    replies = {name: [await d.recv() for _ in range(requests)] for name, d in dealers.items()}
    await server
    return replies


@contextlib.contextmanager
def _private_ipc_address() -> ta.Iterator[str]:
    tmp = tempfile.mkdtemp(prefix='zq')
    try:
        yield f'ipc://{os.path.join(tmp, "router.sock")}'
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def _a_main(args: argparse.Namespace) -> None:
    with contextlib.ExitStack() as es:
        address = args.address or es.enter_context(_private_ipc_address())
        async with new_backend(args.backend) as backend:
            replies = await run(backend, address, clients=args.clients, requests=args.requests)

    for name, msgs in replies.items():
        print(name.decode(), [b' '.join(m).decode() for m in msgs])


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--backend', choices=BACKEND_NAMES, default='pipelines')
    parser.add_argument('--address', help='defaults to a private IPC path')
    parser.add_argument('--clients', type=int, default=3)
    parser.add_argument('--requests', type=int, default=3)
    asyncio.run(_a_main(parser.parse_args()))


if __name__ == '__main__':
    _main()
