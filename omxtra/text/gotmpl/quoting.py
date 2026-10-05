"""Go-compatible string quoting shared by lexer, parse nodes, and formatting."""


def quote_go_string(value: str) -> str:
    """Return the usual double-quoted Go representation of a string."""

    out = ['"']
    escapes = {
        '\a': r'\a',
        '\b': r'\b',
        '\f': r'\f',
        '\n': r'\n',
        '\r': r'\r',
        '\t': r'\t',
        '\v': r'\v',
        '"': r'\"',
        '\\': r'\\',
    }
    for char in value:
        if (escaped := escapes.get(char)) is not None:
            out.append(escaped)
        elif char.isprintable():
            out.append(char)
        elif ord(char) < 0x100:
            out.append(f'\\x{ord(char):02x}')
        elif ord(char) < 0x10000:
            out.append(f'\\u{ord(char):04x}')
        else:
            out.append(f'\\U{ord(char):08x}')
    out.append('"')
    return ''.join(out)


def quote_go_string_or_raw(value: str) -> str:
    """Return Go's alternate-form quoted string, preferring a raw literal."""

    if (
        '`' not in value
        and '\r' not in value
        and all(char == '\t' or (char.isprintable() and char != '\ufeff') for char in value)
    ):
        return f'`{value}`'
    return quote_go_string(value)


def quote_go_rune(value: str) -> str:
    """Return the single-quoted Go representation of one Unicode code point."""

    if len(value) != 1:
        return quote_go_string(value)
    escapes = {
        '\a': r'\a',
        '\b': r'\b',
        '\f': r'\f',
        '\n': r'\n',
        '\r': r'\r',
        '\t': r'\t',
        '\v': r'\v',
        "'": r"\'",
        '\\': r'\\',
    }
    if (escaped := escapes.get(value)) is not None:
        return f"'{escaped}'"
    if value.isprintable():
        return f"'{value}'"
    if ord(value) < 0x100:
        return f"'\\x{ord(value):02x}'"
    if ord(value) < 0x10000:
        return f"'\\u{ord(value):04x}'"
    return f"'\\U{ord(value):08x}'"
