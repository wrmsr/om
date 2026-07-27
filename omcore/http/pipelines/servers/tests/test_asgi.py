# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from ...requests import FullIoPipelineHttpRequest
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..apps.asgi import AsgiIoPipelineHandler


##


class PauseOutputOnFirstBodyIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self._paused = False

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)

        if isinstance(msg, IoPipelineHttpResponseBodyData) and not self._paused:
            self._paused = True
            ctx.feed_in(IoPipelineFlowMessages.PauseOutput())


##


class TestAsgiIoPipelineHandler(unittest.TestCase):
    @staticmethod
    def _request() -> FullIoPipelineHttpRequest:
        return FullIoPipelineHttpRequest.simple('localhost', '/')

    def test_response_and_flush_order(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
                'body': b'a',
                'more_body': True,
            })
            completed.append('a')

            await send({
                'type': 'http.response.body',
                'body': b'b',
            })
            completed.append('b')

        channel = IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(self._request())

        output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineHttpResponseBodyData,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.FinalOutput,
            ],
        )
        self.assertEqual(output[2].data, b'a')
        self.assertEqual(output[4].data, b'b')
        self.assertEqual(completed, ['start', 'a', 'b'])

    def test_send_waits_for_output_writability(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
                'body': b'a',
                'more_body': True,
            })
            completed.append('a')

            await send({
                'type': 'http.response.body',
                'body': b'b',
            })
            completed.append('b')

        channel = IoPipeline.new(
            [
                PauseOutputOnFirstBodyIoPipelineHandler(),
                AsgiIoPipelineHandler(app),
            ],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(self._request())

        paused_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in paused_output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineHttpResponseBodyData,
                IoPipelineFlowMessages.FlushOutput,
            ],
        )
        self.assertEqual(paused_output[2].data, b'a')
        self.assertEqual(completed, ['start', 'a'])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())

        resumed_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in resumed_output],
            [
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(resumed_output[0].data, b'b')
        self.assertEqual(completed, ['start', 'a'])

        channel.run_deferred(resumed_output[-1])

        final_output = channel.output.drain()
        self.assertEqual(len(final_output), 1)
        self.assertIsInstance(final_output[0], IoPipelineMessages.FinalOutput)
        self.assertEqual(completed, ['start', 'a', 'b'])

    def test_pause_before_request_blocks_first_send(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 204,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
            })
            completed.append('body')

        channel = IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(IoPipelineFlowMessages.PauseOutput())
        channel.feed_in(self._request())
        self.assertEqual(channel.output.drain(), [])
        self.assertEqual(completed, [])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())
        resumed_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in resumed_output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )

        channel.run_deferred(resumed_output[-1])

        final_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in final_output],
            [
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.FinalOutput,
            ],
        )
        self.assertEqual(completed, ['start', 'body'])
