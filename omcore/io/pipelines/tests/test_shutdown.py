# ruff: noqa: UP006 UP045
# @om-lite
import dataclasses as dc
import gc
import typing as ta
import unittest
import weakref

from ...streambufs.utils import ByteStreamBuffers
from ..asyncs import AsyncIoPipelineMessages
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages
from ..errors import AbortedIoPipelineError
from ..errors import MessageNotPropagatedIoPipelineError
from ..errors import SawFinalOutputIoPipelineError
from ..errors import SawShutdownOutputIoPipelineError
from ..flow.types import IoPipelineFlowMessages


##


@dc.dataclass(frozen=True)
class _Emit:
    msgs: ta.Sequence[ta.Any]


@dc.dataclass(frozen=True)
class _Release:
    pass


@dc.dataclass(frozen=True, eq=False)
class _CompletableOutput(IoPipelineMessages.Completable[None]):
    pass


@dc.dataclass(frozen=True)
class _ControlOutput(IoPipelineMessages.AfterShutdownOutput):
    pass


class _AppHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

        self.inputs.append(msg)
        if isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)

    @property
    def errors(self) -> ta.List[IoPipelineMessages.Error]:
        return [m for m in self.inputs if isinstance(m, IoPipelineMessages.Error)]


class _RetainingOutboundHandler(IoPipelineHandler):
    """Buffers outbound bytes and retains ShutdownOutput until released, emitting the buffer before forwarding it."""

    def __init__(self) -> None:
        super().__init__()

        self._buf: ta.List[bytes] = []
        self._retained: ta.Optional[IoPipelineMessages.ShutdownOutput] = None

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.ShutdownOutput):
            ctx.mark_propagated('outbound', msg)
            self._retained = msg
            return

        if ByteStreamBuffers.can_bytes(msg):
            self._buf.append(bytes(ByteStreamBuffers.to_bytes(msg)))
            return

        ctx.feed_out(msg)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Release):
            if self._buf:
                ctx.feed_out(b''.join(self._buf))
                self._buf.clear()
            if (so := self._retained) is not None:
                self._retained = None
                ctx.feed_out(so)
            return

        ctx.feed_in(msg)


class _SwallowingOutboundHandler(IoPipelineHandler):
    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.ShutdownOutput):
            return

        ctx.feed_out(msg)


class _DeferringOutboundHandler(IoPipelineHandler):
    """Defers forwarding ShutdownOutput across a pinned deferred boundary."""

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.ShutdownOutput):
            # Pinning keeps the message pending across the deferred boundary instead of marking it propagated.
            ctx.defer(lambda ctx2: ctx2.feed_out(msg), pin=[msg])
            return

        ctx.feed_out(msg)


def _new(*handlers: IoPipelineHandler) -> ta.Tuple[IoPipeline, _AppHandler]:
    app = _AppHandler()
    return IoPipeline.new([*handlers, app]), app


class _Outcome:
    """Captures a completable's outcome, which is only observable from its listeners."""

    def __init__(self, msg: IoPipelineMessages.Completable) -> None:
        self.exc: ta.Optional[BaseException] = None
        self.done = False
        msg.add_listener(self._on_done)

    def _on_done(self, msg: IoPipelineMessages.Completable) -> None:
        self.done = True
        if msg.is_failed():
            self.exc = msg.get_exception()


##


