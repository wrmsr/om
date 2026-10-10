# ruff: noqa: SLF001 UP006 UP007 UP045 UP037 UP033
# @om-lite
"""
Multiplexed streams over real sockets and real drivers: many concurrent request/response streams with payloads far
larger than the stream windows, the drivers' write watermarks, and the per-turn budget - optionally under TLS.
"""
import asyncio
import functools
import socket
import ssl
import time
import typing as ta
import unittest

from .....secrets import tempssl
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...drivers.types import IoPipelineDriverState
from ...flow.stub import StubIoPipelineFlowService
from ...ssl.handlers import SslIoPipelineHandler
from ..handlers import IoPipelineMultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..types import IoPipelineMultiplexMessages
from .apps import AppFactory
from .apps import StreamApp
from .apps import app_spec
from .apps import payload
from .sshlike import SSH_CODEC
from .sshlike import SshLikeAdapter
from .sshlike import SshOpenInfo
from .wire import FrameCodecIoPipelineHandler


##


_N_STREAMS = 12
_REQUEST_SIZE = 150_000
_RESPONSE_SIZE = 400_000


@functools.lru_cache(maxsize=None)
def _cert() -> tempssl.SslCert:
    from .....subprocesses import sync as _  # import side-effect installing _DEFAULT_SUBPROCESSES  # noqa

    return tempssl.generate_temp_localhost_ssl_cert().cert


def _tls(server_side: bool) -> SslIoPipelineHandler:
    cert = _cert()
    if server_side:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert.cert_file, cert.key_file)
        return SslIoPipelineHandler(ctx, server_side=True)
    return SslIoPipelineHandler(
        ssl.create_default_context(cafile=cert.cert_file),
        server_side=False,
        server_hostname='localhost',
    )


class _Session:
    """A client and a server multiplexer, many request/response streams between them, and their checks."""

    def __init__(self, *, tls: bool) -> None:
        super().__init__()

        self.requests = {i: payload(('req', i), _REQUEST_SIZE) for i in range(_N_STREAMS)}
        self.server_factory = AppFactory(
            lambda o: StreamApp(respond=payload(('resp', o.info.info), _RESPONSE_SIZE), manual_read=True),
            auto_read=False,
        )
        config = IoPipelineMultiplexConfig(turn_output_budget=32 * 1024)
        self.client_mux = MultiplexIoPipelineHandler(
            SshLikeAdapter(window=32 * 1024, max_packet=8 * 1024),
            AppFactory(lambda o: StreamApp()),
            config=config,
        )
        self.server_mux = MultiplexIoPipelineHandler(
            SshLikeAdapter(window=32 * 1024, max_packet=8 * 1024),
            self.server_factory,
            config=config,
        )
        self.client_apps = {i: StreamApp(send=self.requests[i], shutdown_after_send=True) for i in range(_N_STREAMS)}

        def spec(mux: MultiplexIoPipelineHandler, server_side: bool) -> IoPipeline.Spec:
            handlers: ta.List[IoPipelineHandler] = [FrameCodecIoPipelineHandler(SSH_CODEC), mux]
            if tls:
                handlers.insert(0, _tls(server_side))
            return IoPipeline.Spec(handlers, services=[StubIoPipelineFlowService(auto_read=False)])

        self.client_spec = spec(self.client_mux, False)
        self.server_spec = spec(self.server_mux, True)

    def open_messages(self) -> ta.List[ta.Any]:
        return [
            IoPipelineMultiplexMessages.OpenStream(app_spec(app), SshOpenInfo('session', str(i).encode()))
            for i, app in self.client_apps.items()
        ]

    def done(self) -> bool:
        return all(a.final_output.is_done() for a in self.client_apps.values())

    def shutdown_messages(self) -> ta.List[ta.Any]:
        return [IoPipelineMultiplexMessages.Shutdown()]

    def check(self, tc: unittest.TestCase) -> None:
        for i, app in self.client_apps.items():
            with tc.subTest(stream=i):
                tc.assertEqual(app.errors, [])
                tc.assertTrue(bytes(app.received) == payload(('resp', str(i).encode()), _RESPONSE_SIZE))
                tc.assertTrue(app.final_output.is_succeeded())
        tc.assertEqual(len(self.server_factory.apps), _N_STREAMS)
        for sapp in self.server_factory.apps.values():
            i = int(ta.cast(ta.Any, sapp.metadata).info.info)
            tc.assertTrue(bytes(sapp.received) == self.requests[i])
            tc.assertEqual(sapp.errors, [])
            tc.assertGreater(sapp.reads_requested, 1)
        tc.assertEqual(len(self.client_mux.streams), 0)
        tc.assertEqual(len(self.server_mux.streams), 0)


