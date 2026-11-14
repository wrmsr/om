"""What the function call format needs to know of a parameter's JSON schema, shared by its grammar and its parsers."""
import typing as ta


##


def schema_takes_text(schema: ta.Any) -> bool:
    """
    Whether a parameter of this schema is written as raw text in the function format: a string is, and so is anything
    that may be one (no type, a union with string) -- JSON text is text too.
    """

    if not isinstance(schema, dict):
        return True
    if 'const' in schema:
        return isinstance(schema['const'], str)
    if 'enum' in schema:
        return any(isinstance(v, str) for v in schema['enum'])
    alts = schema.get('anyOf') or schema.get('oneOf')
    if alts:
        return any(schema_takes_text(a) for a in alts)
    t = schema.get('type')
    if t is None:
        return True
    return 'string' in t if isinstance(t, list) else t == 'string'


def schema_only_text(schema: ta.Any) -> bool:
    """Whether the schema admits nothing but strings, so a parameter's raw text is its value whatever it looks like."""

    if not isinstance(schema, dict):
        return False
    if 'const' in schema:
        return isinstance(schema['const'], str)
    if 'enum' in schema:
        return all(isinstance(v, str) for v in schema['enum'])
    alts = schema.get('anyOf') or schema.get('oneOf')
    if alts:
        return all(schema_only_text(a) for a in alts)
    t = schema.get('type')
    return t == 'string' or t == ['string']


def schema_allows_type(schema: ta.Any, name: str) -> bool:
    """Whether a JSON type is among those the schema names (at its top level, or in a union's alternatives)."""

    if not isinstance(schema, dict):
        return False
    alts = schema.get('anyOf') or schema.get('oneOf')
    if alts:
        return any(schema_allows_type(a, name) for a in alts)
    t = schema.get('type')
    return name in t if isinstance(t, list) else t == name
