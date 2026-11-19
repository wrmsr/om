# ruff: noqa: UP006 UP007 UP045
import asyncio
import logging
import socket
import typing as ta
import unittest

from omcore.lite.marshal import ObjMarshalerManager
from omcore.rpc.asyncio import AsyncioRpcConnections
from omcore.rpc.connection import RpcConnection
from omcore.rpc.dispatch import RpcMethodTableHandler

from ...bootstrap import MainBootstrap
from ...bootstrap_ import main_bootstrap
from ...commands.base import CommandExecutor
from ...commands.local import LocalCommandExecutor
from ...commands.ping import PingCommand
from ...commands.subprocess import SubprocessCommand
from ..connection import InProcessRemoteExecutionConnector
from ..execution import RemoteCommandError
from ..execution import _RemoteLogHandler
from ..protocol import REMOTE_EXECUTION_LOG_METHOD


async def _connection_pair(
        a_handler: ta.Optional[RpcMethodTableHandler] = None,
        b_handler: ta.Optional[RpcMethodTableHandler] = None,
) -> ta.Tuple[RpcConnection, RpcConnection]:
    s1, s2 = socket.socketpair()
    r1, w1 = await asyncio.open_connection(sock=s1)
    r2, w2 = await asyncio.open_connection(sock=s2)
    return (
        AsyncioRpcConnections.of_streams(r1, w1, handler=a_handler),
        AsyncioRpcConnections.of_streams(r2, w2, handler=b_handler),
    )


class TestRemoteExecution(unittest.IsolatedAsyncioTestCase):
    async def test_in_process_fake_remote(self):
        injector = main_bootstrap(MainBootstrap())
        connector = InProcessRemoteExecutionConnector(
            msh=injector[ObjMarshalerManager],
            local_executor=injector[LocalCommandExecutor],
        )

        async with connector.connect() as rce:
            ce: CommandExecutor = rce

            out = await ce.execute(PingCommand())
            self.assertIsInstance(out, PingCommand.Output)

            outs = await asyncio.gather(*[ce.execute(SubprocessCommand(['echo', str(i)])) for i in range(5)])
            self.assertEqual([o.stdout for o in outs], [f'{i}\n'.encode() for i in range(5)])

            with self.assertRaises(RemoteCommandError) as cm:
                await ce.execute(SubprocessCommand(['/nonexistent']))
            self.assertEqual(cm.exception.e.name, 'FileNotFoundError')

            r = await ce.try_execute(SubprocessCommand(['/nonexistent']))
            self.assertIsNone(r.output)
            self.assertIsNotNone(r.exception)

    async def test_log_forwarding(self):
        got: ta.List[ta.Any] = []
        host_handler = RpcMethodTableHandler(inline_notifications={REMOTE_EXECUTION_LOG_METHOD: got.append})
        host, remote = await _connection_pair(host_handler)

        logger = logging.getLogger(f'{__name__}.forwarded')
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        async with host, remote:
            lh = _RemoteLogHandler(remote, asyncio.get_running_loop())
            logger.addHandler(lh)
            try:
                logger.info('hello %s', 'there')
                # Below INFO is not forwarded: the transport logs at debug, and would feed back on itself.
                logger.debug('not forwarded')
                logger.warning('second')

                await remote.ping()
                for _ in range(100):
                    if len(got) >= 2:
                        break
                    await asyncio.sleep(.01)
                await host.ping()

            finally:
                logger.removeHandler(lh)

        self.assertEqual(got, ['hello there', 'second'])
