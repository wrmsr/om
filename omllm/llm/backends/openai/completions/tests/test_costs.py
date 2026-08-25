"""Offline tests of compat-predeclared token cost translation for the openai completions backend."""
import pytest

from .....types.messages import TokenCost
from ..responses import translate_token_usage


# Captured from a live openrouter chat completion response (deepseek/deepseek-v4-flash-0731).
_OPENROUTER_RAW_USAGE = {
    'prompt_tokens': 6844,
    'completion_tokens': 45,
    'total_tokens': 6889,
    'cost': 0.00027736,
    'is_byok': False,
    'prompt_tokens_details': {
        'cached_tokens': 0,
        'cache_write_tokens': 0,
        'audio_tokens': 0,
        'video_tokens': 0,
    },
    'cost_details': {
        'upstream_inference_cost': 0.00027736,
        'upstream_inference_prompt_cost': 0.00027376,
        'upstream_inference_completions_cost': 3.6e-06,
    },
    'completion_tokens_details': {
        'reasoning_tokens': 46,
        'image_tokens': 0,
        'audio_tokens': 0,
    },
}

# Captured from a live openai chat completion response (gpt-5.4-mini) - no cost fields on the wire.
_OPENAI_RAW_USAGE = {
    'prompt_tokens': 7253,
    'completion_tokens': 4,
    'total_tokens': 7257,
    'prompt_tokens_details': {
        'cached_tokens': 6912,
        'audio_tokens': 0,
    },
    'completion_tokens_details': {
        'reasoning_tokens': 0,
        'audio_tokens': 0,
    },
}


def test_openrouter_cost_translation():
    usage = translate_token_usage(_OPENROUTER_RAW_USAGE, cost_mode='openrouter')

    assert usage.input == 6844
    assert usage.output == 45
    assert usage.reasoning == 46

    assert usage.cost == TokenCost(
        source='reported',
        input=0.00027376,
        output=3.6e-06,
        total=0.00027736,
    )


def test_cost_translation_requires_predeclared_mode():
    # The very same response yields no cost without the declared mode - fields are never probed speculatively.
    assert translate_token_usage(_OPENROUTER_RAW_USAGE).cost is None


def test_openai_shaped_usage_has_no_cost():
    assert translate_token_usage(_OPENAI_RAW_USAGE).cost is None

    # Even when the mode is declared, a response reporting nothing translates to no cost at all.
    assert translate_token_usage(_OPENAI_RAW_USAGE, cost_mode='openrouter').cost is None


def test_unknown_cost_mode_rejected():
    with pytest.raises(ValueError):  # noqa: PT011
        translate_token_usage(_OPENROUTER_RAW_USAGE, cost_mode='wat')  # type: ignore[arg-type]
