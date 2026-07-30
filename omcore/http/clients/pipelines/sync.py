# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import collections  # noqa
import dataclasses as dc
import io
import socket
import typing as ta

from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ....io.readers import BytesReader
from ....io.readers import BytesReaders
from ....io.streambufs.types import Bytes
from ....io.streambufs.utils import ByteStreamBuffers
from ....lite.check import check
from ...clients.base import HttpClientContext
from ...clients.base import HttpClientRequest
from ...clients.sync import HttpClient
from ...clients.sync import StreamHttpClientResponse
from ...pipelines.clients.clients import IoPipelineHttpClientMessages
from ...pipelines.responses import FullIoPipelineHttpResponse
from ...pipelines.responses import IoPipelineHttpResponseAborted
from ...pipelines.responses import IoPipelineHttpResponseBodyData
from ...pipelines.responses import IoPipelineHttpResponseEnd
from ...pipelines.responses import IoPipelineHttpResponseHead
from ..base import HttpClientError
from .base import _IoPipelineHttpResponseReaderState
from .base import _raise_http_response_aborted
from .base import BaseIoPipelineHttpClient


##


class IoPipelineHttpClient(HttpClient, BaseIoPipelineHttpClient['IoPipelineHttpClient.Config']):
    @dc.dataclass(frozen=True)
    class Config(BaseIoPipelineHttpClient.Config):
        DEFAULT: ta.ClassVar['IoPipelineHttpClient.Config']

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
                drv: SyncSocketIoPipelineDriver,
                sock: 'socket.socket',
        ) -> None:
            super().__init__()

            self._drv = drv
            self._sock = sock

            self._state = _IoPipelineHttpResponseReaderState()

        def read1(self, n: int = -1, /) -> Bytes:
            if (pending := self._state.read_pending(n)) is not None:
                return pending

            while True:
                out = check.not_none(self._drv.next())

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

        def read(self, n: int = -1, /) -> Bytes:
            if n == 0:
                return b''

            buf = io.BytesIO()
            remaining = n

            while b := self.read1(remaining):
                buf.write(b)
                if remaining > 0:
                    remaining -= len(b)
                    if remaining == 0:
                        break

            return buf.getvalue()

    #

    def _stream_request(self, ctx: HttpClientContext, req: HttpClientRequest) -> StreamHttpClientResponse:
        try:
            prepared = self._prepare_request(req)

            sock = socket.create_connection(
                (prepared.parsed_url.host, prepared.parsed_url.port),
                **(dict(timeout=self._config.connect_timeout_s) if self._config.connect_timeout_s is not None else {}),  # type: ignore[arg-type]  # noqa
            )

            drv: ta.Optional[SyncSocketIoPipelineDriver] = None
            try:
                sock.settimeout(None)
                self._try_set_nodelay(sock)

                drv = SyncSocketIoPipelineDriver(prepared.pipeline_spec, sock)

                drv.enqueue(IoPipelineHttpClientMessages.Request(
                    prepared.full_request,
                    # aggregate=...
                ))

                response: ta.Union[IoPipelineHttpResponseHead, FullIoPipelineHttpResponse, None] = None
                interim_response = False

                while True:
                    if (out := drv.next()) is not None:
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

                response_reader: BytesReader

                if isinstance(response, FullIoPipelineHttpResponse):
                    head = check.not_none(response).head

                    response_reader = BytesReaders.of_bytes(ByteStreamBuffers.to_bytes(response.body, strict=True))

                    drv.close()
                    sock.close()

                    def close() -> None:
                        pass

                elif isinstance(response, IoPipelineHttpResponseHead):
                    head = response

                    response_reader = self._DriverResponseReader(drv, sock)

                    def close() -> None:
                        try:
                            drv.close()
                        finally:
                            sock.close()

                else:
                    raise TypeError(response)  # noqa

                #

                return StreamHttpClientResponse(
                    status=head.status,
                    headers=head.headers,
                    request=req,
                    underlying=drv,
                    _stream=response_reader,
                    _closer=close,
                )

            except BaseException:
                try:
                    if drv is not None:
                        drv.close()
                finally:
                    sock.close()

                raise

        except HttpClientError:
            raise

        except Exception as e:
            raise HttpClientError from e
