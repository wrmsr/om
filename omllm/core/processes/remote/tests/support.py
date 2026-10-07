"""
A `RemoteProcessManager` wired over memory streams to a scripted stand-in for the agent, for tests of the manager's own
behavior against an agent that answers exactly as told - and a TERM-trapping child for teardown tests.
"""
import asyncio
import typing as ta

from ....rpc.channels import AsyncioStreamRpcChannel
from ....rpc.handlers import RpcMethodHandler
from ....rpc.handlers import RpcNotificationRouter
from ....rpc.peers import RpcPeer
from ....rpc.tests.support import memory_rpc_stream_pair
from ..client import RemoteProcessManager
from ..protocol import REMOTE_PROCESS_CLOSE_METHOD
from ..protocol import REMOTE_PROCESS_SIGNAL_METHOD
from ..protocol import REMOTE_PROCESS_SPAWN_METHOD


##


# Darwin's Bash 3.2 can defer a TERM trap around `sleep & wait` until the sleep finishes, or even crash. Either leaves
# the termination marker missing even when killpg succeeds. Use a single Python process to avoid that shell
# fork/wait race, and keep the helper compatible with the Python 3.8 interpreter used for the remote agent.
#
# Arguments: the marker path, written once TERM arrives; then, optionally, a lock path. Given one, it takes an exclusive
# flock on it and forks a descendant into its process group that shares the lock and ignores TERM - one only the group
# sweep's SIGKILL can end. The lock is free again only once both are gone. Everything is in place before 'ready'.
TERMINATION_PROCESS_SRC = """
import fcntl
import os
import signal
import sys
import time


def _fork_stubborn_descendant():
    # Fully set up - TERM ignored, our stdio let go of - before it reports in, so no TERM can reach it first.
    r, w = os.pipe()
    if os.fork():
        os.close(w)
        if os.read(r, 1) != b'+':
            raise RuntimeError('descendant failed to start')
        os.close(r)
        return

    try:
        os.close(r)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        null = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            os.dup2(null, fd)
        os.write(w, b'+')
        os.close(w)
        # Bounded, so one that escapes the sweep does not linger long after the test that let it.
        time.sleep(120)
    finally:
        os._exit(0)


def _main():
    # Block TERM before announcing readiness: sigwait consumes it even if it arrives before the wait starts.
    # Python handlers are deferred, so signal.signal + signal.pause would leave a smaller lost-wakeup window.
    term_signals = {signal.SIGTERM}
    signal.pthread_sigmask(signal.SIG_BLOCK, term_signals)
    if len(sys.argv) > 2:
        lock_fd = os.open(sys.argv[2], os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        _fork_stubborn_descendant()
    os.write(1, b'ready')
    signal.sigwait(term_signals)
    with open(sys.argv[1], 'wb') as f:
        f.write(b'terminated')


if __name__ == '__main__':
    _main()
"""


##


class ScriptedRemoteAgent:
    """
    Answers `process.spawn` with a fabricated process and records what the client asks of it. A set `spawn_gate` holds
    spawn replies until it is released; `before_spawn_reply` runs, with the new id, just before a spawn is answered;
    `hang_close` never answers `process.close`; `on_close` replaces the close reply entirely. The host's end of the
    connection is `client_reader` / `client_writer`, for whichever client a test builds on it.
    """

    def __init__(self) -> None:
        super().__init__()

        self.spawns: list[ta.Any] = []
        self.closes: list[str] = []
        self.signals: list[ta.Any] = []

        self.spawn_started = asyncio.Event()
        self.spawn_gate: asyncio.Event | None = None
        self.before_spawn_reply: ta.Callable[[str], ta.Awaitable[None]] | None = None
        self.close_requested = asyncio.Event()
        self.hang_close = False
        self.on_close: ta.Callable[[ta.Any], ta.Awaitable[ta.Any]] | None = None

        self._next_id = 1

        (self.client_reader, self.client_writer), (agent_reader, agent_writer) = memory_rpc_stream_pair()
        self.peer = RpcPeer(
            AsyncioStreamRpcChannel(agent_reader, agent_writer),
            handler=RpcMethodHandler({
                REMOTE_PROCESS_SPAWN_METHOD: self._spawn,
                REMOTE_PROCESS_CLOSE_METHOD: self._close,
                REMOTE_PROCESS_SIGNAL_METHOD: self._signal,
            }),
        )

    async def _spawn(self, params: ta.Any) -> ta.Any:
        self.spawns.append(params)
        self.spawn_started.set()
        if self.spawn_gate is not None:
            await self.spawn_gate.wait()
        n = self._next_id
        self._next_id += 1
        process_id = f'p{n}'
        if self.before_spawn_reply is not None:
            await self.before_spawn_reply(process_id)
        return {'id': process_id, 'pid': 40000 + n, 'created_at': 0., 'name': params['name']}

    async def _close(self, params: ta.Any) -> ta.Any:
        self.closes.append(params['id'])
        self.close_requested.set()
        if self.on_close is not None:
            return await self.on_close(params)
        if self.hang_close:
            await asyncio.Event().wait()
        return {'returncode': 0, 'state': 'reaped'}

    async def _signal(self, params: ta.Any) -> None:
        self.signals.append(params)

    async def notify(self, method: str, params: ta.Any) -> None:
        await self.peer.notify(method, params)

    async def start(self) -> None:
        await self.peer.start()

    async def aclose(self) -> None:
        await self.peer.aclose()


class ScriptedRemoteProcessClient:
    """The host side: a `RemoteProcessManager` on its own peer to a `ScriptedRemoteAgent`."""

    def __init__(self, agent: ScriptedRemoteAgent) -> None:
        super().__init__()

        self.notifications = RpcNotificationRouter()
        self.peer = RpcPeer(
            AsyncioStreamRpcChannel(agent.client_reader, agent.client_writer),
            handler=self.notifications,
        )
        self.manager = RemoteProcessManager(self.peer, notifications=self.notifications)

    async def start(self) -> None:
        await self.peer.start()
        await self.manager.start()

    async def aclose(self) -> None:
        await self.manager.aclose()
        await self.peer.aclose()


async def scripted_remote_process_client(agent: ScriptedRemoteAgent) -> ScriptedRemoteProcessClient:
    """Starts the agent, and a fresh client over it."""

    client = ScriptedRemoteProcessClient(agent)
    await agent.start()
    await client.start()
    return client
