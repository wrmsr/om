# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta

from ....io.pipelines.core import IoPipelineHandlerContext
from ...parsing import HttpParser
from ..aggregators import IoPipelineHttpObjectAggregatorDecoder
from ..bodymodes import IoPipelineHttpBodyMode
from ..chunking import IoPipelineHttpObjectDechunker
from ..compression.decompressors import IoPipelineHttpObjectDecompressor
from ..decoders import IoPipelineHttpObjectDecoder
from ..objects import IoPipelineHttpMessageHead
from ..requests import IoPipelineHttpRequestObjects
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseHead


##


class IoPipelineHttpRequestDecoder(IoPipelineHttpRequestObjects, IoPipelineHttpObjectDecoder):
    _parse_mode: ta.Final = HttpParser.Mode.REQUEST
    _if_content_length_missing: ta.Final = 'empty'

    def _select_body_mode(self, head: IoPipelineHttpMessageHead) -> IoPipelineHttpBodyMode:
        mode = super()._select_body_mode(head)
        # Park trailing bytes after an Upgrade request instead of parsing them as a second HTTP request, so coalesced
        # upgraded-protocol frames (e.g. WebSocket) survive until the upgrade handler accepts or rejects.
        if (
                mode.mode == 'empty' and
                head.headers.contains_list_value('connection', 'upgrade', ignore_case=True) and
                bool(head.headers.lower.get('upgrade'))
        ):
            return IoPipelineHttpBodyMode('pending_upgrade', None)
        return mode

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(self._state, self._PendingUpgradeState):
            resp_head: ta.Optional[IoPipelineHttpResponseHead] = None
            if isinstance(msg, IoPipelineHttpResponseHead):
                resp_head = msg
            elif isinstance(msg, FullIoPipelineHttpResponse):
                resp_head = msg.head

            if resp_head is not None and not resp_head.is_interim and resp_head.status != 101:
                # Upgrade was rejected; resume HTTP decoding on any parked bytes after forwarding the response.
                buf = self._state.buf
                trailing = buf.split_to(len(buf)) if buf is not None and len(buf) else None
                self._state = self._HeadState(self)
                ctx.feed_out(msg)
                if trailing is not None:
                    out: ta.List[ta.Any] = []
                    self._decode(ctx, trailing, out)
                    for o in out:
                        ctx.feed_in(o)
                return

        ctx.feed_out(msg)


##


class IoPipelineHttpRequestAggregatorDecoder(
    IoPipelineHttpRequestObjects,
    IoPipelineHttpObjectAggregatorDecoder,
):
    _if_content_length_missing: ta.Final = 'empty'


##


class IoPipelineHttpRequestDechunker(IoPipelineHttpRequestObjects, IoPipelineHttpObjectDechunker):
    pass


##


class IoPipelineHttpRequestDecompressor(IoPipelineHttpRequestObjects, IoPipelineHttpObjectDecompressor):
    pass
