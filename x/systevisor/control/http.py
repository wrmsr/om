# ruff: noqa: UP006 UP007 UP037 UP045
import collections
import dataclasses as dc
import errno
import os
import socket
import stat
import typing as ta

from omcore.http.headers import HttpHeaders
from omcore.http.pipelines.requests import FullIoPipelineHttpRequest
from omcore.http.pipelines.requests import IoPipelineHttpRequestAborted
from omcore.http.pipelines.responses import FullIoPipelineHttpResponse
from omcore.http.pipelines.responses import IoPipelineHttpResponseBodyData
from omcore.http.pipelines.responses import IoPipelineHttpResponseEnd
from omcore.http.pipelines.responses import IoPipelineHttpResponseHead
from omcore.http.pipelines.servers.requests import IoPipelineHttpRequestAggregatorDecoder
from omcore.http.pipelines.servers.requests import IoPipelineHttpRequestDecoder
from omcore.http.pipelines.servers.responses import IoPipelineHttpResponseChunker
from omcore.http.pipelines.servers.responses import IoPipelineHttpResponseEncoder
from omcore.io.fdio.handlers import ServerSocketFdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.streambufs.utils import ByteStreamBuffers
from omcore.sockets.addresses import SocketAddress

from ..configs.models import SystevisorApiConfig
from .api import SystevisorApiApplication
from .api import SystevisorApiRequest
from .api import SystevisorApiResponse
from .api import SystevisorApiStreamResponse
from .api import SystevisorApiStreamSubscription
from .configs import SystevisorConfigPreparedChange


@dc.dataclass(frozen=True)
class SystevisorHttpStreamPush(IoPipelineHandlerNotification):
    data: bytes


class SystevisorHttpConnectionIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            application: SystevisorApiApplication,
            queue_capacity_bytes: int,
    ) -> None:
        super().__init__()
        if queue_capacity_bytes < 1:
            raise ValueError(queue_capacity_bytes)
        self._application = application
        self._queue_capacity_bytes = queue_capacity_bytes
        self._pending: ta.Deque[bytes] = collections.deque()
        self._pending_bytes = 0
        self._dropped_items = 0
        self._dropped_bytes = 0
        self._paused = False
        self._pump_scheduled = False
        self._responded = False
        self._stream_response: ta.Optional[SystevisorApiStreamResponse] = None
        self._subscription: ta.Optional[SystevisorApiStreamSubscription] = None

    def _close_subscription(self) -> None:
        if self._subscription is not None:
            self._subscription.close()
            self._subscription = None

    def _enqueue(self, data: bytes) -> None:
        if not data:
            return
        if len(data) > self._queue_capacity_bytes:
            self._dropped_items += 1
            self._dropped_bytes += len(data)
            return
        while self._pending and self._pending_bytes + len(data) > self._queue_capacity_bytes:
            dropped = self._pending.popleft()
            self._pending_bytes -= len(dropped)
            self._dropped_items += 1
            self._dropped_bytes += len(dropped)
        self._pending.append(data)
        self._pending_bytes += len(data)

    def _schedule_pump(self, ctx: IoPipelineHandlerContext) -> None:
        if self._pump_scheduled or self._paused:
            return
        if not self._pending and not self._dropped_items:
            return
        self._pump_scheduled = True

        def pump(deferred_ctx: IoPipelineHandlerContext) -> None:
            self._pump_scheduled = False
            self._pump(deferred_ctx)

        ctx.defer(pump)

    def _pump(self, ctx: IoPipelineHandlerContext) -> None:
        if self._paused:
            return
        response = self._stream_response
        if response is None:
            return
        emitted_bytes = 0
        if self._dropped_items:
            gap = response.stream.gap(self._dropped_items, self._dropped_bytes)
            self._dropped_items = 0
            self._dropped_bytes = 0
            ctx.feed_out(IoPipelineHttpResponseBodyData(gap))
            emitted_bytes += len(gap)
        while self._pending and emitted_bytes < 32 * 1024:
            data = self._pending.popleft()
            self._pending_bytes -= len(data)
            ctx.feed_out(IoPipelineHttpResponseBodyData(data))
            emitted_bytes += len(data)
        if emitted_bytes:
            ctx.feed_out(IoPipelineFlowMessages.FlushOutput())
        self._schedule_pump(ctx)

    def _begin_stream(
            self,
            ctx: IoPipelineHandlerContext,
            response: SystevisorApiStreamResponse,
    ) -> None:
        self._stream_response = response
        headers = HttpHeaders([
            ('Content-Type', response.stream.content_type),
            ('Transfer-Encoding', 'chunked'),
            ('Cache-Control', 'no-store'),
            ('Connection', 'close'),
            *response.headers.items(),
        ])
        ctx.feed_out(IoPipelineHttpResponseHead(
            status=response.status,
            reason=IoPipelineHttpResponseHead.get_reason_phrase(response.status),
            headers=headers,
        ))
        for data in response.stream.initial():
            self._enqueue(data)

        handler_ref = ctx.ref
        def on_data(data: bytes) -> None:
            if handler_ref.invalidated or not handler_ref.pipeline.is_ready:
                return
            handler_ref.pipeline.notify(handler_ref, SystevisorHttpStreamPush(data))

        self._subscription = response.stream.subscribe(on_data)
        self._schedule_pump(ctx)

    @staticmethod
    def _send_response(ctx: IoPipelineHandlerContext, response: SystevisorApiResponse) -> None:
        ctx.feed_out(FullIoPipelineHttpResponse.simple(
            status=response.status,
            content_type=response.content_type,
            body=response.body,
            connection='close',
            headers=response.headers,
        ))
        ctx.feed_final_output()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            IoPipelineFlow.maybe_ready_for_input(ctx)
            return
        if isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._paused = True
            ctx.feed_in(msg)
            return
        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._paused = False
            ctx.feed_in(msg)
            self._schedule_pump(ctx)
            return
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._close_subscription()
            ctx.feed_in(msg)
            if self._stream_response is not None and not ctx.pipeline.saw_final_output:
                ctx.feed_out(IoPipelineHttpResponseEnd())
                ctx.feed_final_output()
            elif not self._responded and not ctx.pipeline.saw_final_output:
                ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineHttpRequestAborted):
            if not self._responded:
                self._responded = True
                self._send_response(ctx, SystevisorApiResponse(
                    status=400,
                    body=b'{"error":{"message":"invalid HTTP request","type":"invalid_request"},"status":400}',
                ))
            return
        if not isinstance(msg, FullIoPipelineHttpRequest):
            ctx.feed_in(msg)
            return
        if self._responded:
            raise RuntimeError('HTTP connection accepts one request')
        self._responded = True
        result = self._application.handle(SystevisorApiRequest(
            method=msg.head.method,
            target=msg.head.target,
            headers={name.lower(): value for name, value in msg.head.headers.raw},
            body=bytes(ByteStreamBuffers.to_bytes(msg.body)),
        ))
        if isinstance(result, SystevisorApiResponse):
            self._send_response(ctx, result)
        elif isinstance(result, SystevisorApiStreamResponse):
            self._begin_stream(ctx, result)
        else:
            raise TypeError(result)

    def notify(self, ctx: IoPipelineHandlerContext, notification: IoPipelineHandlerNotification) -> None:
        if isinstance(notification, SystevisorHttpStreamPush):
            self._enqueue(notification.data)
            self._schedule_pump(ctx)
        elif isinstance(notification, IoPipelineHandlerNotifications.Removed):
            self._close_subscription()

    @classmethod
    def build_pipeline_spec(
            cls,
            application: SystevisorApiApplication,
            queue_capacity_bytes: int,
    ) -> IoPipeline.Spec:
        return IoPipeline.Spec([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(),
            IoPipelineHttpResponseEncoder(),
            IoPipelineHttpResponseChunker(),
            SystevisorHttpConnectionIoPipelineHandler(application, queue_capacity_bytes),
        ])


SystevisorHttpListenerKey = ta.Tuple[ta.Union[str, int], ...]


