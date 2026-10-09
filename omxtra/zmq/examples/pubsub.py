"""
A PUB publishing to a SUB subscribed by topic prefix, by default over a private IPC path.

Publication is lossy and a new subscription takes effect only once it reaches the publisher, so the publisher repeats a
probe until the subscriber sees one - an application-level arrangement of this example, not part of the protocol.

    ./python -m omxtra.zmq.examples.pubsub --backend pipelines --topic weather --updates 5
"""
import argparse
import asyncio
import contextlib
import os
import shutil
import tempfile
import typing as ta

from ..api.backends import Backend
from ..api.errors import ZmqTimeoutError
from ..api.messages import Message
from ..backends.selection import BACKEND_NAMES
from ..backends.selection import new_backend


##


PROBE = b'probe'


async def run(
        backend: Backend,
        address: str,
        *,
        topic: bytes = b'weather',
        updates: int = 5,
) -> list[Message]:
    pub = backend.create_publisher()
    bound = await pub.bind(address)
    sub = backend.create_subscriber()
    await sub.connect(bound.address)
    await sub.subscribe(topic)

    async with asyncio.timeout(10.):
        while True:
            await pub.send((topic, PROBE))
            try:
                if (await sub.recv(timeout=.05))[1:] == (PROBE,):
                    break
            except ZmqTimeoutError:
                pass

    await pub.send((b'other-topic', b'never received'))
    for i in range(updates):
        await pub.send((topic, b'update %d' % i))

    received: list[Message] = []
    while len(received) < updates:
        if (msg := await sub.recv(timeout=10.))[1:] != (PROBE,):
            received.append(msg)
    return received


@contextlib.contextmanager
def _private_ipc_address() -> ta.Iterator[str]:
    tmp = tempfile.mkdtemp(prefix='zq')
    try:
        yield f'ipc://{os.path.join(tmp, "pub.sock")}'
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def _a_main(args: argparse.Namespace) -> None:
    with contextlib.ExitStack() as es:
        address = args.address or es.enter_context(_private_ipc_address())
        async with new_backend(args.backend) as backend:
            received = await run(backend, address, topic=args.topic.encode(), updates=args.updates)

    for msg in received:
        print(b' '.join(msg).decode())


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--backend', choices=BACKEND_NAMES, default='pipelines')
    parser.add_argument('--address', help='defaults to a private IPC path')
    parser.add_argument('--topic', default='weather')
    parser.add_argument('--updates', type=int, default=5)
    asyncio.run(_a_main(parser.parse_args()))


if __name__ == '__main__':
    _main()
