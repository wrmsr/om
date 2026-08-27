"""
Replay identity for content produced by this backend rides Content.backend_signature, always as compact JSON:

- ThinkingContent: the entire raw reasoning output item. Reasoning is opaque (encrypted) and must be replayed as the
  verbatim item to be preserved across turns at all.
- TextContent: the message output item's identity - its 'id', plus its 'phase' when reported.
- ToolCall: the function_call output item's 'id' (the call id itself rides ToolCall.id).

Signatures from other backends are unreadable here and must be dropped rather than replayed - the parsers return None
for anything unrecognized rather than raising.
"""
import typing as ta

from omcore.formats.json import all as json


##


def build_thinking_signature(raw_item: ta.Mapping[str, ta.Any]) -> str:
    return json.dumps_compact(raw_item)


def parse_thinking_signature(s: str | None) -> ta.Mapping[str, ta.Any] | None:
    if not s:
        return None

    try:
        raw_item = json.loads(s)
    except (json.DecodeError, ValueError):
        return None

    if not isinstance(raw_item, ta.Mapping) or raw_item.get('type') != 'reasoning':
        return None
    return raw_item


##


def build_text_signature(raw_item: ta.Mapping[str, ta.Any]) -> str | None:
    raw_id = raw_item.get('id')
    if not isinstance(raw_id, str) or not raw_id:
        return None

    raw_phase = raw_item.get('phase')
    return json.dumps_compact({
        'id': raw_id,
        **({'phase': raw_phase} if isinstance(raw_phase, str) else {}),
    })


def parse_text_signature(s: str | None) -> ta.Mapping[str, ta.Any] | None:
    if not s:
        return None

    try:
        raw_sig = json.loads(s)
    except (json.DecodeError, ValueError):
        return None

    if not isinstance(raw_sig, ta.Mapping) or not isinstance(raw_sig.get('id'), str) or not raw_sig['id']:
        return None
    return raw_sig


##


def build_tool_call_signature(raw_item: ta.Mapping[str, ta.Any]) -> str | None:
    raw_id = raw_item.get('id')
    if not isinstance(raw_id, str) or not raw_id:
        return None

    return json.dumps_compact({'id': raw_id})


def parse_tool_call_signature(s: str | None) -> ta.Mapping[str, ta.Any] | None:
    if not s:
        return None

    try:
        raw_sig = json.loads(s)
    except (json.DecodeError, ValueError):
        return None

    if not isinstance(raw_sig, ta.Mapping) or not isinstance(raw_sig.get('id'), str) or not raw_sig['id']:
        return None
    return raw_sig
