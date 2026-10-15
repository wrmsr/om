# @om-amalg _amalg.py
# ruff: noqa: UP006 UP007 UP045
"""Entrypoint for the ephemeral remote agent payload launched through pyremote."""
import asyncio
import typing as ta

from omcore.asyncs.asyncio.streams import asyncio_open_stream_reader
from omcore.asyncs.asyncio.streams import asyncio_open_stream_writer
from omcore.os.pyremote.core import pyremote_bootstrap_finalize

from ...core.rpc.channels import AsyncioStreamRpcChannel
from ...core.rpc.peers import RpcPeer
from .server import RemoteAgentRpcHandler


##


async def serve_remote_agent(input: ta.BinaryIO, output: ta.BinaryIO) -> None:  # noqa
    reader = await asyncio_open_stream_reader(input)
    writer = await asyncio_open_stream_writer(output)

    handler = RemoteAgentRpcHandler()
    peer = RpcPeer(AsyncioStreamRpcChannel(reader, writer), handler=handler)
    handler.set_peer(peer)
    try:
        await peer.serve()
    finally:
        await handler.aclose()


def remote_agent_main() -> None:
    runtime = pyremote_bootstrap_finalize()
    asyncio.run(serve_remote_agent(runtime.input, runtime.output))
