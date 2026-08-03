# @om-lite
import unittest

from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...handlers.fns import FnIoPipelineHandler
from ...handlers.queues import InboundQueueIoPipelineHandler
from ..queues import InboundBytesBufferingQueueIoPipelineHandler


class TestQueues(unittest.TestCase):
    def test_inbound_queue(self):
        ch = IoPipeline.new([
            FnIoPipelineHandler.of(inbound=lambda ctx, msg: ctx.feed_in(msg + b'!')),
            h := InboundBytesBufferingQueueIoPipelineHandler(),
        ])

        ch.feed_in(b'abc')
        assert not ch.output.poll()
        assert h.inbound_buffered_bytes() == 4
        assert h.drain() == [b'abc!']
        assert h.inbound_buffered_bytes() == 0

    def test_inbound_queue_filter(self):
        ch = IoPipeline.new([
            FnIoPipelineHandler.of(inbound=lambda ctx, msg: ctx.feed_in(msg + b'!' if isinstance(msg, bytes) else msg)),  # noqa
            h := InboundBytesBufferingQueueIoPipelineHandler(filter=True),
            ibq := InboundQueueIoPipelineHandler(),
        ], config=IoPipeline.Config.DEFAULT.update(raise_immediately=True))

        ch.feed_in(b'abc')
        assert not ch.output.poll()
        assert h.inbound_buffered_bytes() == 4
        assert h.drain() == [b'abc!']
        assert not ibq.poll()
        assert h.inbound_buffered_bytes() == 0

        ch.feed_in(420)
        assert h.inbound_buffered_bytes() == 0
        assert not h.poll()
        assert ibq.drain() == [420]
        assert h.inbound_buffered_bytes() == 0

    def test_default_does_not_trap_must_propagate(self):
        # The unfiltered default enqueues everything, so it must still forward the identity-tracked lifecycle
        # messages - swallowing them fails the pipeline's propagation check.

        ch = IoPipeline.new([
            h := InboundBytesBufferingQueueIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_initial_input()
        ch.feed_in(b'abc')
        ch.feed_final_input()

        assert [type(m) for m in ibq.drain()] == [
            IoPipelineMessages.InitialInput,
            IoPipelineMessages.FinalInput,
        ]
        assert [
            m if isinstance(m, bytes) else type(m)
            for m in h.drain()
        ] == [
            IoPipelineMessages.InitialInput,
            b'abc',
            IoPipelineMessages.FinalInput,
        ]
        assert h.inbound_buffered_bytes() == 0
