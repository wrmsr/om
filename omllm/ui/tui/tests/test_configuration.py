import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....core import ui
from ....harness.prompts.standard import TextPromptContributor
from ....harness.skills.catalogs import SkillCatalog
from ..config import Config
from ..inject import prompt_contributors
from .features import RecordingTextDisplayer
from .features import write_verification_skill
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


def test_cli_options():
    config = Config.parse_from_arguments([
        '--effort', 'minimal', '--no-thinking', '--skills-dir', '/one', '--skills-dir', '/two',
        '--system-prompt', 'custom',
    ])
    assert config.effort is llm.ReasoningEffort.MINIMAL
    assert config.thinking is False
    assert config.skills_dirs == ['/one', '/two']
    assert config.system_prompt == 'custom'


@pytest.mark.asyncs('asyncio')
async def test_effort_command_updates_real_turn_options_and_preserves_others():
    display = RecordingTextDisplayer()
    seen = []
    turns = [
        llm.BackendScriptTurn(text_message('ok'), expect=lambda inv: seen.append(check.not_none(inv.options)))
        for _ in range(3)
    ]
    model = llm.Model(
        key=llm.ModelKey('scripted', 'test'),
        backend='scripted',
        reasoning_efforts=frozenset({llm.ReasoningEffort.LOW, llm.ReasoningEffort.HIGH}),
    )
    backend = llm.ScriptedImmediateBackend(model, llm.BackendScript(turns))
    async with headless_tui(inj.override(
        bind_headless_tui(Config(
            model='scripted', in_memory=True, no_skills=True, effort=llm.ReasoningEffort.LOW, thinking=False,
        )),
        inj.bind(ui.TextDisplayer, to_const=display),
        inj.bind(agn.BackendManager, to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        })),
    )) as tui:
        turn_config = check.not_none(tui.agent.state.turn_config)
        await tui.agent.update_state(lambda s: dc.replace(s, turn_config=dc.replace(
            turn_config,
            llm_options=dc.replace(check.not_none(turn_config.llm_options), max_tokens=1234),
        )))
        await tui.session.prompt('first')
        await tui.session.prompt('/effort high')
        await tui.session.prompt('/effort minimal')
        assert 'does not support effort minimal' in display.lines[-1]
        await tui.session.prompt('second')
        await tui.session.prompt('/effort default')
        await tui.session.prompt('third')

    assert [o.reasoning_effort for o in seen] == [llm.ReasoningEffort.LOW, llm.ReasoningEffort.HIGH, None]
    assert all(o.thinking is False and o.max_tokens == 1234 for o in seen)


@pytest.mark.asyncs('asyncio')
async def test_effort_command_accounts_for_installed_tools(tmp_path):
    write_verification_skill(tmp_path, 'phrase')
    display = RecordingTextDisplayer()
    model = llm.default_model_catalog()[llm.ModelKey('openai', 'gpt-5.4-nano')]
    backend = llm.ScriptedImmediateBackend(model)
    async with headless_tui(inj.override(
        bind_headless_tui(Config(model='scripted', in_memory=True, skills_dirs=[str(tmp_path)])),
        inj.bind(ui.TextDisplayer, to_const=display),
        inj.bind(agn.BackendManager, to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        })),
    )) as tui:
        await tui.session.prompt('/effort')
        assert display.lines[-1].endswith('Supported: none')
        await tui.session.prompt('/effort low')
        assert 'does not support effort low with tools' in display.lines[-1]
        await tui.session.prompt('/effort none')
        assert check.not_none(check.not_none(tui.agent.state.turn_config).llm_options).reasoning_effort is (
            llm.ReasoningEffort.NONE
        )


