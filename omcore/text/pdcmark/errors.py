"""
Exception hierarchy.

Deliberately small: resource bounds (nesting depth, link-ref expansion fuel, paren nesting) degrade gracefully - deeper
input parses as plain content - rather than raising.
"""


##


class PdcmarkError(Exception):
    pass


class ParserStateError(PdcmarkError):
    """Raised when the parser is used incorrectly - e.g. `feed()` after `finish()`."""
