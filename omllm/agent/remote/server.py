# ruff: noqa: UP006 UP007 UP045
"""
The remote agent payload's request handler: the method tables of each remotable concern's target-side service, merged
into one table over the one rpc connection. Lite: this is the amalgam's composition root beneath `_main.py`. A new
remotable concern plugs in here, and its host-side client into `client.py`; nothing below either knows the others exist.
"""
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodTableHandler
from omcore.rpc.dispatch import rpc_merge_method_tables

from ...core.processes.remote.server import RemoteProcessService
from ..fs.remote.server import RemoteFsService


##


class RemoteAgentRpcHandler(RpcMethodTableHandler):
    def __init__(self) -> None:
        super().__init__()

        self._fs = RemoteFsService()
        self._processes = RemoteProcessService()

        self.add_methods(rpc_merge_method_tables(
            self._fs.methods(),
            self._processes.methods(),
        ))

    def set_connection(self, connection: RpcConnection) -> None:
        # Only the process service speaks unprompted - its output and exit notifications - so only it needs the
        # connection.
        self._processes.set_connection(connection)

    async def aclose(self) -> None:
        try:
            await self._fs.aclose()
        finally:
            await self._processes.aclose()
