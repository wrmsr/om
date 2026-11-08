# ruff: noqa: SLF001
"""Stream request bodies through the same HTTP pipeline used by the built-in clients."""

import asyncio
import dataclasses as dc
import socket
import typing as ta

from omcore.http.clients.asyncs import AsyncStreamHttpClientResponse
from omcore.http.clients.base import HttpClientError
from omcore.http.clients.base import HttpClientRequest
from omcore.http.clients.pipelines.asyncio import AsyncioIoPipelineAsyncHttpClient
from omcore.http.clients.pipelines.sync import IoPipelineHttpClient
from omcore.http.clients.sync import StreamHttpClientResponse
from omcore.http.headers import HttpHeaders
from omcore.http.pipelines.clients.clients import IoPipelineHttpClientMessages
from omcore.http.pipelines.requests import IoPipelineHttpRequestBodyData
from omcore.http.pipelines.requests import IoPipelineHttpRequestChunk
from omcore.http.pipelines.requests import IoPipelineHttpRequestChunkedTrailers
from omcore.http.pipelines.requests import IoPipelineHttpRequestEnd
from omcore.http.pipelines.requests import IoPipelineHttpRequestEndChunk
from omcore.http.pipelines.requests import IoPipelineHttpRequestHead
from omcore.http.pipelines.requests import IoPipelineHttpRequestLastChunk
from omcore.http.pipelines.responses import FullIoPipelineHttpResponse
from omcore.http.pipelines.responses import IoPipelineHttpResponseAborted
from omcore.http.pipelines.responses import IoPipelineHttpResponseEnd
from omcore.http.pipelines.responses import IoPipelineHttpResponseHead
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from omcore.io.pipelines.drivers.sync.sockets import SocketSyncIoPipelineDriver
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.readers import AsyncBytesReaders
from omcore.io.readers import BytesReaders
from omcore.io.streambufs.utils import ByteStreamBuffers


##


@dc.dataclass(frozen=True)
class _Send:
    message: ta.Any


class _RequestSender(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Send):
            ctx.feed_out(msg.message)
        else:
            ctx.feed_in(msg)


class _FlushDone(IoPipelineMessages.MayPropagate):
    pass


class _SyncResponseDriver:
    def __init__(self, drv: SocketSyncIoPipelineDriver) -> None:
        super().__init__()
        self._drv = drv

    def next(self) -> ta.Any:
        while isinstance(out := self._drv.next(), _FlushDone):
            pass
        return out


class _AsyncResponseDriver:
    def __init__(self, drv: PollAsyncioStreamIoPipelineDriver) -> None:
        super().__init__()
        self._drv = drv

    async def next(self) -> ta.Any:
        while isinstance(out := await self._drv.next(), _FlushDone):
            pass
        return out


def _prepare(
    client: IoPipelineHttpClient | AsyncioIoPipelineAsyncHttpClient,
    req: HttpClientRequest,
    trailers: HttpHeaders,
) -> tuple[ta.Any, ta.Any, IoPipelineHttpRequestHead]:
    parsed = client.parse_url(req.url)
    headers = HttpHeaders.of(req.headers_).update(
        ('Host', parsed.authority),
        ('User-Agent', 'omcore-http-client/0.1'),
        ('Transfer-Encoding', 'chunked'),
        ('Connection', 'close'),
        if_present='skip',
    )
    if 'content-length' in headers:
        raise ValueError('Content-Length cannot be used with a streamed upload')
    if headers.single['transfer-encoding'].lower() != 'chunked':
        raise ValueError('streamed uploads require Transfer-Encoding: chunked')
    if trailers:
        headers = headers.update(
            ('Trailer', ', '.join(name for name, _ in trailers.raw)),
            if_present='skip',
        )

    spec = client._build_pipeline_spec(
        with_ssl=parsed.is_ssl,
        ssl_kwargs=dict(server_side=False, server_hostname=parsed.host) if parsed.is_ssl else None,
        request_timeout_s=req.timeout_s,
        no_decompress=req.no_decompress,
        flow_auto_read=True,
        innermost_handlers=[_RequestSender()],
    )
    return parsed, spec, IoPipelineHttpRequestHead(
        method=req.method_or_default,
        target=parsed.path,
        headers=headers,
    )


def _response_from_output(out: ta.Any) -> IoPipelineHttpResponseHead | FullIoPipelineHttpResponse | None:
    if isinstance(out, BaseException):
        if isinstance(out, HttpClientError):
            raise out
        raise HttpClientError from out
    if not isinstance(out, IoPipelineHttpClientMessages.Output):
        raise HttpClientError(f'unexpected pipeline output: {out!r}')

    msg = out.msg
    if isinstance(msg, IoPipelineHttpResponseAborted):
        raise HttpClientError(f'HTTP response aborted: {msg.reason_str}')
    if isinstance(msg, IoPipelineHttpResponseHead):
        return None if msg.is_interim else msg
    if isinstance(msg, FullIoPipelineHttpResponse):
        return None if msg.head.is_interim else msg
    if isinstance(msg, IoPipelineHttpResponseEnd):
        return None
    if isinstance(msg, (IoPipelineMessages.FinalInput, IoPipelineHttpClientMessages.Close)):
        raise HttpClientError('connection closed before the response head')
    raise HttpClientError(f'unexpected HTTP response message: {msg!r}')


def _chunk_messages(data: bytes) -> tuple[_Send, ...]:
    return (
        _Send(IoPipelineHttpRequestChunk(len(data))),
        _Send(IoPipelineHttpRequestBodyData(data)),
        _Send(IoPipelineHttpRequestEndChunk()),
    )


