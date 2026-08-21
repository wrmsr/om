"""Query text formatting shared by the sync and async cursors: parameter escaping, mogrification, and bulk insert."""
import re
import typing as ta


##


# Matches an INSERT / REPLACE with a single VALUES row of placeholders, for executemany bulk rewriting.
RE_INSERT_VALUES = re.compile(
    r'\s*((?:INSERT|REPLACE)\b.+\bVALUES?\s*)'
    r'(\(\s*(?:%s|%\([^)]+\)s)\s*(?:,\s*(?:%s|%\([^)]+\)s)\s*)*\))'
    r'(\s*(?:AS\s+(?:`[^`]+`|"[^"]+"|[0-9A-Za-z_$]+)\s*'
    r'(?:\(\s*(?:`[^`]+`|"[^"]+"|[0-9A-Za-z_$]+)\s*'
    r'(?:,\s*(?:`[^`]+`|"[^"]+"|[0-9A-Za-z_$]+)\s*)*\))?\s*)?'
    r'(?:ON DUPLICATE.*)?);?\s*\Z',
    re.IGNORECASE | re.DOTALL,
)


def backquote_escape(s: str) -> str:
    return s.replace('`', '``')


def escape_args(args: ta.Any, escaper: ta.Any) -> ta.Any:
    if isinstance(args, (tuple, list)):
        return tuple(escaper.literal(a) for a in args)
    elif isinstance(args, dict):
        return {k: escaper.literal(v) for k, v in args.items()}
    else:
        return escaper.escape(args)


def mogrify(query: str, args: ta.Any, escaper: ta.Any) -> str:
    if args is not None:
        query = query % escape_args(args, escaper)
    return query