@pytest.mark.asyncs('asyncio')
async def test_host_skills_prompt_contribution_and_tool_roundtrip(tmp_path):
    host = tmp_path / 'host'
    write_verification_skill(host, 'host-phrase')
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'AGENTS.md').write_text('REPOSITORY_SENTINEL')
    write_verification_skill(target, 'wrong-phrase')
    seen = []
    display = RecordingTextDisplayer()

    def expect(inv):
        seen.append(inv.context)

    async with headless_tui(inj.override(
        bind_headless_tui(Config(
            model='scripted', in_memory=True, cwd=str(target), skills_dirs=[str(host)], system_prompt='HOST_SENTINEL',
        )),
        bind_scripted_backend(
            llm.BackendScriptTurn(
                tool_call_message(llm.ToolCall('s1', 'read_skill', {'name': 'verification'})),
                expect=expect,
            ),
            tool_call_message(llm.ToolCall(
                's2', 'read_skill', {'name': 'verification', 'path': 'reference/phrase.txt'},
            )),
            llm.BackendScriptTurn(text_message('host-phrase'), expect=expect),
            llm.BackendScriptTurn(text_message('applied'), expect=expect),
        ),
        inj.bind(ui.TextDisplayer, to_const=display),
    ), prompt_contributors().bind_item(to_const=TextPromptContributor('extension', 'EXTENSION_SENTINEL'))) as tui:
        catalog = await tui.injector[SkillCatalog]
        assert [s.name for s in catalog.skills] == ['verification']
        assert [t.name for t in check.not_none(tui.agent.state.context.tools)] == ['read_skill']
        await tui.session.prompt('Use the verification skill.')
        results = [m for m in check.not_none(tui.agent.state.context.messages) if isinstance(m, llm.ToolResultMessage)]
        assert all(not r.is_error for r in results)
        assert results[-1].content[0].text == 'host-phrase'
        await tui.session.prompt('/skills')
        assert 'verification:' in display.lines[-1]
        await tui.session.prompt('/skills show verification reference/phrase.txt')
        assert display.lines[-1] == 'host-phrase'
        await tui.session.prompt('/skills use verification apply it')

    prompt = check.not_none(seen[0].system_prompt)
    assert 'HOST_SENTINEL' in prompt and 'EXTENSION_SENTINEL' in prompt
    assert 'REPOSITORY_SENTINEL' not in prompt
    assert 'host-phrase' not in prompt
    assert 'wrong-phrase' not in str(seen)
    assert 'Its full instructions follow' in str(seen[-1].messages[-1])


@pytest.mark.asyncs('asyncio')
async def test_skills_can_be_disabled_without_reading_configured_roots(tmp_path):
    async with headless_tui(bind_headless_tui(Config(
        model='scripted', in_memory=True, no_skills=True, skills_dirs=[str(tmp_path / 'missing')],
    ))) as tui:
        catalog = await tui.injector[SkillCatalog]
        assert not catalog.skills and not catalog.diagnostics
        assert not tui.agent.state.context.tools


@pytest.mark.asyncs('asyncio')
async def test_empty_skill_catalog_does_not_advertise_a_reading_tool(tmp_path):
    async with headless_tui(bind_headless_tui(Config(
        model='scripted', in_memory=True, skills_dirs=[str(tmp_path)],
    ))) as tui:
        assert not tui.agent.state.context.tools
        assert 'No tools are available' in check.not_none(tui.agent.state.context.system_prompt)


@pytest.mark.asyncs('asyncio')
async def test_skill_tool_pages_long_resources_and_validates_ranges(tmp_path):
    write_verification_skill(tmp_path, 'a' * 20_000 + 'the end')
    async with headless_tui(bind_headless_tui(Config(
        model='scripted', in_memory=True, skills_dirs=[str(tmp_path)],
    ))) as tui:
        tool = check.not_none(tui.agent.state.context.tools).by_name['read_skill']

        async def read(**kwargs):
            return await tool.executor(agn.ToolContext(
                tool=tool,
                args=dict(name='verification', path='reference/phrase.txt', **kwargs),
            ))

        first = await read()
        assert first.error is None
        assert 'Continue with offset=20000.' in first.content.text
        assert first.content.text.endswith('a' * 20_000)
        assert 'the end' not in first.content.text
        last = await read(offset=20_000)
        assert last.error is None
        assert last.content.text.endswith('the end')
        assert 'End of resource.' in last.content.text
        for kwargs in [dict(offset=-1), dict(offset=30_000), dict(limit=0), dict(limit=20_001)]:
            assert (await read(**kwargs)).error is not None
