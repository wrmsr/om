# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
The MySQL protocol as omcore.io.pipelines handlers: a packet framer (sequence ids, 16MB splitting and reassembly) and a
session handler which drives ProtocolSession operations. These are synchronous and transport-agnostic; sync and async
connections differ only in the pipeline driver they are attached to.
"""
import collections
import typing as ta

from omcore import dataclasses as dc
from omcore.io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.errors import IncompleteDecodingIoPipelineError
from omcore.io.streambufs.types import ByteStreamBuffer

from ..errors import InterfaceError
from ..errors import OperationalError
from ..protocol.packets import HEADER_SIZE
from ..protocol.packets import MAX_PACKET_LENGTH
from ..protocol.packets import pack_packet
from ..protocol.packets import split_payload
from ..protocol.packets import unpack_header
from ..protocol.session import Operation
from ..protocol.session import OutPacket
from ..protocol.session import ProtocolSession
from ..protocol.session import Step


##


@dc.dataclass(frozen=True)
class ServerPacket:
    """A fully reassembled server packet payload, fed inbound to the session handler."""

    payload: bytes


@dc.dataclass(frozen=True)
class OperationRequest:
    op: Operation


@dc.dataclass(frozen=True)
class OperationDone:
    op: Operation


##


class MysqlFramingIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """
    Owns the packet sequence number for both directions: inbound it deframes and reassembles server packets (validating
    sequence ids), outbound it frames OutPackets, resetting the sequence to zero at the start of each command.
    """

    def __init__(self, *, max_buffer_size: int | None = None) -> None:
        super().__init__(max_buffer_size=max_buffer_size)

        self._seq = 0
        self._pending = bytearray()

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OutPacket):
            if msg.starts_command:
                self._seq = 0
            for chunk in split_payload(msg.payload):
                ctx.feed_out(pack_packet(self._seq, chunk))
                self._seq = (self._seq + 1) % 256
            return

        ctx.feed_out(msg)

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while len(buf) >= HEADER_SIZE:
            length, seq = unpack_header(buf.coalesce(HEADER_SIZE))
            if len(buf) < HEADER_SIZE + length:
                break

            if seq != self._seq:
                if seq == 0:
                    # The server reset the sequence, which happens when it drops the connection (e.g. wait_timeout).
                    raise OperationalError(2013, 'Lost connection to MySQL server during query')
                raise InterfaceError(f'Packet sequence number wrong - got {seq} expected {self._seq}')
            self._seq = (self._seq + 1) % 256

            buf.advance(HEADER_SIZE)
            self._pending += buf.split_to(length).tobytes() if length else b''

            # A packet whose payload fills the maximum is continued by the next packet.
            if length < MAX_PACKET_LENGTH:
                out.append(ServerPacket(bytes(self._pending)))
                self._pending = bytearray()

        if final and (len(buf) or self._pending):
            raise IncompleteDecodingIoPipelineError('incomplete MySQL packet at end of input')


class MysqlSessionIoPipelineHandler(IoPipelineHandler):
    def __init__(self, session: ProtocolSession) -> None:
        super().__init__()

        self._session = session
        # Server packets that arrived with no operation waiting for them (an eager driver reading ahead of an
        # unbuffered result). They are replayed, in order, into the next operation.
        self._pending: collections.deque[bytes] = collections.deque()

    def _emit(self, ctx: IoPipelineHandlerContext, step: Step) -> None:
        while True:
            for packet in step.packets:
                ctx.feed_out(packet)
            if step.more:
                step = self._session.resume()
            else:
                break

    def _fail_current(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        if (op := self._session.current) is not None:
            self._session.fail(exc)
            ctx.feed_out(OperationDone(op))

    def _feed(self, ctx: IoPipelineHandlerContext, payload: bytes) -> None:
        cur = self._session.current
        try:
            step = self._session.handle(payload)
        except Exception as e:
            self._fail_current(ctx, e)
            raise
        self._emit(ctx, step)
        if cur is not None and cur.done:
            ctx.feed_out(OperationDone(cur))

    def _drain_pending(self, ctx: IoPipelineHandlerContext) -> None:
        while self._session.current is not None and self._pending:
            self._feed(ctx, self._pending.popleft())

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationRequest):
            op = msg.op
            self._emit(ctx, op.start())
            if op.done:
                ctx.feed_out(OperationDone(op))
            self._drain_pending(ctx)
            return

        if isinstance(msg, ServerPacket):
            self._pending.append(msg.payload)
            self._drain_pending(ctx)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self._fail_current(ctx, msg.exc)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._fail_current(ctx, InterfaceError(0, 'Lost connection to MySQL server during query'))
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)

def make_pipeline_spec(session: ProtocolSession) -> IoPipeline.Spec:
    return IoPipeline.Spec([
        MysqlFramingIoPipelineHandler(),
        MysqlSessionIoPipelineHandler(session),
    ])
