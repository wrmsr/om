import pytest

from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from ... import llm
from ...core.asyncs.asyncio import AsyncioGroupRunner
from ..agent import Agent
from ..backends import DictBackendManager
from ..turns.loop import TurnLoop
from ..types.turns import NullaryFactoryTurnRunner
from ..types.turns import PromptCacheConfig
from ..types.turns import TurnConfig
from .scripted import text_message


##


def _model(cache: llm.CacheCapabilities | None) -> llm.Model:
    return llm.Model(
        key=llm.ModelKey('test', 'm'),
        backend='scripted',
        cache=cache,
    )


def test_prompt_cache_resolves_per_model_capabilities():
    cfg = PromptCacheConfig(key='sess-123')

    # Anthropic: explicit opt-in retention, no cache_key.
    anthropic = _model(llm.CacheCapabilities(
        control_style='anthropic',
        retentions=frozenset({llm.CacheRetention.FIVE_MINUTES, llm.CacheRetention.ONE_HOUR}),
    ))
    opts = cfg.resolve_options(anthropic)
    assert opts == llm.Options(cache_retention=llm.CacheRetention.FIVE_MINUTES)

    # OpenAI Responses / Completions: cache_key supported, implicit caching already enabled so no forced retention.
    openai = _model(llm.CacheCapabilities(
        control_style='openai_ttl',
        retentions=frozenset({llm.CacheRetention.THIRTY_MINUTES}),
        key=True,
    ))
    assert cfg.resolve_options(openai) == llm.Options(cache_key='sess-123')

    # OpenRouter: session affinity header via cache_key, no retention.
    openrouter = _model(llm.CacheCapabilities(
        control_style='openrouter',
        key=True,
    ))
    assert cfg.resolve_options(openrouter) == llm.Options(cache_key='sess-123')

    # Google implicit & uncached models: neither field sent.
    google = _model(llm.CacheCapabilities(control_style='google_implicit'))
    assert cfg.resolve_options(google) is None
    assert cfg.resolve_options(_model(None)) is None

    # Explicit llm_options take precedence over defaults.
    explicit = llm.Options(cache_retention=llm.CacheRetention.ONE_HOUR)
    assert cfg.resolve_options(anthropic, explicit) == llm.Options(cache_retention=llm.CacheRetention.ONE_HOUR)

    explicit_key = llm.Options(cache_key='custom-key')
    assert cfg.resolve_options(openai, explicit_key) == llm.Options(cache_key='custom-key')


@pytest.mark.asyncs('asyncio')
async def test_turn_loop_applies_prompt_cache_against_active_model():
    seen_options: list[llm.Options | None] = []

    def expect(inv):
        seen_options.append(inv.options)

    anthropic_model = _model(llm.CacheCapabilities(
        control_style='anthropic',
        retentions=frozenset({llm.CacheRetention.FIVE_MINUTES}),
    ))
    backend = llm.ScriptedImmediateBackend(
        anthropic_model,
        llm.BackendScript([
            llm.BackendScriptTurn(text_message('hi'), expect=expect),
        ]),
    )
    agent = Agent(
        backends=DictBackendManager.of(backend),
        turn_runner=NullaryFactoryTurnRunner(
            TurnLoop,
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
        ),
    )

    await agent.update_state(lambda s: dc.replace(
        s,
        model=anthropic_model,
        turn_config=TurnConfig(prompt_cache=PromptCacheConfig(key='sess-abc')),
    ))
    await agent.prompt('hello')

    assert seen_options == [llm.Options(cache_retention=llm.CacheRetention.FIVE_MINUTES)]
