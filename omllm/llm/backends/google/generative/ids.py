import uuid


##


# Gemini requires thought signatures issued on functionCall parts to be echoed back with those parts on replay, and
# rejects tool-calling requests whose history lacks them. Tool call ids are the only field round-tripped through the
# message types - and google does not always issue ids itself, so they may be locally fabricated anyway - so signatures
# are smuggled through them. The separator appears in neither base64(url) signatures, google-issued ids, nor uuids.
_THOUGHT_SIGNATURE_SEP = '~'


def join_tool_call_id(raw_id: str | None, thought_signature: str | None) -> str:
    if not raw_id:
        raw_id = str(uuid.uuid4())

    if thought_signature:
        return f'{raw_id}{_THOUGHT_SIGNATURE_SEP}{thought_signature}'

    return raw_id


def split_tool_call_id(tool_call_id: str) -> tuple[str, str | None]:
    raw_id, sep, thought_signature = tool_call_id.partition(_THOUGHT_SIGNATURE_SEP)
    return (raw_id, thought_signature if sep else None)
