# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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
