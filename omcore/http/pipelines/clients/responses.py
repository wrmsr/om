# ruff: noqa: UP006 UP045
# @om-lite
import collections
import typing as ta

from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineHandlerNotification
from ....io.pipelines.core import IoPipelineHandlerNotifications
from ....io.pipelines.core import IoPipelineMessages
from ....lite.check import check
from ...parsing import HttpParser
from ..aggregators import IoPipelineHttpObjectAggregatorDecoder
from ..bodymodes import IoPipelineHttpBodyMode
from ..chunking import IoPipelineHttpObjectDechunker
from ..compression.decompressors import IoPipelineHttpObjectDecompressor
from ..decoders import IoPipelineHttpDecodingConfig
from ..decoders import IoPipelineHttpObjectDecoder
from ..objects import IoPipelineHttpMessageHead
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestHead
from ..responses import IoPipelineHttpResponseHead
from ..responses import IoPipelineHttpResponseObjects


##


class IoPipelineHttpResponseDecoder(IoPipelineHttpResponseObjects, IoPipelineHttpObjectDecoder):
    """
    Request-agnostic HTTP response decoder.

    Framing uses only the response status and headers. This keeps the decoder useful on its own, but means it cannot
    infer the special response semantics of HEAD or CONNECT requests. Real HTTP clients should use
    IoPipelineHttpClientResponseDecoder instead.
    """

    _parse_mode: ta.Final = HttpParser.Mode.RESPONSE
    _if_content_length_missing: ta.Final = 'eof'

    def _select_body_mode(self, head: IoPipelineHttpMessageHead) -> IoPipelineHttpBodyMode:
        head = check.isinstance(head, IoPipelineHttpResponseHead)

        if head.status == 101:
            return IoPipelineHttpBodyMode('tunnel', None)

        if 100 <= head.status < 200 or head.status in (204, 304):
            return IoPipelineHttpBodyMode('empty', None)

        return super()._select_body_mode(head)


#


class IoPipelineHttpClientResponseDecoder(IoPipelineHttpResponseDecoder):
    """
    HTTP client response decoder correlating responses with outbound request methods.

    Informational responses retain the current request method. Final responses consume it, allowing HEAD and CONNECT
    response framing to take precedence over otherwise misleading Content-Length or Transfer-Encoding headers.
    """

    def __init__(
            self,
            *,
            config: IoPipelineHttpDecodingConfig = IoPipelineHttpDecodingConfig.DEFAULT,
    ) -> None:
        super().__init__(config=config)

        self._request_methods: ta.Deque[str] = collections.deque()

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, (IoPipelineHandlerNotifications.Added, IoPipelineHandlerNotifications.Removed)):
            self._request_methods.clear()

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, FullIoPipelineHttpRequest):
            self._request_methods.append(msg.head.method)

        elif isinstance(msg, IoPipelineHttpRequestHead):
            self._request_methods.append(msg.method)

        elif isinstance(msg, IoPipelineMessages.FinalOutput):
            self._request_methods.clear()

        ctx.feed_out(msg)

    def _select_body_mode(self, head: IoPipelineHttpMessageHead) -> IoPipelineHttpBodyMode:
        head = check.isinstance(head, IoPipelineHttpResponseHead)

        if not self._request_methods:
            raise RuntimeError('received HTTP response without a corresponding request')

        if head.is_interim:
            return super()._select_body_mode(head)

        method = self._request_methods.popleft()

        if head.status == 101:
            self._request_methods.clear()
            return IoPipelineHttpBodyMode('tunnel', None)

        if method == 'HEAD':
            return IoPipelineHttpBodyMode('empty', None)

        if method == 'CONNECT' and 200 <= head.status < 300:
            self._request_methods.clear()
            return IoPipelineHttpBodyMode('tunnel', None)

        return super()._select_body_mode(head)


##


class IoPipelineHttpResponseAggregatorDecoder(
    IoPipelineHttpResponseObjects,
    IoPipelineHttpObjectAggregatorDecoder,
):
    _if_content_length_missing: ta.Final = 'eof'


##


class IoPipelineHttpResponseDechunker(IoPipelineHttpResponseObjects, IoPipelineHttpObjectDechunker):
    pass


##


class IoPipelineHttpResponseDecompressor(IoPipelineHttpResponseObjects, IoPipelineHttpObjectDecompressor):
    pass
