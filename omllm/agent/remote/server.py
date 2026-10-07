# ruff: noqa: UP006 UP007 UP045
"""
The remote agent payload's request handler: the method tables of each remotable concern's target-side service, merged
over the one rpc peer. Lite: this is the amalgam's composition root beneath `main.py`. A new remotable concern plugs in
here, and its host-side client into `client.py`; nothing below either knows the others exist.
"""
import typing as ta

from ...core.processes.remote.server import RemoteProcessService
from ...core.rpc.errors import RpcMethodNotFoundError
from ...core.rpc.handlers import RpcHandler
from ...core.rpc.handlers import RpcMethod
from ...core.rpc.peers import RpcPeer
from ..fs.remote.server import RemoteFsService


##


class RemoteAgentRpcHandler(RpcHandler):
    def __init__(self) -> None:
        super().__init__()

        self._fs = RemoteFsService()
        self._processes = RemoteProcessService()

        self._methods: ta.Dict[str, RpcMethod] = {}
        for table in (
                self._fs.methods(),
                self._processes.methods(),
        ):
            for method, fn in table.items():
                if method in self._methods:
                    raise ValueError(f'Duplicate remote agent method: {method!r}')
                self._methods[method] = fn

    def set_peer(self, peer: RpcPeer) -> None:
        # Only the process service speaks unprompted - its output and exit notifications - so only it needs the peer.
        self._processes.set_peer(peer)

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None
        return await fn(params)

    async def aclose(self) -> None:
        try:
            await self._fs.aclose()
        finally:
            await self._processes.aclose()