@dc.dataclass(frozen=True)
class SystevisorHttpListener:
    key: SystevisorHttpListenerKey
    handler: ServerSocketFdioHandler
    unix_socket_identity: ta.Optional[ta.Tuple[str, int, int]] = None


class SystevisorHttpPreparedChange(SystevisorConfigPreparedChange):
    def __init__(
            self,
            server: 'SystevisorHttpServer',
            config: SystevisorApiConfig,
            desired_keys: ta.Sequence[SystevisorHttpListenerKey],
            created: ta.Mapping[SystevisorHttpListenerKey, SystevisorHttpListener],
            previous_unix_mode: ta.Optional[ta.Tuple[str, int]],
    ) -> None:
        self._server = server
        self._config = config
        self._desired_keys = tuple(desired_keys)
        self._created = dict(created)
        self._previous_unix_mode = previous_unix_mode
        self._finished = False

    def commit(self) -> None:
        if self._finished:
            raise RuntimeError('HTTP configuration change is already finished')
        self._server._commit_prepared(self._config, self._desired_keys, self._created)  # noqa: SLF001
        self._finished = True

    def rollback(self) -> None:
        if self._finished:
            return
        for listener in self._created.values():
            listener.handler.close()
            if listener.unix_socket_identity is not None:
                self._server._unlink_owned_unix_socket(listener.unix_socket_identity)  # noqa: SLF001
        if self._previous_unix_mode is not None:
            path, mode = self._previous_unix_mode
            try:
                os.chmod(path, mode)
            except FileNotFoundError:
                pass
        self._finished = True


