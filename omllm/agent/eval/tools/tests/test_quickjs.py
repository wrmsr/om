"""The quickjs tool: evals off the loop, bounded by the runner's timeout, and interrupted by a cancellation."""
import asyncio
import time

import pytest

from ..... import llm
from .....core.asyncs.asyncio import AsyncioJobRunner
from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ..quickjs import QuickjsTool


pytest.importorskip('omdev.js.quickjs._pyqjsng')


##


async def _poll(fn, timeout=5., interval=.01):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        await asyncio.sleep(interval)
    return fn()


def _tool(runner):
    return QuickjsTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        job_runner=runner,
    )


def _context(tool, **args):
    return ToolContext(
        tool=tool.tool(),
        args=args,
        llm_tool_call=llm.ToolCall('t1', 'quickjs', args),
    )


@pytest.mark.asyncs('asyncio')
async def test_eval_result_is_json():
    async with AsyncioJobRunner() as runner:
        tool = _tool(runner)

        result = await tool.execute_context(_context(tool, code='[1, 2].map(x => x * 2)'))

        assert result.error is None
        assert result.content.text == '[2,4]'

        result = await tool.execute_context(_context(tool, code='1 + 1'))

        assert result.error is None
        assert result.content.text == '2'


@pytest.mark.asyncs('asyncio')
async def test_runaway_eval_times_out_as_a_tool_error():
    async with AsyncioJobRunner() as runner:
        tool = _tool(runner)

        result = await tool.execute_context(_context(tool, code='while (true) {}', timeout_s=.1))

        assert result.error is not None
        assert 'timed out' in result.content.text
        # The eval was interrupted, not left spinning.
        assert await _poll(lambda: not runner.num_running)


@pytest.mark.asyncs('asyncio')
async def test_cancelling_the_call_interrupts_the_eval():
    async with AsyncioJobRunner() as runner:
        tool = _tool(runner)

        task = asyncio.create_task(tool.execute_context(_context(tool, code='while (true) {}')))
        assert await _poll(lambda: runner.num_running)

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert await _poll(lambda: not runner.num_running)
