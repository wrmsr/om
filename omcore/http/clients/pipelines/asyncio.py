# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import asyncio
import dataclasses as dc
import io
import typing as ta

from ....asyncs.asyncio.timeouts import asyncio_maybe_timeout
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ....io.readers import AsyncBytesReader
from ....io.readers import AsyncBytesReaders
from ....io.streambufs.utils import ByteStreamBuffers
from ....lite.bytes import Bytes
from ....lite.check import check
from ...clients.asyncs import AsyncHttpClient
from ...clients.asyncs import AsyncStreamHttpClientResponse
from ...clients.base import HttpClientContext
from ...clients.base import HttpClientRequest
from ...pipelines.clients.clients import IoPipelineHttpClientMessages
from ...pipelines.responses import FullIoPipelineHttpResponse
from ...pipelines.responses import IoPipelineHttpResponseAborted
from ...pipelines.responses import IoPipelineHttpResponseBodyData
from ...pipelines.responses import IoPipelineHttpResponseEnd
from ...pipelines.responses import IoPipelineHttpResponseHead
from ..base import HttpClientError
from .base import BaseIoPipelineHttpClient
from .base import _IoPipelineHttpResponseReaderState
from .base import _raise_http_response_aborted


##


class AsyncioIoPipelineAsyncHttpClient(AsyncHttpClient, BaseIoPipelineHttpClient['AsyncioIoPipelineAsyncHttpClient.Config']):  # noqa
    @dc.dataclass(frozen=True)
    class Config(BaseIoPipelineHttpClient.Config):
        DEFAULT: ta.ClassVar['AsyncioIoPipelineAsyncHttpClient.Config']

    Config.DEFAULT = Config()

    def __init__(
            self,
            config: Config = Config.DEFAULT,
            **pipeline_kwargs: ta.Any,
    ) -> None:
        super().__init__(
            config,
            **pipeline_kwargs,
        )

    #

    class _DriverResponseReader:
        def __init__(
                self,
                drv: PollAsyncioStreamIoPipelineDriver,
        ) -> None:
            super().__init__()

            self._drv = drv
            self._state = _IoPipelineHttpResponseReaderState()

        async def read1(self, n: int = -1, /) -> Bytes:
            if (pending := self._state.read_pending(n)) is not None:
                return pending

            while True:
                # Transport failures mid-body are raised by the driver rather than returned as output, and must be
                # normalized like the pre-head ones in _stream_request - callers only know HttpClientError.
                try:
                    out = check.not_none(await self._drv.next())
                except asyncio.CancelledError:
                    raise
                except HttpClientError:
                    self._state.feed_end()
                    raise
                except Exception as e:
                    self._state.feed_end()
                    raise HttpClientError from e

                if isinstance(out, IoPipelineHttpClientMessages.Output):
                    msg = out.msg

                    if isinstance(msg, IoPipelineHttpResponseBodyData):
                        return self._state.feed_data(msg.data, n)

                    elif isinstance(msg, IoPipelineHttpResponseAborted):
                        self._state.feed_end()
                        _raise_http_response_aborted(msg)

                    elif isinstance(msg, (
                            IoPipelineHttpResponseEnd,
                            IoPipelineMessages.FinalInput,
                            IoPipelineHttpClientMessages.Close,
                    )):
                        return self._state.feed_end()

                    else:
                        raise TypeError(out)  # noqa

                elif isinstance(out, BaseException):
                    self._state.feed_end()
                    raise HttpClientError from out

                else:
                    raise TypeError(out)  # noqa

        async def read(self, n: int = -1, /) -> Bytes:
            if n == 0:
                return b''

            buf = io.BytesIO()
            remaining = n

            while b := await self.read1(remaining):
                buf.write(b)
                if remaining > 0:
                    remaining -= len(b)
                    if remaining == 0:
                        break

            return buf.getvalue()

    #

    async def _stream_request(self, ctx: HttpClientContext, req: HttpClientRequest) -> AsyncStreamHttpClientResponse:
        try:
            prepared = self._prepare_request(req)

            reader, writer = await asyncio_maybe_timeout(
                asyncio.open_connection(
                    prepared.parsed_url.host,
                    prepared.parsed_url.port,
                ),
                self._config.connect_timeout_s,
            )

            drv: ta.Optional[PollAsyncioStreamIoPipelineDriver] = None
            try:
                drv = PollAsyncioStreamIoPipelineDriver(
                    prepared.pipeline_spec,
                    reader,
                    writer,
                )

                drv.enqueue(IoPipelineHttpClientMessages.Request(
                    prepared.full_request,
                    # aggregate=...
                ))

                response: ta.Union[IoPipelineHttpResponseHead, FullIoPipelineHttpResponse, None] = None
                interim_response = False

                while True:
                    if (out := await drv.next()) is not None:
                        if isinstance(out, IoPipelineHttpClientMessages.Output):
                            msg = out.msg

                            if isinstance(msg, IoPipelineHttpResponseHead):
                                if msg.is_interim:
                                    interim_response = True
                                    continue

                                check.none(response)
                                response = msg

                                break

                            if isinstance(msg, FullIoPipelineHttpResponse):
                                if msg.head.is_interim:
                                    continue

                                check.none(response)
                                response = msg

                                drv.enqueue(IoPipelineHttpClientMessages.Close())

                            elif isinstance(msg, IoPipelineHttpResponseAborted):
                                _raise_http_response_aborted(msg)

                            elif isinstance(msg, IoPipelineHttpResponseEnd) and interim_response:
                                interim_response = False

                            elif isinstance(msg, (IoPipelineMessages.FinalInput, IoPipelineHttpClientMessages.Close)):
                                pass

                            else:
                                raise TypeError(out)  # noqa

                        elif isinstance(out, BaseException):
                            raise out

                        else:
                            raise TypeError(out)  # noqa

                    if not drv.pipeline.is_ready:
                        break

                #

                response = check.not_none(response)  # type: ignore[assignment]

                head: IoPipelineHttpResponseHead

                response_reader: AsyncBytesReader

                if isinstance(response, FullIoPipelineHttpResponse):
                    head = check.not_none(response).head

                    response_reader = AsyncBytesReaders.of_bytes(ByteStreamBuffers.to_bytes(response.body, strict=True))

                    await drv.close()
                    writer.close()
                    await writer.wait_closed()

                    async def close() -> None:
                        pass

                elif isinstance(response, IoPipelineHttpResponseHead):
                    head = response

                    response_reader = self._DriverResponseReader(drv)

                    async def close() -> None:
                        # Best-effort: close() runs from __aexit__, so raising here would replace whatever exception
                        # is already propagating. A peer reset in particular leaves the error on the transport's
                        # close-waiter, which the driver already consumed and ignored.
                        try:
                            await drv.close()
                        finally:
                            writer.close()
                            try:
                                await writer.wait_closed()
                            except Exception:  # noqa
                                pass

                else:
                    raise TypeError(response)  # noqa

                #

                return AsyncStreamHttpClientResponse(
                    status=head.status,
                    headers=head.headers,
                    request=req,
                    underlying=drv,
                    _stream=response_reader,
                    _closer=close,
                )

            except BaseException:
                # Cleanup must not replace the exception being propagated.
                try:
                    if drv is not None:
                        await drv.close()
                finally:
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:  # noqa
                        pass

                raise

        except asyncio.CancelledError:
            raise

        except HttpClientError:
            raise

        except Exception as e:
            raise HttpClientError from e
