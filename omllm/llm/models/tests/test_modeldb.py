from ...types.models import Model
from ...types.models import ModelKey
from ...types.models import resolve_model_limits
from ..modeldb import modeldb_model_limits
from ..modeldb import modeldb_token_pricing


def test_modeldb_token_pricing():
    pricing = modeldb_token_pricing('anthropic', 'claude-sonnet-5')()

    # Asserted structurally rather than against exact figures, which change with cache refreshes.
    assert pricing is not None
    assert pricing.input is not None and pricing.input > 0
    assert pricing.output is not None and pricing.output > 0
    assert pricing.cache_read is not None
    assert 0 < pricing.cache_read < pricing.input


def test_modeldb_token_pricing_unknown():
    assert modeldb_token_pricing('anthropic', 'no-such-model')() is None
    assert modeldb_token_pricing('no-such-provider', 'no-such-model')() is None


def test_modeldb_model_limits():
    provider = modeldb_model_limits('openai', 'gpt-5.6-sol')
    limits = provider()

    assert limits is not None
    assert limits.context > limits.output > 0
    assert limits.input is not None
    assert limits.input <= limits.context - limits.output

    model = Model(key=ModelKey('test', 'test'), backend='test', limits=provider)
    assert resolve_model_limits(model) == limits


def test_modeldb_model_limits_unknown():
    assert modeldb_model_limits('openai', 'no-such-model')() is None
    assert modeldb_model_limits('no-such-provider', 'no-such-model')() is None
