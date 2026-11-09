from ..signatures import ToolCallSignature
from ..signatures import build_tool_call_signature
from ..signatures import parse_tool_call_signature


def test_round_trip():
    for thought_signature, function_call_id in [
        ('sig', 'call-1'),
        ('sig', None),
        (None, 'call-1'),
    ]:
        s = build_tool_call_signature(thought_signature=thought_signature, function_call_id=function_call_id)
        assert parse_tool_call_signature(s) == ToolCallSignature(
            thought_signature=thought_signature,
            function_call_id=function_call_id,
        )


def test_nothing_is_nothing():
    assert build_tool_call_signature(thought_signature=None, function_call_id=None) is None
    assert build_tool_call_signature(thought_signature='', function_call_id='') is None
    assert parse_tool_call_signature(None) == ToolCallSignature()
    assert parse_tool_call_signature('') == ToolCallSignature()


def test_a_bare_signature_is_a_thought_signature():
    assert parse_tool_call_signature('CoQBAb').thought_signature == 'CoQBAb'
    assert parse_tool_call_signature('CoQBAb').function_call_id is None

    # Even one json happens to read, as a number.
    assert parse_tool_call_signature('12345') == ToolCallSignature(thought_signature='12345')


def test_foreign_json_carries_nothing():
    assert parse_tool_call_signature('{"id":"fc_1"}') == ToolCallSignature()
    assert parse_tool_call_signature('{"type":"reasoning","id":"rs_1"}') == ToolCallSignature()
    assert parse_tool_call_signature('{"function_call_id":7}') == ToolCallSignature()