class TestShutdownOutput(unittest.TestCase):
    def test_reaches_terminal_after_preceding_output(self) -> None:
        pipeline, _ = _new()
        so = IoPipelineMessages.ShutdownOutput()

        pipeline.feed_in(_Emit([b'a', b'b', so]))

        self.assertEqual(pipeline.output.drain(), [b'a', b'b', so])
        self.assertTrue(pipeline.saw_shutdown_output)
        self.assertFalse(pipeline.saw_final_output)
        self.assertFalse(so.is_done())
        self.assertTrue(pipeline.is_ready)

    def test_feed_shutdown_output_helper(self) -> None:
        sos: ta.List[IoPipelineMessages.ShutdownOutput] = []

        class Handler(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, _Release):
                    sos.append(ctx.feed_shutdown_output())
                    return
                ctx.feed_in(msg)

        pipeline = IoPipeline.new([Handler()], IoPipeline.Config(inbound_terminal='drop'))
        pipeline.feed_in(_Release())

        self.assertEqual(len(sos), 1)
        self.assertIsInstance(sos[0], IoPipelineMessages.ShutdownOutput)
        self.assertEqual(pipeline.output.drain(), sos)

    def test_ordinary_output_after_shutdown_is_rejected_as_inbound_error(self) -> None:
        pipeline, app = _new()

        pipeline.feed_in(_Emit([IoPipelineMessages.ShutdownOutput()]))
        pipeline.output.drain()

        pipeline.feed_in(_Emit([b'late', 'also late']))

        self.assertEqual(pipeline.output.drain(), [])
        self.assertEqual(len(app.errors), 2)
        for err in app.errors:
            self.assertIsInstance(err.exc, SawShutdownOutputIoPipelineError)
            self.assertEqual(err.direction, 'outbound')
        self.assertTrue(pipeline.is_ready)

    def test_completable_output_after_shutdown_fails(self) -> None:
        pipeline, app = _new()
        late = _CompletableOutput()
        late_outcome = _Outcome(late)

        pipeline.feed_in(_Emit([IoPipelineMessages.ShutdownOutput(), late]))

        self.assertTrue(late.is_failed())
        self.assertIsInstance(late_outcome.exc, SawShutdownOutputIoPipelineError)
        self.assertEqual(len(app.errors), 1)

    def test_second_shutdown_output_is_rejected(self) -> None:
        pipeline, app = _new()
        first = IoPipelineMessages.ShutdownOutput()
        second = IoPipelineMessages.ShutdownOutput()
        second_outcome = _Outcome(second)

        pipeline.feed_in(_Emit([first, second]))

        self.assertEqual(pipeline.output.drain(), [first])
        self.assertFalse(first.is_done())
        self.assertTrue(second.is_failed())
        self.assertIsInstance(second_outcome.exc, SawShutdownOutputIoPipelineError)
        self.assertEqual(len(app.errors), 1)

    def test_control_messages_remain_deliverable_after_shutdown(self) -> None:
        deferred: ta.List[IoPipelineMessages.Defer] = []

        class Handler(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, _Release):
                    deferred.append(ctx.defer(lambda _: None))
                    return
                ctx.feed_in(msg)

        pipeline, app = _new(Handler())
        so = IoPipelineMessages.ShutdownOutput()
        rfi = IoPipelineFlowMessages.ReadyForInput()
        flush = IoPipelineFlowMessages.FlushOutput()
        awt: AsyncIoPipelineMessages.Await[None] = AsyncIoPipelineMessages.Await(None)  # type: ignore[arg-type]
        ctl = _ControlOutput()

        pipeline.feed_in(_Emit([so, rfi, flush, awt, ctl]))
        pipeline.feed_in(_Release())

        self.assertEqual(pipeline.output.drain(), [so, rfi, flush, awt, ctl, deferred[0]])
        self.assertEqual(app.errors, [])

    def test_final_output_after_shutdown_and_nothing_after_final_output(self) -> None:
        pipeline, app = _new()
        so = IoPipelineMessages.ShutdownOutput()
        fo = IoPipelineMessages.FinalOutput()
        late_flush = IoPipelineFlowMessages.FlushOutput()
        late_flush_outcome = _Outcome(late_flush)

        pipeline.feed_in(_Emit([so, fo]))
        self.assertEqual(pipeline.output.drain(), [so, fo])
        self.assertTrue(pipeline.saw_final_output)

        pipeline.feed_in(_Emit([late_flush]))
        self.assertEqual(pipeline.output.drain(), [])
        self.assertTrue(late_flush.is_failed())
        self.assertIsInstance(late_flush_outcome.exc, SawFinalOutputIoPipelineError)
        self.assertEqual(len(app.errors), 1)

    def test_shutdown_after_final_output_is_rejected(self) -> None:
        pipeline, _ = _new()
        so = IoPipelineMessages.ShutdownOutput()
        so_outcome = _Outcome(so)

        pipeline.feed_in(_Emit([IoPipelineMessages.FinalOutput(), so]))

        self.assertTrue(so.is_failed())
        self.assertIsInstance(so_outcome.exc, SawFinalOutputIoPipelineError)
        self.assertFalse(pipeline.saw_shutdown_output)

    def test_input_continues_after_shutdown(self) -> None:
        pipeline, app = _new()

        pipeline.feed_in(IoPipelineMessages.InitialInput())
        pipeline.feed_in(_Emit([IoPipelineMessages.ShutdownOutput()]))
        pipeline.feed_in('after', 'shutdown')
        pipeline.feed_in(IoPipelineMessages.FinalInput())

        self.assertEqual(app.inputs[1:3], ['after', 'shutdown'])
        self.assertIsInstance(app.inputs[0], IoPipelineMessages.InitialInput)
        self.assertIsInstance(app.inputs[3], IoPipelineMessages.FinalInput)
        self.assertTrue(pipeline.saw_final_input)
        self.assertTrue(pipeline.saw_shutdown_output)
        self.assertTrue(pipeline.is_ready)

    def test_shutdown_output_is_never_inbound(self) -> None:
        pipeline, _ = _new()

        with self.assertRaises(TypeError):
            pipeline.feed_in(IoPipelineMessages.ShutdownOutput())

    def test_dropping_shutdown_output_is_a_propagation_error(self) -> None:
        pipeline, _ = _new(_SwallowingOutboundHandler())

        with self.assertRaises(MessageNotPropagatedIoPipelineError):
            pipeline.feed_in(_Emit([IoPipelineMessages.ShutdownOutput()]))

        self.assertFalse(pipeline.saw_shutdown_output)

    def test_retained_shutdown_follows_buffered_output(self) -> None:
        pipeline, _ = _new(_RetainingOutboundHandler())
        so = IoPipelineMessages.ShutdownOutput()

        pipeline.feed_in(_Emit([b'one', b'two', so]))
        self.assertEqual(pipeline.output.drain(), [])
        self.assertFalse(pipeline.saw_shutdown_output)

        pipeline.feed_in(_Release())
        self.assertEqual(pipeline.output.drain(), [b'onetwo', so])
        self.assertTrue(pipeline.saw_shutdown_output)

    def test_shutdown_pinned_across_defer(self) -> None:
        pipeline, _ = _new(_DeferringOutboundHandler())
        so = IoPipelineMessages.ShutdownOutput()

        pipeline.feed_in(_Emit([b'x', so]))
        out = pipeline.output.drain()
        self.assertEqual(out[0], b'x')
        dfl = out[1]
        self.assertIsInstance(dfl, IoPipelineMessages.Defer)
        self.assertFalse(pipeline.saw_shutdown_output)

        pipeline.run_deferred(dfl)
        self.assertEqual(pipeline.output.drain(), [so])
        self.assertTrue(pipeline.saw_shutdown_output)

    def test_destroy_fails_pending_shutdown_output(self) -> None:
        pipeline, _ = _new()
        so = IoPipelineMessages.ShutdownOutput()
        excs: ta.List[ta.Optional[BaseException]] = []
        so.add_listener(lambda m: excs.append(m.get_exception()))

        pipeline.feed_in(_Emit([so]))
        pipeline.destroy()

        self.assertTrue(so.is_failed())
        self.assertEqual(len(excs), 1)
        self.assertIsInstance(excs[0], AbortedIoPipelineError)

    def test_completed_shutdown_releases_pipeline_without_cyclic_gc(self) -> None:
        def run() -> ta.Tuple[weakref.ReferenceType, weakref.ReferenceType]:
            pipeline, _ = _new(_RetainingOutboundHandler())
            so = IoPipelineMessages.ShutdownOutput()
            pipeline.feed_in(_Emit([b'x', so]))
            pipeline.feed_in(_Release())
            pipeline.output.drain()
            with pipeline.enter():
                so.set_succeeded(None)
            return weakref.ref(pipeline), weakref.ref(so)

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            pipeline_ref, so_ref = run()
            self.assertIsNone(pipeline_ref())
            self.assertIsNone(so_ref())
        finally:
            if was_enabled:
                gc.enable()
