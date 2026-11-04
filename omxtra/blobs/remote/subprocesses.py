"""
Launching a remote blob store's target: the `_main.py` amalgam, bootstrapped through pyremote into an interpreter on
the other end of a command's stdio, and a `RemoteBlobStore` connected to it.

`argv_prefix` is what reaches the other interpreter - nothing for a local subprocess, `docker exec -i <container>` for
a container. Its arguments are passed verbatim, so a prefix which runs its command through a shell, as ssh does, needs
the bootstrap quoted for that shell. The target needs only a Python 3.8+ interpreter and the root directory.
"""
import asyncio
import contextlib
import importlib.resources
import sys
import typing as ta

from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source
from omcore.rpc.asyncio import AsyncioRpcConnections
from omcore.rpc.connection import RpcConnection

from .client import RemoteBlobStore


##


def get_remote_blob_store_payload_src() -> str:
    return importlib.resources.files(__package__).joinpath('_amalg.py').read_text()


@contextlib.asynccontextmanager
async def remote_blob_store_subprocess(
        root: str,
        *,
        python: str = sys.executable,
        argv_prefix: ta.Sequence[str] = (),
        no_fsync: bool = False,
        payload_src: str | None = None,
        context_name: str = 'omxtra-blobs',
        stderr: ta.Any = None,
        exit_timeout_s: float = 10.,
        **store_kwargs: ta.Any,
) -> ta.AsyncIterator[RemoteBlobStore]:
    """
    Serves a `LocalBlobStore` at `root` on the target for the life of the context. The target exits once the
    connection closes. `stderr` is the target's, as for `asyncio.create_subprocess_exec`.
    """

    proc = await asyncio.create_subprocess_exec(
        *argv_prefix,
        python,
        '-c',
        pyremote_build_bootstrap_source(context_name),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=stderr,
    )
    stdin, stdout = proc.stdin, proc.stdout
    if stdin is None or stdout is None:
        raise RuntimeError('subprocess has no stdio pipes')

    conn: RpcConnection | None = None
    try:
        await PyremoteBootstrapDriver([
            payload_src if payload_src is not None else get_remote_blob_store_payload_src(),
            f'remote_blob_store_main({root!r}, no_fsync={no_fsync!r})',
        ]).async_run(stdout, stdin)

        conn = AsyncioRpcConnections.of_streams(stdout, stdin)
        await conn.start()
        yield await RemoteBlobStore.connect(conn, **store_kwargs)

    finally:
        if conn is not None:
            await conn.close()
        elif stdin.can_write_eof():
            stdin.write_eof()
        else:
            stdin.close()

        try:
            await asyncio.wait_for(proc.wait(), exit_timeout_s)
        except TimeoutError:
            proc.kill()
            await proc.wait()
