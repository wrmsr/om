import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import scripted_backend
from ....agent.tests.scripted import text_message
from ....core import ui
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ..base import CommandContext
from ..compact import CompactCommand


##


class _Capture:
    def __init__(self):
        self.lines: list[str] = []

    async def __call__(self, *texts):
        self.lines.append(ui.Text.str_of(list(texts)))

    @property
    def last(self) -> str:
        return self.lines[-1]


def _backends(backend):
    return agn.DictBackendManager({llm.ImmediateBackend: {None: backend}})  # type: ignore[type-abstract]


@pytest.mark.asyncs('asyncio')
async def test_compact_command():
    seen: list = []

    def expect(invocation):
        seen.append(invocation.context)

    backend = scripted_backend(llm.BackendScriptTurn(text_message('Summary.'), expect=expect))
    agent = agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=_backends(backend),
        ),
    )
    await agent.update_state(lambda s: dc.replace(s, context=agn.Context(messages=[
        llm.UserMessage('x' * 2_000),
        llm.AiMessage([llm.TextContent('ok')]),
        llm.UserMessage('y' * 2_000),
        llm.AiMessage([llm.TextContent('ok')]),
    ])))

    cmd = CompactCommand(
        agent=agent,
        compaction=agn.ContextCompactionRunner(
            backends=_backends(backend),
            context_lifecycle_manager=agn.StandardContextLifecycleManager(
                compactor=agn.SummarizingContextCompactor(config=agn.SummarizingContextCompactor.Config(
                    keep_recent_tokens=100,
                    max_summary_tokens=50,
                )),
            ),
        ),
    )
    assert cmd.name == 'compact'

    cap = _Capture()
    ctx = CommandContext(print=cap)

    await cmd.run(ctx, ['keep', 'the', 'paths'])
    assert cap.last.startswith('Context compacted: ')
    assert cap.last.endswith(' tokens')
    assert check.not_none(agent.state.context.projection).summary == 'Summary.'
    [request] = seen
    request_text = check.isinstance(check.isinstance((request.messages or [])[0], llm.UserMessage).content, str)
    assert 'keep the paths' in request_text

    # Nothing ahead of the kept tail is left to summarize.
    await cmd.run(ctx, [])
    assert cap.last == 'Nothing to compact.'
    assert backend.invocations == 1

    # No compactor at all.
    bare = CompactCommand(agent=agent, compaction=agn.ContextCompactionRunner(backends=_backends(backend)))
    await bare.run(ctx, [])
    assert cap.last == 'Context compaction is not available.'
