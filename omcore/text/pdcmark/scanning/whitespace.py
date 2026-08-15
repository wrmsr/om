"""
Whitespace / EOL / character-class helpers.

Direct ports of the small scanners at the bottom of pulldown-cmark/src/scanners.rs, adapted to work on `str` rather than
`&[u8]`. For pure-ASCII control characters (which is what these test) the operation is identical.

Convention: where pulldown-cmark uses byte indices into `&[u8]`, we use character indices into `str`. For ASCII-only
content the two coincide; for inputs containing non-ASCII characters the character index is what naturally indexes a
Python `str`.
"""


##


# pulldown-cmark/src/scanners.rs::is_ascii_whitespace_no_nl
def is_ascii_whitespace_no_nl(c: str) -> bool:
    return c in ' \t\v\f'


def is_ascii_punctuation(c: str) -> bool:
    return c in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'


def is_ascii_alphanumeric(c: str) -> bool:
    return c.isascii() and c.isalnum()


# pulldown-cmark/src/scanners.rs::scan_ch_repeat
def scan_ch_repeat(s: str, i: int, c: str) -> int:
    """Count of repeated `c` at `s[i:]`."""

    j = i
    n = len(s)
    while j < n and s[j] == c:
        j += 1
    return j - i


def is_blank_line(line: str) -> bool:
    """True if `line` (which does not contain a trailing newline) is empty or all-whitespace."""

    return not line.strip(' \t\v\f')
