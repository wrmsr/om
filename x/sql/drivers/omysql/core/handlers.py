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
import functools
import math
import typing as ta
import weakref

from omcore import check
from omcore import dataclasses as dc
from omcore.io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.errors import IncompleteDecodingIoPipelineError
from omcore.io.pipelines.errors import TimeoutIoPipelineError
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.pipelines.sched.types import IoPipelineScheduling
from omcore.io.streambufs.types import ByteStreamBuffer
from omcore.io.streambufs.utils import ByteStreamBuffers

from ..constants import CR
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
        # Server packets that arrived with no operation waiting for them (an eager driver reading ahead of an unbuffered
        # result). They are replayed, in order, into the next operation.
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
        op = self._session.current
        self._session.fail(exc)
        if op is not None:
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
            exc = msg.exc
            if isinstance(exc, TimeoutIoPipelineError):
                new_exc = OperationalError(CR.CR_SERVER_LOST, f'Lost connection to MySQL server during query ({exc})')
                new_exc.__cause__ = exc
                exc = new_exc
            self._fail_current(ctx, exc)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._fail_current(ctx, InterfaceError(0, 'Lost connection to MySQL server during query'))
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)


class OperationTimeoutsIoPipelineHandler(IoPipelineHandler):
    """
    Enforces read and write deadlines while an operation is in flight.

    Placed on the transport side of the framing handler so its read activity is raw transport input; when a TLS handler
    is later added outermost, that activity becomes the decrypted stream, and a stalled TLS handshake is still caught
    because the deadline of whichever operation drove the handshake keeps running.

    The read deadline is armed while an operation is in flight and reset by each inbound chunk, so it times out a
    transport gone quiet mid-operation, not a slow-but-flowing response. Writes are covered by flush fences: each burst
    of outbound data is followed by a FlushOutput fence, which the transport driver completes once everything before it
    has crossed the transport, and a fence outstanding for longer than the write timeout fails the pipeline. With
    neither timeout configured the handler is a scheduler-independent, tickless pass-through.
    """

    def __init__(
            self,
            *,
            read_timeout_s: float | None = None,
            write_timeout_s: float | None = None,
    ) -> None:
        super().__init__()

        for timeout_s in (read_timeout_s, write_timeout_s):
            if timeout_s is not None and (not math.isfinite(timeout_s) or timeout_s <= 0.):
                raise ValueError(timeout_s)
        self._read_timeout_s = read_timeout_s
        self._write_timeout_s = write_timeout_s

        self._active = False
        self._timed_out = False
        self._read_handle: IoPipelineScheduling.Handle | None = None
        self._write_handle: IoPipelineScheduling.Handle | None = None
        self._write_dirty = False

    #

    def _cancel_read(self) -> None:
        if (handle := self._read_handle) is not None:
            self._read_handle = None
            handle.cancel()

    def _cancel_write(self) -> None:
        if (handle := self._write_handle) is not None:
            self._write_handle = None
            handle.cancel()
        self._write_dirty = False

    def _reset(self) -> None:
        self._active = False
        self._timed_out = False
        self._cancel_read()
        self._cancel_write()

    def _arm_read(self, ctx: IoPipelineHandlerContext) -> None:
        self._cancel_read()
        if self._read_timeout_s is None:
            return

        self._read_handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            self._read_timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, OperationTimeoutsIoPipelineHandler)._on_read_timeout(ctx2),  # noqa
        )

    def _on_read_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._read_handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Read timed out after {check.not_none(self._read_timeout_s):g} seconds'),
            direction='inbound',
            handler=ctx.ref,
        ))

    def _on_write_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._write_handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Write timed out after {check.not_none(self._write_timeout_s):g} seconds'),
            direction='outbound',
            handler=ctx.ref,
        ))

    @staticmethod
    def _on_fence_done(
            ctx_ref: ta.Callable[[], IoPipelineHandlerContext | None],
            _msg: IoPipelineMessages.Completable[None],
    ) -> None:
        if (ctx := ctx_ref()) is None or ctx.invalidated:
            return

        handler = check.isinstance(ctx.handler, OperationTimeoutsIoPipelineHandler)
        if (handle := handler._write_handle) is not None:  # noqa: SLF001
            handler._write_handle = None  # noqa: SLF001
            handle.cancel()

        # More output passed while this fence was pending; cover it with a fresh fence and deadline.
        if handler._write_dirty and handler._active and not handler._timed_out:  # noqa: SLF001
            handler._emit_write_fence(ctx)  # noqa: SLF001

    def _emit_write_fence(self, ctx: IoPipelineHandlerContext) -> None:
        self._write_dirty = False
        self._write_handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            check.not_none(self._write_timeout_s),
            lambda ctx2: check.isinstance(ctx2.handler, OperationTimeoutsIoPipelineHandler)._on_write_timeout(ctx2),  # noqa
        )
        fence = IoPipelineFlowMessages.FlushOutput()
        fence.add_listener(functools.partial(self._on_fence_done, weakref.ref(ctx)))
        ctx.feed_out(fence)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._read_timeout_s is not None or self._write_timeout_s is not None:
                check.not_none(ctx.services.find(IoPipelineScheduling))
            self._reset()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._reset()

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationRequest):
            self._active = True
            self._timed_out = False
            self._arm_read(ctx)

        elif isinstance(msg, (IoPipelineMessages.Error, IoPipelineMessages.FinalInput)):
            self._reset()

        elif self._active and not self._timed_out and ByteStreamBuffers.can_bytes(msg):
            self._arm_read(ctx)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationDone):
            self._reset()
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._reset()
            ctx.feed_out(msg)
            return

        ctx.feed_out(msg)

        if (
                self._write_timeout_s is not None and
                self._active and
                not self._timed_out and
                ByteStreamBuffers.can_bytes(msg)
        ):
            if self._write_handle is None:
                self._emit_write_fence(ctx)
            else:
                self._write_dirty = True


def make_pipeline_spec(
        session: ProtocolSession,
        *,
        read_timeout: float | None = None,
        write_timeout: float | None = None,
) -> IoPipeline.Spec:
    return IoPipeline.Spec([
        OperationTimeoutsIoPipelineHandler(
            read_timeout_s=read_timeout,
            write_timeout_s=write_timeout,
        ),
        MysqlFramingIoPipelineHandler(),
        MysqlSessionIoPipelineHandler(session),
    ])