class SystevisorHttpServer:
    def __init__(
            self,
            fdio_manager: FdioManager,
            application: SystevisorApiApplication,
    ) -> None:
        self._fdio_manager = fdio_manager
        self._application = application
        self._listeners: ta.Dict[SystevisorHttpListenerKey, SystevisorHttpListener] = {}
        self._connections: ta.Set[IoPipelineDriverSocketFdioHandler] = set()
        self._queue_capacity_bytes = 1024 * 1024

    @property
    def started(self) -> bool:
        return bool(self._listeners)

    @staticmethod
    def _bind_unix_socket(path: str, mode: int) -> ta.Tuple[socket.socket, ta.Tuple[str, int, int]]:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            try:
                sock.bind(path)
            except OSError as exc:
                if exc.errno != errno.EADDRINUSE:
                    raise
                probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    probe.connect(path)
                except OSError as probe_exc:
                    if probe_exc.errno not in (errno.ECONNREFUSED, errno.ENOENT):
                        raise
                else:
                    raise OSError(errno.EADDRINUSE, 'Unix socket is active', path)
                finally:
                    probe.close()
                path_stat = os.lstat(path)
                if not stat.S_ISSOCK(path_stat.st_mode):
                    raise OSError(errno.EADDRINUSE, 'existing path is not a socket', path) from None
                os.unlink(path)
                sock.bind(path)
            os.chmod(path, mode)
            bound_stat = os.lstat(path)
            return sock, (path, bound_stat.st_dev, bound_stat.st_ino)
        except BaseException:
            sock.close()
            raise

    def _accept(self, sock: socket.socket, address: SocketAddress) -> None:
        self._connections = {connection for connection in self._connections if not connection.closed}
        try:
            connection = IoPipelineDriverSocketFdioHandler(
                sock,
                address,
                SystevisorHttpConnectionIoPipelineHandler.build_pipeline_spec(
                    self._application,
                    self._queue_capacity_bytes,
                ),
            )
            connection.next(read=False)
            if connection.is_active:
                self._connections.add(connection)
                self._fdio_manager.register(connection)
            else:
                connection.close()
        except BaseException:
            sock.close()
            raise

    def start(self, config: SystevisorApiConfig) -> None:
        if self.started:
            raise RuntimeError('HTTP server is already started')
        self.reconfigure(config)

    @staticmethod
    def _listener_keys(config: SystevisorApiConfig) -> ta.Sequence[SystevisorHttpListenerKey]:
        keys: ta.List[SystevisorHttpListenerKey] = []
        if config.unix_socket is not None:
            keys.append(('unix', config.unix_socket))
        if config.tcp_host is not None and config.tcp_port is not None:
            keys.append(('tcp', config.tcp_host, config.tcp_port))
        return tuple(keys)

    def _create_listener(
            self,
            key: SystevisorHttpListenerKey,
            config: SystevisorApiConfig,
    ) -> SystevisorHttpListener:
        if key[0] == 'unix':
            path = ta.cast(str, key[1])
            unix_socket, unix_identity = self._bind_unix_socket(path, config.unix_socket_mode)
            return SystevisorHttpListener(
                key,
                ServerSocketFdioHandler(unix_socket, self._accept),
                unix_identity,
            )
        if key[0] == 'tcp':
            host = ta.cast(str, key[1])
            port = ta.cast(int, key[2])
            tcp_socket = socket.create_server((host, port))
            return SystevisorHttpListener(key, ServerSocketFdioHandler(tcp_socket, self._accept))
        raise ValueError(key)

    def prepare_reconfigure(self, config: SystevisorApiConfig) -> SystevisorHttpPreparedChange:
        if config.stream_queue_bytes < 1:
            raise ValueError(config.stream_queue_bytes)
        desired_keys = self._listener_keys(config)
        created: ta.Dict[SystevisorHttpListenerKey, SystevisorHttpListener] = {}
        previous_unix_mode: ta.Optional[ta.Tuple[str, int]] = None
        try:
            for key in desired_keys:
                if key not in self._listeners:
                    created[key] = self._create_listener(key, config)
            if config.unix_socket is not None and ('unix', config.unix_socket) in self._listeners:
                previous_unix_mode = (
                    config.unix_socket,
                    os.stat(config.unix_socket).st_mode & 0o777,
                )
                os.chmod(config.unix_socket, config.unix_socket_mode)
        except BaseException:
            for listener in created.values():
                listener.handler.close()
                if listener.unix_socket_identity is not None:
                    self._unlink_owned_unix_socket(listener.unix_socket_identity)
            if previous_unix_mode is not None:
                os.chmod(*previous_unix_mode)
            raise
        return SystevisorHttpPreparedChange(
            self,
            config,
            desired_keys,
            created,
            previous_unix_mode,
        )

    def _commit_prepared(
            self,
            config: SystevisorApiConfig,
            desired_keys: ta.Sequence[SystevisorHttpListenerKey],
            created: ta.Mapping[SystevisorHttpListenerKey, SystevisorHttpListener],
    ) -> None:
        registered: ta.List[SystevisorHttpListener] = []
        try:
            for listener in created.values():
                self._fdio_manager.register(listener.handler)
                registered.append(listener)
        except BaseException:
            for listener in registered:
                self._fdio_manager.unregister(listener.handler)
            raise
        retained = {
            key: self._listeners[key] if key in self._listeners else created[key]
            for key in desired_keys
        }
        for key, listener in self._listeners.items():
            if key not in retained:
                listener.handler.close()
                if listener.unix_socket_identity is not None:
                    self._unlink_owned_unix_socket(listener.unix_socket_identity)
        self._listeners = retained
        self._queue_capacity_bytes = config.stream_queue_bytes

    def reconfigure(self, config: SystevisorApiConfig) -> None:
        change = self.prepare_reconfigure(config)
        try:
            change.commit()
        except BaseException:
            change.rollback()
            raise

    @staticmethod
    def _unlink_owned_unix_socket(identity: ta.Tuple[str, int, int]) -> None:
        path, device, inode = identity
        try:
            path_stat = os.lstat(path)
        except FileNotFoundError:
            return
        if stat.S_ISSOCK(path_stat.st_mode) and (path_stat.st_dev, path_stat.st_ino) == (device, inode):
            os.unlink(path)

    def close(self) -> None:
        for listener in self._listeners.values():
            listener.handler.close()
            if listener.unix_socket_identity is not None:
                self._unlink_owned_unix_socket(listener.unix_socket_identity)
        self._listeners.clear()
        for connection in self._connections:
            connection.close()
        self._connections.clear()