class TestMultiplexOverFdio(unittest.TestCase):
    def _run(self, *, tls: bool) -> None:
        sess = _Session(tls=tls)
        sock_c, sock_s = socket.socketpair()
        poller = SelectFdioPoller()
        cfg = IoPipelineDriverSocketFdioHandler.Config(write_high_watermark=16 * 1024, write_low_watermark=4 * 1024)
        client = IoPipelineDriverSocketFdioHandler(sock_c, ('c', 0), sess.client_spec, cfg)
        server = IoPipelineDriverSocketFdioHandler(sock_s, ('s', 0), sess.server_spec, cfg)
        manager = FdioManager(poller)
        try:
            for d in (client, server):
                self.assertIsNone(d.next(read=False))
                manager.register(d)
            client.enqueue(*sess.open_messages())
            self.assertIsNone(client.next(read=False))

            deadline = time.monotonic() + 60.
            while not sess.done():
                self.assertLess(time.monotonic(), deadline)
                manager.poll(timeout=1.)

            client.enqueue(*sess.shutdown_messages())
            self.assertIsNone(client.next(read=False))
            while client.is_active or server.is_active:
                self.assertLess(time.monotonic(), deadline)
                manager.poll(timeout=1.)

            sess.check(self)
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server.state, IoPipelineDriverState.CLOSED)
        finally:
            client.close()
            server.close()
            poller.close()

    def test_many_streams(self) -> None:
        self._run(tls=False)

    def test_many_streams_over_tls(self) -> None:
        self._run(tls=True)


class TestMultiplexOverAsyncio(AsyncioIsolatedAsyncTestCase):
    async def _run(self, *, tls: bool) -> None:
        sess = _Session(tls=tls)
        server_done: asyncio.Future = asyncio.get_running_loop().create_future()

        async def on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            drv = PollAsyncioStreamIoPipelineDriver(
                sess.server_spec,
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(write_high_watermark=16 * 1024, write_low_watermark=4 * 1024),
            )
            try:
                await drv.loop_until_done()
            except BaseException as e:  # noqa
                server_done.set_exception(e)
            else:
                server_done.set_result(drv.state)
            finally:
                await drv.close()

        server = await asyncio.start_server(on_connect, '127.0.0.1', 0)
        try:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection('127.0.0.1', port)
            client = PollAsyncioStreamIoPipelineDriver(
                sess.client_spec,
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(write_high_watermark=16 * 1024, write_low_watermark=4 * 1024),
            )
            try:
                # Once every stream has finished, shut the connection down gracefully.
                remaining = [len(sess.client_apps)]

                def on_stream_done(_: ta.Any) -> None:
                    remaining[0] -= 1
                    if not remaining[0]:
                        client.enqueue(*sess.shutdown_messages())

                for app in sess.client_apps.values():
                    app.final_output.add_listener(on_stream_done)

                client.enqueue(*sess.open_messages())
                await asyncio.wait_for(asyncio.gather(client.loop_until_done(), server_done), 60.)
            finally:
                await client.close()

            sess.check(self)
            self.assertIs(client.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server_done.result(), IoPipelineDriverState.CLOSED)
        finally:
            server.close()
            await server.wait_closed()

    async def test_many_streams(self) -> None:
        await self._run(tls=False)

    async def test_many_streams_over_tls(self) -> None:
        await self._run(tls=True)