def _end_messages(trailers: HttpHeaders) -> tuple[_Send, ...]:
    return (
        _Send(IoPipelineHttpRequestLastChunk()),
        _Send(IoPipelineHttpRequestChunkedTrailers(trailers)),
        _Send(IoPipelineHttpRequestEnd()),
    )


def _send_sync(
    drv: SocketSyncIoPipelineDriver,
    *messages: _Send,
) -> IoPipelineHttpResponseHead | FullIoPipelineHttpResponse | None:
    fence = IoPipelineFlowMessages.FlushOutput()
    fence.add_listener(lambda f: drv.enqueue(_Send(_FlushDone())) if f.is_succeeded() else None)
    drv.enqueue(*messages, _Send(fence))
    while not fence.is_done():
        out = drv.next()
        if isinstance(out, _FlushDone):
            continue
        if out is not None and (response := _response_from_output(out)) is not None:
            return response
        if not drv.pipeline.is_ready:
            raise HttpClientError('pipeline closed while sending the request')
    if not fence.is_succeeded():
        raise HttpClientError('request output flush failed')
    return None


async def _send_async(
    drv: PollAsyncioStreamIoPipelineDriver,
    *messages: _Send,
) -> IoPipelineHttpResponseHead | FullIoPipelineHttpResponse | None:
    fence = IoPipelineFlowMessages.FlushOutput()
    fence.add_listener(lambda f: drv.enqueue(_Send(_FlushDone())) if f.is_succeeded() else None)
    drv.enqueue(*messages, _Send(fence))
    while not fence.is_done():
        out = await drv.next()
        if isinstance(out, _FlushDone):
            continue
        if out is not None and (response := _response_from_output(out)) is not None:
            return response
        if not drv.pipeline.is_ready:
            raise HttpClientError('pipeline closed while sending the request')
    if not fence.is_succeeded():
        raise HttpClientError('request output flush failed')
    return None


def stream_sync_request(
    client: IoPipelineHttpClient,
    req: HttpClientRequest,
    source: ta.BinaryIO,
    *,
    chunk_size: int,
    trailers: HttpHeaders,
) -> StreamHttpClientResponse:
    parsed, spec, head = _prepare(client, req, trailers)
    sock = socket.create_connection((parsed.host, parsed.port), timeout=client.config.connect_timeout_s)
    drv: SocketSyncIoPipelineDriver | None = None
    try:
        sock.settimeout(None)
        client._try_set_nodelay(sock)
        drv = SocketSyncIoPipelineDriver(spec, sock)

        response = _send_sync(drv, _Send(head))
        while response is None and (data := source.read(chunk_size)):
            response = _send_sync(drv, *_chunk_messages(data))
        if response is None:
            response = _send_sync(drv, *_end_messages(trailers))
        while response is None:
            out = drv.next()
            if isinstance(out, _FlushDone):
                continue
            if out is not None:
                response = _response_from_output(out)
            if response is None and not drv.pipeline.is_ready:
                raise HttpClientError('connection closed before the response head')

        if isinstance(response, FullIoPipelineHttpResponse):
            body = ByteStreamBuffers.to_bytes(response.body, strict=True)
            drv.close()
            sock.close()
            return StreamHttpClientResponse(
                request=req,
                status=response.head.status,
                headers=response.head.headers,
                _stream=BytesReaders.of_bytes(body),
            )

        def close() -> None:
            try:
                drv.close()
            finally:
                sock.close()

        return StreamHttpClientResponse(
            request=req,
            status=response.status,
            headers=response.headers,
            underlying=drv,
            _stream=IoPipelineHttpClient._DriverResponseReader(
                ta.cast(SocketSyncIoPipelineDriver, _SyncResponseDriver(drv)), sock,
            ),
            _closer=close,
        )
    except BaseException:
        try:
            if drv is not None:
                drv.close()
        finally:
            sock.close()
        raise


async def stream_async_request(
    client: AsyncioIoPipelineAsyncHttpClient,
    req: HttpClientRequest,
    source: ta.BinaryIO,
    *,
    chunk_size: int,
    trailers: HttpHeaders,
) -> AsyncStreamHttpClientResponse:
    parsed, spec, head = _prepare(client, req, trailers)
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(parsed.host, parsed.port),
        timeout=client.config.connect_timeout_s,
    )
    drv: PollAsyncioStreamIoPipelineDriver | None = None
    try:
        drv = PollAsyncioStreamIoPipelineDriver(spec, reader, writer)

        response = await _send_async(drv, _Send(head))
        while response is None and (data := await asyncio.to_thread(source.read, chunk_size)):
            response = await _send_async(drv, *_chunk_messages(data))
        if response is None:
            response = await _send_async(drv, *_end_messages(trailers))
        while response is None:
            out = await drv.next()
            if isinstance(out, _FlushDone):
                continue
            if out is not None:
                response = _response_from_output(out)
            if response is None and not drv.pipeline.is_ready:
                raise HttpClientError('connection closed before the response head')

        if isinstance(response, FullIoPipelineHttpResponse):
            body = ByteStreamBuffers.to_bytes(response.body, strict=True)
            await drv.close()
            writer.close()
            await writer.wait_closed()
            return AsyncStreamHttpClientResponse(
                request=req,
                status=response.head.status,
                headers=response.head.headers,
                _stream=AsyncBytesReaders.of_bytes(body),
            )

        async def close() -> None:
            try:
                await drv.close()
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

        return AsyncStreamHttpClientResponse(
            request=req,
            status=response.status,
            headers=response.headers,
            underlying=drv,
            _stream=AsyncioIoPipelineAsyncHttpClient._DriverResponseReader(
                ta.cast(PollAsyncioStreamIoPipelineDriver, _AsyncResponseDriver(drv)),
            ),
            _closer=close,
        )
    except BaseException:
        try:
            if drv is not None:
                await drv.close()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
        raise
