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
