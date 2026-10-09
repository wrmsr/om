import asyncio
import contextlib
import shutil
import tempfile
import typing as ta

from omcore import lang

from ..api.backends import Backend
from ..api.messages import Message
from ..api.sockets import Publisher
from ..api.sockets import Subscriber
from ..backends.selection import new_backend as _new_backend


##


TIMEOUT = 10.

PROBE = b'\xffprobe'


def backend_names() -> list[str]:
    names = ['pipelines']
    if lang.can_import('zmq'):
        names.append('pyzmq')
    return names


def new_backend(name: str) -> Backend:
    return _new_backend(name)


@contextlib.contextmanager
def short_tmp_dir() -> ta.Iterator[str]:
    """A private temporary directory with a short path, as Unix-domain socket paths are short on macOS."""

    path = tempfile.mkdtemp(prefix='zq', dir='/tmp')
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


async def await_subscribed(pub: Publisher, sub: Subscriber, topic: bytes) -> None:
    """
    Publish probes on a subscribed topic until one arrives, proving the subscription - and every subscription change
    made before it on the same connection - reached the publisher. A probe is `(topic + PROBE,)`; recv_skipping_probes
    skips any still in flight. Must not be called while other messages may arrive.
    """

    async with asyncio.timeout(TIMEOUT):
        while True:
            await pub.send((topic + PROBE,))
            try:
                msg = await sub.recv(timeout=.05)
            except TimeoutError:
                continue
            if not (len(msg) == 1 and msg[0].endswith(PROBE)):
                raise RuntimeError(f'unexpected message while awaiting subscription: {msg!r}')
            return


async def recv_skipping_probes(sub: Subscriber, *, timeout: float = TIMEOUT) -> Message:
    while True:
        msg = await sub.recv(timeout=timeout)
        if not (len(msg) == 1 and msg[0].endswith(PROBE)):
            return msg
