import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from .... import llm
from ....agent.inject.backends import InjectorBackendOpener
from ....agent.inject.backends import ScriptedBackendBinder
from ....agent.tests.scripted import text_message
from ....core import ui
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ..base import CommandContext
from ..model import ModelCommand


##


class _Capture:
    def __init__(self) -> None:
        super().__init__()

        self.lines: list[str] = []

    async def __call__(self, *texts: ui.CanText) -> None:
        self.lines.append(ui.Text.str_of(list(texts)))

    @property
    def last(self) -> str:
        return self.lines[-1]


def _make_model(
        mid: str,
        short_id: str,
        *,
        efforts: frozenset[llm.ReasoningEffort] | None = None,
        limits: llm.ModelLimits | None = None,
) -> llm.Model:
    return llm.Model(
        key=llm.ModelKey('scripted', mid),
        name=f'Model {mid}',
        backend='scripted',
        short_ids=llm.ModelShortIds(short_id=short_id),
        reasoning_efforts=efforts,
        limits=limits,
    )


@pytest.mark.asyncs('asyncio')
async def test_model_command_show_list_switch_and_unload():
    m_alpha = _make_model(
        'alpha',
        'alpha',
        efforts=frozenset({llm.ReasoningEffort.HIGH}),
        limits=llm.ModelLimits(context=100_000, output=8_000),
    )
    m_beta = _make_model(
        'beta',
        'beta',
        efforts=frozenset(),
        limits=llm.ModelLimits(context=50_000, output=4_000),
    )
    catalog = llm.ModelCatalog([m_alpha, m_beta])

    opener = InjectorBackendOpener(
        binder=ScriptedBackendBinder(
            script=llm.BackendScript(
                [llm.BackendScriptTurn(text_message('hi'))],
                on_exhausted='restart',
            ),
        ),
    )

    async with agn.ManagedBackendManager(
        opener=opener,
        events=asl.asyncio.Events(),
        default_model=m_alpha,
        no_prefer_stream=True,
    ) as backends:
        agent = agn.Agent(
            backends=backends,
            turn_runner=agn.NullaryFactoryTurnRunner(
                agn.TurnLoop,
                cancellation=asl.asyncio.Cancellation(),
                group_runner=AsyncioGroupRunner(),
            ),
        )

        # Simulate startup state on alpha with HIGH effort and an existing context budget.
        async with backends.acquire_backend(llm.ImmediateBackend, m_alpha):  # type: ignore[type-abstract]
            pass
        await agent.update_state(lambda s: dc.replace(
            s,
            model=m_alpha,
            context=dc.replace(
                s.context,
                context_budget=agn.ContextBudget(
                    context_limit=100_000,
                    input_limit=92_000,
                    threshold=90_976,
                    output_reserve=8_000,
                    observed_input=1_000,
                ),
            ),
            turn_config=agn.TurnConfig(
                llm_options=llm.Options(reasoning_effort=llm.ReasoningEffort.HIGH),
            ),
        ))

        cmd = ModelCommand(agent=agent, backends=backends, catalog=catalog)
        assert cmd.name == 'model'

        cap = _Capture()
        ctx = CommandContext(print=cap)

        # Show current model.
        await cmd.run(ctx, [])
        assert 'Model: scripted::alpha (Model alpha)' in cap.last
        assert 'Loaded: scripted::alpha' in cap.last

        # List catalog models.
        await cmd.run(ctx, ['--list'])
        assert '* scripted::alpha  [alpha]  (loaded)' in cap.last
        assert '  scripted::beta  [beta]' in cap.last

        # Unknown model leaves state untouched.
        await cmd.run(ctx, ['does-not-exist'])
        assert 'Unknown model' in cap.last
        assert agent.state.model == m_alpha

        # Switch to beta: clears unsupported HIGH effort and old context budget.
        await cmd.run(ctx, ['beta'])
        assert 'Model: scripted::beta' in cap.last
        assert 'Cleared unsupported reasoning effort: high' in cap.last
        assert agent.state.model == m_beta
        assert check.not_none(check.not_none(agent.state.turn_config).llm_options).reasoning_effort is None
        assert agent.state.context.context_budget is None

        # Unload alpha by short id.
        await cmd.run(ctx, ['--unload', 'alpha'])
        assert cap.last == 'Unloaded: scripted::alpha'
        assert backends.loaded_models == (m_beta,)

        # Unload remaining idle backends.
        await cmd.run(ctx, ['--unload'])
        assert cap.last == 'Unloaded 1 idle backend(s).'
        assert backends.loaded_models == ()
