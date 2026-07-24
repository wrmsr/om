from ....types.messages import StopReason


##


def translate_stop_reason(s: str) -> StopReason:
    if s == 'STOP':
        # Google reports STOP even on tool-calling turns - callers must structurally override this to 'tool_use' when
        # function call parts are present.
        return 'stop'

    elif s == 'MAX_TOKENS':
        return 'length'

    elif s in (
            'SAFETY',
            'RECITATION',
            'LANGUAGE',
            'BLOCKLIST',
            'PROHIBITED_CONTENT',
            'SPII',
            'IMAGE_SAFETY',
            'OTHER',
            'MALFORMED_FUNCTION_CALL',
            'UNEXPECTED_TOOL_CALL',
            'TOO_MANY_TOOL_CALLS',
    ):
        return 'error'

    else:
        raise ValueError(s)
