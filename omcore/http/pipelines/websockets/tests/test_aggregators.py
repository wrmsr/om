# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ..aggregators import IoPipelineWebsocketAggregator
from ..objects import IoPipelineWebsocketBinary
from ..objects import IoPipelineWebsocketFrame
from ..objects import IoPipelineWebsocketOpcode
from ..objects import IoPipelineWebsocketText


def _new():
    pipeline = IoPipeline.new([
        IoPipelineWebsocketAggregator(),
        ibq := InboundQueueIoPipelineHandler(),
    ])
    return pipeline, ibq


def _frame(opcode, payload, *, fin):
    return IoPipelineWebsocketFrame(fin=fin, opcode=opcode, payload=payload)


class TestAggregator(unittest.TestCase):
    def test_fragmented_message(self) -> None:
        pipeline, ibq = _new()

        pipeline.feed_in(
            _frame(IoPipelineWebsocketOpcode.TEXT, b'Hel', fin=False),
            _frame(IoPipelineWebsocketOpcode.CONTINUATION, b'l', fin=False),
            _frame(IoPipelineWebsocketOpcode.CONTINUATION, b'o', fin=True),
        )

        assert ibq.drain() == [IoPipelineWebsocketText('Hello')]

    def test_interleaved_data_frame_is_an_error(self) -> None:
        # RFC 6455 §5.4 forbids a new data frame while a fragmented message is in flight.
        pipeline, ibq = _new()

        pipeline.feed_in(_frame(IoPipelineWebsocketOpcode.TEXT, b'Hel', fin=False))
        assert ibq.drain() == []

        pipeline.feed_in(_frame(IoPipelineWebsocketOpcode.TEXT, b'other', fin=True))
        [err] = ibq.drain()
        assert isinstance(err, IoPipelineMessages.Error)
        assert isinstance(err.exc, ValueError)

        # The abandoned partial must not linger - a later continuation must not be appended to it and emitted as a
        # franken-message.
        pipeline.feed_in(_frame(IoPipelineWebsocketOpcode.CONTINUATION, b'lo', fin=True))
        [err2] = ibq.drain()
        assert isinstance(err2, IoPipelineMessages.Error)
        assert isinstance(err2.exc, ValueError)

    def test_interleaved_non_fin_data_frame_is_an_error(self) -> None:
        pipeline, ibq = _new()

        pipeline.feed_in(
            _frame(IoPipelineWebsocketOpcode.TEXT, b'Hel', fin=False),
            _frame(IoPipelineWebsocketOpcode.BINARY, b'xyz', fin=False),
        )

        [err] = ibq.drain()
        assert isinstance(err, IoPipelineMessages.Error)
        assert isinstance(err.exc, ValueError)

    def test_unexpected_continuation_is_an_error(self) -> None:
        pipeline, ibq = _new()

        pipeline.feed_in(_frame(IoPipelineWebsocketOpcode.CONTINUATION, b'lo', fin=True))

        [err] = ibq.drain()
        assert isinstance(err, IoPipelineMessages.Error)
        assert isinstance(err.exc, ValueError)

    def test_control_frame_during_fragmented_message(self) -> None:
        # Control frames may be interleaved - only data frames may not.
        pipeline, ibq = _new()

        pipeline.feed_in(
            _frame(IoPipelineWebsocketOpcode.TEXT, b'ab', fin=False),
            _frame(IoPipelineWebsocketOpcode.PING, b'', fin=True),
            _frame(IoPipelineWebsocketOpcode.CONTINUATION, b'cd', fin=True),
        )

        [ping, msg] = ibq.drain()
        assert msg == IoPipelineWebsocketText('abcd')
        assert not isinstance(ping, IoPipelineWebsocketText)

    def test_unfragmented_binary(self) -> None:
        pipeline, ibq = _new()

        pipeline.feed_in(_frame(IoPipelineWebsocketOpcode.BINARY, b'xy', fin=True))

        assert ibq.drain() == [IoPipelineWebsocketBinary(b'xy')]
