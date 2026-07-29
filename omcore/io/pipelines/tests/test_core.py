# @om-lite
import dataclasses as dc
import gc
import typing as ta
import unittest
import weakref

from ....lite.check import check
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages
from ..core import IoPipelineMetadata
from ..errors import AbortedIoPipelineError
from ..errors import ContextInvalidatedIoPipelineError
from ..errors import MessageNotPropagatedIoPipelineError
from ..handlers.feedback import FeedbackInboundIoPipelineHandler
from ..handlers.queues import InboundQueueIoPipelineHandler


class IntIncInboundHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, int):
            msg += 1

        ctx.feed_in(msg)


class IntMulThreeInboundHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, int):
            msg *= 3

        ctx.feed_in(msg)


class IntStrDuplexHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, int):
            msg = str(msg)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, str):
            msg = int(msg)

        ctx.feed_out(msg)


class DuplicateInboundHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_in(msg)
        ctx.feed_in(msg)


class ReplaceSelfInboundHandler(IoPipelineHandler):
    def __init__(self, fn):
        self.fn = fn

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        h = self.fn()
        hr = ctx.pipeline.replace(ctx.ref, h)
        ctx.pipeline.feed_in_to(hr, msg)


class TestReferenceOwnership(unittest.TestCase):
    def test_pipeline_topology_does_not_require_cyclic_gc(self) -> None:
        def make_refs():
            first = IntIncInboundHandler()
            second = IntStrDuplexHandler()
            pipeline = IoPipeline.new([first, second])

            # Populate every handler lookup cache; these are part of the long-lived pipeline topology too.
            pipeline.handlers()
            pipeline.handlers_by_name()
            pipeline.find_handlers_of_type(IoPipelineHandler)
            pipeline.find_single_handler_of_type(IntIncInboundHandler)

            handler_ref = check.not_none(pipeline.find_handler(first))
            return (
                weakref.ref(pipeline),
                weakref.ref(first),
                weakref.ref(second),
                weakref.ref(handler_ref._context),  # noqa
                weakref.ref(handler_ref),
            )

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = make_refs()
            self.assertTrue(all(ref() is None for ref in refs))
        finally:
            if was_enabled:
                gc.enable()

    def test_handler_ref_keeps_pipeline_alive_without_a_cycle(self) -> None:
        was_enabled = gc.isenabled()
        gc.disable()
        try:
            pipeline = IoPipeline.new([IntIncInboundHandler()])
            pipeline_ref = weakref.ref(pipeline)
            handler_ref = pipeline.handlers()[0]

            del pipeline
            self.assertIs(handler_ref.pipeline, pipeline_ref())

            del handler_ref
            self.assertIsNone(pipeline_ref())
        finally:
            if was_enabled:
                gc.enable()


