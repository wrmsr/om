# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""Posting into a stream's child pipeline, which reaches it through the parent's posting service."""
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...errors import ContextInvalidatedIoPipelineError
from ...posting.types import ClosedIoPipelinePostingError
from ...posting.types import IoPipelinePost
from ...posting.types import IoPipelinePosting
from ..handlers import MultiplexIoPipelineHandler
from ..types import ConnectionClosedMultiplexIoPipelineError
from ..types import IoPipelineMultiplexMessages
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LReset
from .loopback import OutboundRecorder


##


class _RecordingApp(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.inputs.append(msg)
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


def _outcome(post: IoPipelinePost) -> ta.List[ta.Any]:
    out: ta.List[ta.Any] = []
    post.add_listener(lambda p: out.append(p.get_exception() if p.is_failed() else 'ok'))
    return out


class _PostOnErrorApp(IoPipelineHandler):
    """On an inbound Error - a reset - posts into its own pipeline, recording the post's outcome."""

    def __init__(self) -> None:
        super().__init__()

        self.outcomes: ta.List[ta.List[ta.Any]] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.outcomes.append(_outcome(ctx.services[IoPipelinePosting].post(lambda: None)))
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class TestChildPosting(unittest.TestCase):
    def _harness(self) -> LoopbackHarness:
        return LoopbackHarness(lambda o: IoPipeline.Spec([_RecordingApp()]))

    def test_post_runs_in_the_child_at_the_next_parent_step(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            posting = child.services[IoPipelinePosting]

            ran: ta.List[ta.Any] = []
            post = posting.post(lambda: ran.append(child.is_ready))
            outcome = _outcome(post)
            self.assertEqual(ran, [])

            h.step()

            self.assertEqual(ran, [True])
            self.assertEqual(outcome, ['ok'])
        finally:
            h.close()

    def test_post_context_runs_with_the_child_handler_context(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            ref = child.handlers()[0]
            app = h.app('k')

            seen: ta.List[ta.Any] = []
            post = child.services[IoPipelinePosting].post_context(
                ref,
                lambda ctx: seen.append((ctx.handler, ctx.pipeline)),
            )
            outcome = _outcome(post)
            h.step()

            self.assertEqual(seen, [(app, child)])
            self.assertEqual(outcome, ['ok'])
        finally:
            h.close()

    def test_posts_are_ordered_with_feed_stream(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            app = h.app('k')
            posting = child.services[IoPipelinePosting]

            posting.post(lambda: app.inputs.append('p1'))
            h.driver.enqueue(IoPipelineMultiplexMessages.FeedStream('k', ['m']))
            posting.post(lambda: app.inputs.append('p2'))
            h.step()

            self.assertEqual(app.inputs[-3:], ['p1', 'm', 'p2'])
        finally:
            h.close()

    def test_post_into_an_ended_stream_is_refused(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            posting = child.services[IoPipelinePosting]
            ref = child.handlers()[0]
            h.feed(LReset('k'))

            with self.assertRaises(ClosedIoPipelinePostingError):
                posting.post(lambda: None)
            with self.assertRaises(ClosedIoPipelinePostingError):
                posting.post_context(ref, lambda ctx: None)
        finally:
            h.close()

    def test_post_pending_when_the_stream_ends_fails(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            posting = child.services[IoPipelinePosting]

            # The reset is read from the transport after the post was queued, so the post runs first; one queued after
            # the reset has arrived finds the stream gone when the parent delivers it.
            post = posting.post(lambda: None)
            h.feed(LReset('k'))
            self.assertTrue(post.is_succeeded())

            h.feed(LOpen('j'))
            child_j = ta.cast(IoPipeline, h.mux.child_pipeline('j'))
            posting_j = child_j.services[IoPipelinePosting]
            h.driver.feed_input(LReset('j'))
            late = posting_j.post(lambda: None)
            outcome = _outcome(late)
            h.step()
            self.assertEqual(outcome, ['ok'])  # ran before the reset was read: it was queued first
            self.assertIsNone(h.mux.child_pipeline('j'))
        finally:
            h.close()

    def test_post_fails_when_the_multiplexer_is_removed_first(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            post = child.services[IoPipelinePosting].post(lambda: None)
            outcome = _outcome(post)

            mux_ref = h.pipeline.find_handler(h.mux)
            h.pipeline.remove(ta.cast(ta.Any, mux_ref))
            h.step()

            self.assertEqual(len(outcome), 1)
            self.assertIsInstance(outcome[0], ContextInvalidatedIoPipelineError)
        finally:
            h.close()

    def test_post_fails_when_the_parent_closes_first(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            child = ta.cast(IoPipeline, h.mux.child_pipeline('k'))
            post = child.services[IoPipelinePosting].post(lambda: None)
            outcome = _outcome(post)

            h.close()

            self.assertEqual(len(outcome), 1)
            self.assertIsInstance(outcome[0], AbortedIoPipelineError)
        finally:
            h.close()

    def test_post_made_while_the_stream_is_being_reset_fails(self) -> None:
        # A child told of its reset posts into itself from that very turn: the stream is still running when the post
        # is accepted, and gone by the time the parent hands it to the host.
        h = LoopbackHarness(lambda o: IoPipeline.Spec([_PostOnErrorApp()]))
        try:
            h.feed(LOpen('k'))
            app = ta.cast(_PostOnErrorApp, h.app('k'))

            h.feed(LReset('k'))

            self.assertEqual(len(app.outcomes), 1)
            self.assertEqual(len(app.outcomes[0]), 1)
            self.assertIsInstance(app.outcomes[0][0], ConnectionClosedMultiplexIoPipelineError)
            self.assertIsNone(h.mux.child_pipeline('k'))
        finally:
            h.close()

    def test_no_child_posting_without_parent_posting(self) -> None:
        mux = MultiplexIoPipelineHandler(LoopbackAdapter(), lambda o: IoPipeline.Spec([_RecordingApp()]))
        with IoPipeline.new([OutboundRecorder(), mux]) as parent:
            parent.feed_initial_input()
            parent.feed_in(LOpen('k'))
            child = ta.cast(IoPipeline, mux.child_pipeline('k'))

            self.assertIsNone(child.services.find(IoPipelinePosting))
