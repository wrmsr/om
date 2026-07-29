# ruff: noqa: SLF001 UP006 UP045
# @om-lite
import time
import typing as ta
import unittest

from .....lite.check import check
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerRef
from ..heap import HeapIoPipelineSchedulingService


##


class NopIoPipelineHandler(IoPipelineHandler):
    pass


class TestHeapIoPipelineSchedulingService(unittest.TestCase):
    def make_pipeline(
            self,
            *handlers: IoPipelineHandler,
    ) -> ta.Tuple[IoPipeline, HeapIoPipelineSchedulingService]:
        sched = HeapIoPipelineSchedulingService()
        pipeline = IoPipeline.new(handlers, services=[sched])
        return pipeline, sched

    def find_handler_ref(
            self,
            pipeline: IoPipeline,
            handler: IoPipelineHandler,
    ) -> IoPipelineHandlerRef:
        return check.not_none(pipeline.find_handler(handler))

    def test_deadline_views_and_tickless_cancellation(self) -> None:
        handler = NopIoPipelineHandler()
        pipeline, sched = self.make_pipeline(handler)
        try:
            self.assertIsNone(sched.next_deadline())
            self.assertIsNone(sched.next_delay())

            before = time.monotonic()
            handle = sched.schedule(self.find_handler_ref(pipeline, handler), 60., lambda: None)
            after = time.monotonic()

            deadline = check.not_none(sched.next_deadline())
            self.assertGreaterEqual(deadline, before + 60.)
            self.assertLessEqual(deadline, after + 60.)
            delay = check.not_none(sched.next_delay())
            self.assertLess(0., delay)
            self.assertLessEqual(delay, 60.)

            handle.cancel()
            handle.cancel()

            self.assertIsNone(sched.next_deadline())
            self.assertIsNone(sched.next_delay())
            self.assertEqual(sched.run_due(), 0)
        finally:
            pipeline.destroy()

    def test_injected_clock(self) -> None:
        now = [10.]
        handler = NopIoPipelineHandler()
        sched = HeapIoPipelineSchedulingService(lambda: now[0])
        pipeline = IoPipeline.new([handler], services=[sched])
        try:
            events: ta.List[str] = []
            sched.schedule(self.find_handler_ref(pipeline, handler), 3., lambda: events.append('timer'))

            self.assertEqual(sched.next_deadline(), 13.)
            self.assertEqual(sched.next_delay(), 3.)
            self.assertEqual(sched.run_due(), 0)

            now[0] = 13.
            self.assertEqual(sched.next_delay(), 0.)
            self.assertEqual(sched.run_due(), 1)
            self.assertEqual(events, ['timer'])
            self.assertIsNone(sched.next_deadline())
        finally:
            pipeline.destroy()

    def test_due_batch_is_snapshotted_and_context_is_supplied(self) -> None:
        handler = NopIoPipelineHandler()
        pipeline, sched = self.make_pipeline(handler)
        try:
            handler_ref = self.find_handler_ref(pipeline, handler)
            events: ta.List[str] = []

            def first(ctx) -> None:
                self.assertIs(ctx.handler, handler)
                events.append('first')
                sched.schedule(ctx.ref, 0., lambda: events.append('third'))

            sched.schedule_context(handler_ref, 0., first)
            sched.schedule(handler_ref, 0., lambda: events.append('second'))

            self.assertEqual(sched.run_due(), 2)
            self.assertEqual(events, ['first', 'second'])
            self.assertIsNotNone(sched.next_deadline())

            self.assertEqual(sched.run_due(), 1)
            self.assertEqual(events, ['first', 'second', 'third'])
            self.assertIsNone(sched.next_deadline())
        finally:
            pipeline.destroy()

    def test_handler_removal_cancels_timer_in_current_due_batch(self) -> None:
        removing_handler = NopIoPipelineHandler()
        removed_handler = NopIoPipelineHandler()
        pipeline, sched = self.make_pipeline(removing_handler, removed_handler)
        try:
            removing_ref = self.find_handler_ref(pipeline, removing_handler)
            removed_ref = self.find_handler_ref(pipeline, removed_handler)
            events: ta.List[str] = []

            sched.schedule(removing_ref, 0., lambda: pipeline.remove(removed_ref))
            sched.schedule(removed_ref, 0., lambda: events.append('removed'))

            self.assertEqual(sched.run_due(), 1)
            self.assertEqual(events, [])
            self.assertTrue(removed_ref.invalidated)
            self.assertIsNone(sched.next_deadline())
            with self.assertRaises(RuntimeError):
                sched.schedule(removed_ref, 0., lambda: events.append('orphan'))
        finally:
            pipeline.destroy()

    def test_callback_failure_preserves_later_due_callbacks(self) -> None:
        handler = NopIoPipelineHandler()
        pipeline, sched = self.make_pipeline(handler)
        try:
            handler_ref = self.find_handler_ref(pipeline, handler)
            error = RuntimeError('timer')
            events: ta.List[str] = []

            def fail() -> None:
                raise error

            sched.schedule(handler_ref, 0., fail)
            sched.schedule(handler_ref, 0., lambda: events.append('later'))

            with self.assertRaises(RuntimeError) as raised:
                sched.run_due()
            self.assertIs(raised.exception, error)
            self.assertEqual(events, [])

            self.assertEqual(sched.run_due(), 1)
            self.assertEqual(events, ['later'])
        finally:
            pipeline.destroy()

    def test_pipeline_destroy_cancels_all_callbacks(self) -> None:
        handler = NopIoPipelineHandler()
        pipeline, sched = self.make_pipeline(handler)
        handler_ref = self.find_handler_ref(pipeline, handler)
        events: ta.List[str] = []
        sched.schedule(handler_ref, 60., lambda: events.append('timer'))

        pipeline.destroy()

        self.assertIsNone(sched.next_deadline())
        self.assertEqual(sched.run_due(), 0)
        self.assertEqual(events, [])