class TestCore(unittest.TestCase):
    def test_core(self):
        ch = IoPipeline.new([
            IntIncInboundHandler(),
            IntStrDuplexHandler(),
            fbi := FeedbackInboundIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in('hi')
        assert ibq.drain() == ['hi']

        ch.feed_in(42)
        assert ibq.drain() == ['43']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]

        #

        ch.add_outer_to(
            ch.handlers()[0],
            IntMulThreeInboundHandler(),
        )

        ch.feed_in(42)
        assert ibq.drain() == ['127']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]

        #

        rem = ch.handlers()[1]
        ch.remove(ch.handlers()[1])

        with ch.enter():
            with self.assertRaises(ContextInvalidatedIoPipelineError):
                rem._context._inbound('hi')  # noqa

        #

        ch.feed_in(42)
        assert ibq.drain() == ['126']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]

        #

        ch.replace(ch.handlers()[0], IntIncInboundHandler())

        ch.feed_in('hi')
        assert ibq.drain() == ['hi']

        ch.feed_in(42)
        assert ibq.drain() == ['43']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]

    def test_replace_self(self):
        ch = IoPipeline.new([
            DuplicateInboundHandler(),
            ReplaceSelfInboundHandler(IntIncInboundHandler),
            IntStrDuplexHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(42)
        assert ibq.drain() == ['43', '43']

    def test_named(self):
        ch = IoPipeline.new([
            fbi := FeedbackInboundIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.add_outermost(IntStrDuplexHandler(), name='int_str')
        ch.add_outermost(IntIncInboundHandler(), name='int_inc')

        ch.feed_in(42)
        assert ibq.drain() == ['43']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]

        ch.remove(ch.handlers_by_name()['int_inc'])

        ch.feed_in(42)
        assert ibq.drain() == ['42']

        ch.feed_in(fbi.wrap('24'))
        assert ch.output.drain() == [24]


class TestMetadata(unittest.TestCase):
    @dc.dataclass(frozen=True)
    class FooMetadata(IoPipelineMetadata):
        foo: str

    @dc.dataclass(frozen=True)
    class BarMetadata(IoPipelineMetadata):
        bar: str

    def test_metadata(self):
        ch = IoPipeline.new(metadata=[TestMetadata.FooMetadata('foo')])
        assert ch.metadata[TestMetadata.FooMetadata] == TestMetadata.FooMetadata('foo')
        assert TestMetadata.FooMetadata in ch.metadata
        with self.assertRaises(KeyError):  # noqa
            ch.metadata[TestMetadata.BarMetadata]  # noqa
        assert TestMetadata.BarMetadata not in ch.metadata


class TestCompletable(unittest.TestCase):
    @dc.dataclass(frozen=True)
    class CompletableFoo(IoPipelineMessages.Completable[str]):
        i: int

    def test_completable_no_listeners(self):
        cf = TestCompletable.CompletableFoo(420)
        assert cf.i == 420

        assert not cf.is_done()
        cf.set_succeeded('hiya')
        assert cf.is_done()
        assert not hasattr(cf, '_completion_')

    def test_completable_listeners(self):
        cf = TestCompletable.CompletableFoo(420)
        assert cf.i == 420

        l: list = []

        @cf.add_listener
        def my_listener(o):
            l.append(o.get_result())

        assert not cf.is_done()
        cf.set_succeeded('hiya')

        assert cf.is_done()

        assert l == ['hiya']

    def test_listener_failure_does_not_retain_completion_state(self):
        cf = TestCompletable.CompletableFoo(420)
        events = []

        def fail_listener(o):
            events.append(('fail', o.get_result()))
            raise RuntimeError('listener')

        cf.add_listener(fail_listener)
        cf.add_listener(lambda o: events.append(('later', o.get_result())))

        with self.assertRaisesRegex(RuntimeError, 'listener'):
            cf.set_succeeded('hiya')

        self.assertTrue(cf.is_succeeded())
        self.assertFalse(hasattr(cf, '_completion_'))
        self.assertEqual(events, [('fail', 'hiya'), ('later', 'hiya')])

    def test_pipeline_destroy_fails_pending_completable(self):
        ch = IoPipeline.new([
            fbi := FeedbackInboundIoPipelineHandler(),
        ])
        cf = TestCompletable.CompletableFoo(420)
        failures = []
        cf.add_listener(lambda o: failures.append(o.get_exception()))

        ch.feed_in(fbi.wrap(cf))
        self.assertFalse(cf.is_done())

        ch.destroy()

        self.assertTrue(cf.is_failed())
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], AbortedIoPipelineError)


class TestMustPropagate(unittest.TestCase):
    def test_must_propagate(self):
        class BrokenPropagator(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineMessages.FinalInput):
                    return

                ctx.feed_in(msg)

        ch = IoPipeline.new([
            IntStrDuplexHandler(),
            bph := BrokenPropagator(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(240)
        assert not ch.output.drain()
        assert ibq.drain() == ['240']

        fi = IoPipelineMessages.FinalInput()
        with self.assertRaises(MessageNotPropagatedIoPipelineError) as ex:
            ch.feed_in(fi)
        assert isinstance(ex.exception, MessageNotPropagatedIoPipelineError)
        it = ex.exception.items[0]
        assert it.direction == 'inbound'
        assert it.msg is fi
        assert check.not_none(it.last_seen).handler is bph


class TestDefer(unittest.TestCase):
    def test_defer(self):
        class DeferThing(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if msg == 'hi':
                    ctx.defer_no_context(lambda: ctx.feed_in('bye'))
                    return

                ctx.feed_in(msg)

        ch = IoPipeline.new([
            IntStrDuplexHandler(),
            DeferThing(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(240)
        assert not ch.output.drain()
        assert ibq.drain() == ['240']

        ch.feed_in('hi')
        assert not ibq.drain()
        [dfl] = ch.output.drain()
        assert isinstance(dfl, IoPipelineMessages.Defer)

        ch.run_deferred(dfl)
        assert not ch.output.drain()
        assert ibq.drain() == ['bye']

    def test_defer_pinning(self):
        class PinningDeferThing(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineMessages.FinalInput):
                    def foo():
                        ctx.feed_in(msg)

                    ctx.defer_no_context(foo, pin=[msg])
                    return

                ctx.feed_in(msg)

        ch = IoPipeline.new([
            IntStrDuplexHandler(),
            PinningDeferThing(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(240)
        assert not ch.output.drain()
        assert ibq.drain() == ['240']

        fi = IoPipelineMessages.FinalInput()
        ch.feed_in(fi)
        assert not ibq.drain()
        [dfl] = ch.output.drain()
        assert isinstance(dfl, IoPipelineMessages.Defer)

        ch.run_deferred(dfl)
        assert not ch.output.drain()
        assert ibq.drain() == [fi]
