# @om-amalg _amalg.py
# ruff: noqa: UP006 UP007 UP045
"""
The entrypoint of a remote blob store's target, launched through pyremote: a `LocalBlobStore` at a root, served over
the bootstrap's channel until the host goes away. The service runs under the sync runtime, so the store's blocking
calls run inline, one at a time.
"""
import typing as ta

from omcore.os.pyremote.core import pyremote_bootstrap_finalize
from omcore.rpc.dispatch import RpcMethodTableHandler
from omcore.rpc.sync import SyncRpcConnections

from ..local.stores import LocalBlobStore
from ..stores import BlobStore
from .server import RemoteBlobStoreService


##


def serve_remote_blob_store(store: BlobStore, read_fd: int, write_fd: int, **kwargs: ta.Any) -> None:
    service = RemoteBlobStoreService(store, **kwargs)
    conn = SyncRpcConnections.of_fds(read_fd, write_fd, handler=RpcMethodTableHandler(service.method_table()))
    conn.add_close_callback(service.close)
    try:
        with conn:
            conn.serve()
    finally:
        service.close()


def remote_blob_store_main(root: str, *, no_fsync: bool = False) -> None:
    runtime = pyremote_bootstrap_finalize()
    serve_remote_blob_store(
        LocalBlobStore(root, config=LocalBlobStore.Config(no_fsync=no_fsync)),
        runtime.input.fileno(),
        runtime.output.fileno(),
    )
