"""
JsonrpcFrame <-> Request / Response / Batch / InvalidMessage.

Decoding never raises: malformed input becomes an InvalidMessage for the session to answer or reject by policy. Encoding
never raises either: a payload which cannot be encoded, or which encodes larger than the frame limit, is dropped and
reported inward as an OutboundEncodeFailed so the session can fail just that message rather than the connection.
"""
import typing as ta

from ....io.pipelines import all as ipl
from ..errors import JsonrpcMessageTooLargeError
from ..parsing import ParseOptions
from ..parsing import dumps_payload
from ..parsing import loads_payload
from ..types import Batch
from ..types import InvalidMessage
from ..types import Request
from ..types import Response
from .framing import JsonrpcFrame
from .messages import JsonrpcPipelineMessages as Jpm


##


class JsonrpcCodecHandler(ipl.Handler):
    def __init__(
            self,
            *,
            max_frame_bytes: int,
            parse_options: ParseOptions = ParseOptions.DEFAULT,
    ) -> None:
        super().__init__()

        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        self._max_frame_bytes = max_frame_bytes
        self._parse_options = parse_options

    def inbound(self, ctx: ipl.HandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, JsonrpcFrame):
            msg = loads_payload(msg.data, self._parse_options)

        ctx.feed_in(msg)

    def outbound(self, ctx: ipl.HandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (Request, Response, Batch, InvalidMessage)):
            try:
                data = dumps_payload(msg).encode('utf-8')
            except (TypeError, ValueError) as e:
                ctx.feed_in(Jpm.OutboundEncodeFailed(msg, e))
                return

            if len(data) > self._max_frame_bytes:
                ctx.feed_in(Jpm.OutboundEncodeFailed(msg, JsonrpcMessageTooLargeError(
                    f'outbound message is {len(data)} bytes, exceeding limit {self._max_frame_bytes}',
                )))
                return

            msg = JsonrpcFrame(data)

        ctx.feed_out(msg)
