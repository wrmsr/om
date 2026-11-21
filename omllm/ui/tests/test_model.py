import pytest

from omcore import check
from omcore import inject as inj

from ... import agent as agn
from ... import llm
from ...agent.tests.scripted import text_message
from ...core import ui
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import headless_ui


##


class _RecordingTextDisplayer(ui.TextDisplayer):
    def __init__(self) -> None:
        super().__init__()

        self.texts: list[str] = []

    async def display_text(self, *texts: ui.CanText) -> None:
        self.texts.append(ui.Text.str_of(list(texts)))


@pytest.mark.asyncs('asyncio')
async def test_headless_model_switch_routes_prompts_to_new_backend():
    m1 = llm.Model(
        key=llm.ModelKey('scripted', 'one'),
        name='One',
        backend='scripted',
        short_ids=llm.ModelShortIds(short_id='one'),
    )
    m2 = llm.Model(
        key=llm.ModelKey('scripted', 'two'),
        name='Two',
        backend='scripted',
        short_ids=llm.ModelShortIds(short_id='two'),
    )

    b1 = llm.ScriptedImmediateBackend(m1, llm.BackendScript([llm.BackendScriptTurn(text_message('from one'))]))
    b2 = llm.ScriptedImmediateBackend(m2, llm.BackendScript([llm.BackendScriptTurn(text_message('from two'))]))
    displayer = _RecordingTextDisplayer()

    async with headless_ui(bind_headless_ui(
        UiConfig(
            model='scripted',
            immediate=True,
            in_memory=True,
        ),
        ui_rewriter=inj.overrider(
            inj.bind(ui.TextDisplayer, to_const=displayer),
        ),
        host_rewriter=inj.overrider(
            inj.bind(llm.ModelCatalog, to_const=llm.ModelCatalog([m1, m2])),
            inj.bind(agn.BackendManager, to_const=agn.DictBackendManager.of(b1, b2, default=b1)),
        ),
    )) as hui:
        assert hui.agent.state.model == m1

        r1 = await hui.agent.prompt('first')
        m1_msg = check.isinstance((r1.context.messages or ())[-1], llm.AiMessage)
        assert check.isinstance(check.single(m1_msg.content), llm.TextContent).text == 'from one'

        await hui.commands.parse('model two').run()
        assert hui.agent.state.model == m2
        assert 'Model: scripted::two' in displayer.texts[-1]

        r2 = await hui.agent.prompt('second')
        m2_msg = check.isinstance((r2.context.messages or ())[-1], llm.AiMessage)
        assert check.isinstance(check.single(m2_msg.content), llm.TextContent).text == 'from two'

        await hui.commands.parse('status').run()
        assert 'Model: scripted::two' in displayer.texts[-1]
