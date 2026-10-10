# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import gc
import typing as ta
import unittest
import weakref

from ...asyncs import AsyncIoPipelineMessages
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...sched.types import IoPipelineScheduling
from ..types import ConnectionClosedMultiplexIoPipelineError
from ..types import IoPipelineMultiplexMessages
from ..types import IoPipelineMultiplexOpenedStream
from ..types import UnclaimedOutputMultiplexIoPipelineError
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .loopback import LData
from .loopback import LEnd
from .loopback import LGoodbye
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LReset
from .loopback import Outcome
from .loopback import data_of
from .loopback import of_type


##


def _keep_open(**kwargs: ta.Any) -> StreamApp:
    return StreamApp(close_on_final_input=False, **kwargs)


class _Fail(IoPipelineMessages.AfterFinalInput):
    pass


class _FailingHandler(IoPipelineHandler):
    """Raises when told to; outer to the app, so its errors reach the app as inbound Errors."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Fail):
            raise RuntimeError('handler failed')  # noqa: TRY004
        ctx.feed_in(msg)


class TestChildErrors(unittest.TestCase):
    def test_handled_child_error_stays_in_the_child(self) -> None:
        app = _keep_open()

        def factory(o: ta.Any) -> IoPipeline.Spec:
            return IoPipeline.Spec([_FailingHandler(), app], services=[StubIoPipelineFlowService()])

        h = LoopbackHarness(factory)
        try:
            h.feed(LOpen('k'), LOpen('other'))
            h.feed_stream('k', _Fail())
            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], RuntimeError)

            # The stream - and the connection - carry on.
            h.feed(LData('k', b'still here'))
            self.assertEqual(bytes(app.received), b'still here')
            self.assertEqual(of_type(h.frames, LReset), [])
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()

    def test_unhandled_child_error_resets_only_that_stream(self) -> None:
        def factory(o: ta.Any) -> IoPipeline.Spec:
            # No app consumes Errors here: one reaching the child's end is fatal to the child.
            return IoPipeline.Spec([_FailingHandler()])

        survivor = _keep_open()
        apps = {'other': survivor}
        h = LoopbackHarness(lambda o: factory(o) if o.key == 'k' else app_spec(apps[ta.cast(str, o.key)]))
        try:
            h.feed(LOpen('k'), LOpen('other'))
            h.feed_stream('k', _Fail())

            (reset,) = of_type(h.frames, LReset)
            self.assertEqual(reset.key, 'k')
            self.assertNotIn('k', h.mux.streams)
            self.assertEqual(h.mux.streams.stats.reset_local, 1)

            h.feed(LData('other', b'fine'))
            self.assertEqual(bytes(survivor.received), b'fine')
            self.assertTrue(h.pipeline.is_ready)
            self.assertEqual(of_type(h.frames, LGoodbye), [])
        finally:
            h.close()

    def test_unclaimed_output_is_an_error_in_the_child(self) -> None:
        class _Unclaimed(IoPipelineMessages.Completable[None]):
            pass

        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(claim=lambda m: not isinstance(m, _Unclaimed)),
        )
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            msg = _Unclaimed()
            failures: ta.List[ta.Any] = []
            msg.add_listener(lambda m: failures.append(m.get_exception()))
            h.feed_stream('k', Emit(msg, b'after'))

            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], UnclaimedOutputMultiplexIoPipelineError)
            self.assertIsInstance(failures[0], UnclaimedOutputMultiplexIoPipelineError)
            self.assertEqual(data_of(h.frames, 'k'), b'after')
        finally:
            h.close()


class TestTeardown(unittest.TestCase):
    def _setup(self) -> ta.Tuple[LoopbackHarness, StreamApp, Outcome, IoPipelineMessages.ShutdownOutput]:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        h.feed(LOpen('k', credit=0))
        app = h.app('k')
        so = IoPipelineMessages.ShutdownOutput()
        h.feed_stream('k', Emit(b'blocked', so))
        opening = h.open(app_spec(_keep_open()))
        return h, app, opening, so

    def test_parent_destroy_aborts_streams(self) -> None:
        h, app, opening, so = self._setup()
        try:
            child = h.mux.child_pipeline('k')
            assert child is not None
            h.pipeline.destroy()

            self.assertFalse(child.is_ready)
            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], ConnectionClosedMultiplexIoPipelineError)
            self.assertTrue(so.is_failed())
            self.assertIsInstance(opening.exc, AbortedIoPipelineError)
        finally:
            h.close()

    def test_removing_the_multiplexer_aborts_streams(self) -> None:
        h, app, opening, so = self._setup()
        try:
            child = h.mux.child_pipeline('k')
            assert child is not None
            with h.pipeline.enter():
                h.pipeline.remove(h.pipeline.handlers()[-1])

            self.assertFalse(child.is_ready)
            self.assertIsInstance(app.errors[0], ConnectionClosedMultiplexIoPipelineError)
            self.assertTrue(so.is_failed())
            self.assertIsInstance(opening.exc, ConnectionClosedMultiplexIoPipelineError)
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()

    def test_inbound_error_fails_the_connection(self) -> None:
        h, app, opening, so = self._setup()
        try:
            h.enqueue(IoPipelineMessages.Error(RuntimeError('transport-side failure')))

            (bye,) = of_type(h.frames, LGoodbye)
            self.assertIsInstance(bye.exc, RuntimeError)
            self.assertIsInstance(app.errors[0], ConnectionClosedMultiplexIoPipelineError)
            self.assertIsInstance(app.errors[0].__cause__, RuntimeError)
            self.assertIsInstance(opening.exc, ConnectionClosedMultiplexIoPipelineError)
            self.assertTrue(h.pipeline.saw_final_output)
            self.assertEqual(len(h.mux.streams), 0)
        finally:
            h.close()


class _TimerApp(StreamApp):
    def __init__(self, delay_s: float) -> None:
        super().__init__(close_on_final_input=False)

        self._delay_s = delay_s
        self.handle: ta.Optional[IoPipelineScheduling.Handle] = None

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self.handle = ctx.services[IoPipelineScheduling].schedule_context(
                ctx.ref,
                self._delay_s,
                lambda ctx2: ctx2.feed_out(b'tick'),
            )
        super().inbound(ctx, msg)


class TestChildScheduling(unittest.TestCase):
    def test_child_timer_runs_through_the_parent_scheduler(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _TimerApp(5.)))
        try:
            h.feed(LOpen('k'))
            self.assertEqual(h.driver.next_deadline(), 5.)
            h.driver.advance_time(5.)
            h.step()
            self.assertEqual(data_of(h.frames, 'k'), b'tick')
            self.assertIsNone(h.driver.next_deadline())
        finally:
            h.close()

    def test_stream_close_cancels_child_timers(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _TimerApp(5.)))
        try:
            h.feed(LOpen('k'), LOpen('j'))
            self.assertEqual(len(h.driver._sched._live), 2)
            h.feed(LReset('k'))
            self.assertEqual(len(h.driver._sched._live), 1)
            h.driver.advance_time(5.)
            h.step()
            self.assertEqual(data_of(h.frames, 'k'), b'')
            self.assertEqual(data_of(h.frames, 'j'), b'tick')
        finally:
            h.close()

    def test_child_handler_removal_cancels_its_timers(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _TimerApp(5.)))
        try:
            h.feed(LOpen('k'))
            child = h.mux.child_pipeline('k')
            assert child is not None
            with h.pipeline.enter():
                with child.enter():
                    child.remove(child.handlers()[0])
            self.assertEqual(len(h.driver._sched._live), 0)
        finally:
            h.close()

    def test_failing_child_timer_resets_its_stream(self) -> None:
        class Boom(StreamApp):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineMessages.InitialInput):
                    ctx.services[IoPipelineScheduling].schedule(ctx.ref, 1., self._boom)
                super().inbound(ctx, msg)

            def _boom(self) -> None:
                raise RuntimeError('timer failed')

        h = LoopbackHarness(AppFactory(lambda o: Boom(close_on_final_input=False)))
        try:
            h.feed(LOpen('k'))
            h.driver.advance_time(1.)
            h.step()
            (reset,) = of_type(h.frames, LReset)
            self.assertIsInstance(reset.reason, RuntimeError)
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()

    def test_no_child_scheduling_without_parent_scheduling(self) -> None:
        seen: ta.List[ta.Any] = []

        class Probe(StreamApp):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineMessages.InitialInput):
                    seen.append(ctx.services.find(IoPipelineScheduling))
                super().inbound(ctx, msg)

        h = LoopbackHarness(AppFactory(lambda o: Probe(close_on_final_input=False)))
        try:
            # The pure driver installs a scheduler, so the child gets one...
            h.feed(LOpen('k'))
            self.assertIsNotNone(seen[0])
        finally:
            h.close()

        # ...while a parent pipeline without one gives the child none.
        mux_spec = LoopbackHarness(AppFactory(lambda o: Probe(close_on_final_input=False))).mux
        parent = IoPipeline.new([mux_spec])
        try:
            parent.feed_initial_input()
            parent.feed_in(LOpen('k'))
            self.assertIsNone(seen[1])
        finally:
            parent.destroy()


class _AwaitApp(StreamApp):
    def __init__(self) -> None:
        super().__init__(close_on_final_input=False)

        self.awt: ta.Optional[AsyncIoPipelineMessages.Await] = None
        self.result: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            obj: ta.Any = 'awaitable'
            awt: AsyncIoPipelineMessages.Await[ta.Any] = AsyncIoPipelineMessages.Await(obj)
            self.awt = awt
            awt.add_listener(lambda m: self.result.append(m.get_result() if m.is_succeeded() else m.get_exception()))
            ctx.feed_out(awt)
        super().inbound(ctx, msg)


class TestAwaitForwarding(unittest.TestCase):
    def test_child_await_is_forwarded_and_completed_inside_the_child(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _AwaitApp()))
        try:
            frames = h.feed(LOpen('k'))
            # The pure driver cannot await: it hands the parent Await to its caller, as it would a top-level one.
            (pawt,) = [f for f in frames if isinstance(f, AsyncIoPipelineMessages.Await)]
            self.assertEqual(pawt.obj, 'awaitable')
            app = h.app('k')
            self.assertEqual(app.result, [])

            with h.pipeline.enter():
                pawt.set_succeeded(42)
            h.step()
            self.assertEqual(app.result, [42])
        finally:
            h.close()

    def test_child_await_fails_with_the_connection(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _AwaitApp()))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            h.pipeline.destroy()
            self.assertEqual(len(app.result), 1)
            self.assertIsInstance(app.result[0], AbortedIoPipelineError)
        finally:
            h.close()


class _Opener(IoPipelineHandler):
    """Inside the parent, outside the multiplexer: opens a stream when told to."""

    def __init__(self, spec: IoPipeline.Spec) -> None:
        super().__init__()

        self._spec = spec
        self.msg: ta.Optional[IoPipelineMultiplexMessages.OpenStream] = None

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg == 'open':
            self.msg = IoPipelineMultiplexMessages.OpenStream(self._spec, 'from-handler')
            ctx.feed_in(self.msg)
            return
        ctx.feed_in(msg)


class TestOpenSources(unittest.TestCase):
    def test_open_from_a_handler_in_the_parent(self) -> None:
        app = _keep_open()
        opener = _Opener(app_spec(app))
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(explicit_open=False))
        h2 = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(explicit_open=False), extra_outer=[opener])  # noqa
        try:
            h2.enqueue('open')
            assert opener.msg is not None
            self.assertTrue(opener.msg.is_succeeded())
            self.assertTrue(app.saw_initial_input)
            self.assertEqual(app.metadata.info, 'from-handler')  # type: ignore[union-attr]
        finally:
            h.close()
            h2.close()

    def test_open_from_outside_the_pipeline_by_feeding_the_multiplexer(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(explicit_open=False))
        try:
            h.step()
            app = _keep_open()
            msg = IoPipelineMultiplexMessages.OpenStream(app_spec(app))
            out = Outcome(msg)
            mux_ref = h.pipeline.handlers()[-1]
            h.pipeline.feed_in_to(mux_ref, msg)
            h.step()
            self.assertIsInstance(out.result, IoPipelineMultiplexOpenedStream)
            self.assertTrue(app.saw_initial_input)
        finally:
            h.close()


class TestReferenceRelease(unittest.TestCase):
    def _run_gc_disabled(self, fn: ta.Callable[[], ta.Sequence[weakref.ReferenceType]]) -> None:
        was_enabled = gc.isenabled()
        gc.collect()
        gc.disable()
        try:
            refs = fn()
            self.assertEqual([r() for r in refs], [None] * len(refs))
        finally:
            if was_enabled:
                gc.enable()

    def test_closed_stream_is_released_while_the_connection_lives(self) -> None:
        # A factory which, unlike AppFactory, keeps no reference to the apps it creates.
        h = LoopbackHarness(lambda o: app_spec(_TimerApp(100.)))
        try:
            def run() -> ta.Sequence[weakref.ReferenceType]:
                h.feed(LOpen('k'))
                child = h.mux._children['k']
                refs: ta.List[weakref.ReferenceType] = [
                    weakref.ref(child),
                    weakref.ref(ta.cast(IoPipeline, child.pipeline)),
                    weakref.ref(child.stream),
                    weakref.ref(h.app('k')),
                ]
                h.feed(LData('k', b'data'), LEnd('k'))
                h.feed_stream('k', Emit(b'reply', IoPipelineMessages.FinalOutput))
                self.assertNotIn('k', h.mux.streams)
                del child
                return refs

            self._run_gc_disabled(run)
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()

    def test_reset_stream_is_released(self) -> None:
        h = LoopbackHarness(lambda o: app_spec(_TimerApp(100.)))
        try:
            def run() -> ta.Sequence[weakref.ReferenceType]:
                h.feed(LOpen('k', credit=0))
                h.feed_stream('k', Emit(b'blocked', IoPipelineMessages.ShutdownOutput))
                child = h.mux._children['k']
                refs: ta.List[weakref.ReferenceType] = [
                    weakref.ref(child),
                    weakref.ref(ta.cast(IoPipeline, child.pipeline)),
                    weakref.ref(child.stream),
                ]
                h.feed(LReset('k'))
                del child
                return refs

            self._run_gc_disabled(run)
        finally:
            h.close()

    def test_destroyed_parent_releases_everything(self) -> None:
        def run() -> ta.Sequence[weakref.ReferenceType]:
            h = LoopbackHarness(lambda o: app_spec(_TimerApp(100.)))
            h.feed(LOpen('a'), LOpen('b', credit=0))
            h.feed_stream('b', Emit(b'blocked'))
            refs: ta.List[weakref.ReferenceType] = [
                weakref.ref(h.driver),
                weakref.ref(h.pipeline),
                weakref.ref(h.mux),
                weakref.ref(h.mux._children['a']),
                weakref.ref(ta.cast(IoPipeline, h.mux._children['b'].pipeline)),
                weakref.ref(h.app('a')),
            ]
            h.close()
            return refs

        self._run_gc_disabled(run)
