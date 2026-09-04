def ascii_control_repr(c: str) -> str | None:
    """Caret notation for ascii control characters ('^A', '^?'), or None for printable characters."""

    code = ord(c)
    if code < 32:
        return '^' + chr(code + 64)
    if code == 127:
        return '^?'
    return None
