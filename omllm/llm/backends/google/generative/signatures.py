"""
Replay identity for a tool call produced by this backend rides ToolCall.backend_signature as compact JSON, carrying
what Gemini wants back with the call: the 'thought_signature' issued on its part, when there was one, and its
'function_call_id', when Gemini issued one - in which case Gemini matches the call's response to it by that id, which
the response must carry too. Text and thinking parts carry a bare thought signature, having nothing else to carry.

A call id Gemini did not issue is fabricated locally, to pair results with calls here, and is never sent back: such a
response matches its call by order, as Gemini expects. A signature which is not JSON is a bare thought signature, as
this backend wrote before it recorded ids; JSON carrying neither key is another backend's, unreadable here and dropped.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore.formats.json import all as json


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolCallSignature:
    thought_signature: str | None = None

    # Gemini's own id for the call, as distinct from `ToolCall.id`, which may be a local fabrication.
    function_call_id: str | None = None


def build_tool_call_signature(
        *,
        thought_signature: str | None,
        function_call_id: str | None,
) -> str | None:
    if not thought_signature and not function_call_id:
        return None

    return json.dumps_compact({
        **({'function_call_id': function_call_id} if function_call_id else {}),
        **({'thought_signature': thought_signature} if thought_signature else {}),
    })


def parse_tool_call_signature(s: str | None) -> ToolCallSignature:
    if not s:
        return ToolCallSignature()

    try:
        raw = json.loads(s)
    except (json.DecodeError, ValueError):
        return ToolCallSignature(thought_signature=s)

    if not isinstance(raw, ta.Mapping):
        # A thought signature is base64, which json reads as nothing but a number in the rarest of cases.
        return ToolCallSignature(thought_signature=s)

    raw_ts = raw.get('thought_signature')
    raw_id = raw.get('function_call_id')
    return ToolCallSignature(
        thought_signature=raw_ts if isinstance(raw_ts, str) and raw_ts else None,
        function_call_id=raw_id if isinstance(raw_id, str) and raw_id else None,
    )
