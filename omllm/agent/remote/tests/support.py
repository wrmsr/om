"""
A `RemoteAgentClient` wired over memory streams to a scripted stand-in for the agent, for tests of the client's own
behavior against an agent that answers exactly as told.
"""
import asyncio
import typing as ta

from ....core.rpc.channels import AsyncioStreamRpcChannel
from ....core.rpc.handlers import RpcMethodHandler
from ....core.rpc.peers import RpcPeer
from ....core.rpc.tests.support import memory_rpc_stream_pair
from ..client import RemoteAgentClient
from ..protocol import PROCESS_CLOSE_METHOD
from ..protocol import PROCESS_SIGNAL_METHOD
from ..protocol import PROCESS_SPAWN_METHOD


class ScriptedRemoteAgent:
    """
    Answers `process.spawn` with a fabricated process and records what the client asks of it. A set `spawn_gate` holds
    spawn replies until it is released; `before_spawn_reply` runs, with the new id, just before a spawn is answered;
    `hang_close` never answers `process.close`; `on_close` replaces the close reply entirely.
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

        (client_reader, client_writer), (agent_reader, agent_writer) = memory_rpc_stream_pair()
        self.peer = RpcPeer(
            AsyncioStreamRpcChannel(agent_reader, agent_writer),
            handler=RpcMethodHandler({
                PROCESS_SPAWN_METHOD: self._spawn,
                PROCESS_CLOSE_METHOD: self._close,
                PROCESS_SIGNAL_METHOD: self._signal,
            }),
        )
        self.client = RemoteAgentClient(AsyncioStreamRpcChannel(client_reader, client_writer))

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
        await self.client.start()

    async def aclose(self) -> None:
        await self.peer.aclose()
