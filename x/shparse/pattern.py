# Copyright (c) 2016, Daniel Martí. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
#   products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Copyright (c) 2017, Daniel Martí <mvdan@mvdan.cc>
# See LICENSE for licensing information

# Package pattern allows working with shell pattern matching notation, also
# known as wildcards or globbing.
#
# For reference, see
# https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_13.

import io

from omcore import dataclasses as dc


##


# Mode can be used to supply a number of options to the package's functions.
# Not all functions change their behavior with all of the options below.
SHORTEST = 1 << 0           # prefer the shortest match.
FILENAMES = 1 << 1           # "*" and "?" don't match slashes; only "**" does
ENTIRE_STRING = 1 << 2       # match the entire string using ^$ delimiters
NO_GLOB_CASE = 1 << 3        # case-insensitive match ((?i) in the regexp); shopt "nocaseglob"
NO_GLOB_STAR = 1 << 4        # do not support "**"; negated shopt "globstar"
GLOB_LEADING_DOT = 1 << 5    # let wildcards match leading dots in filenames; shopt "dotglob"
EXTENDED_OPERATORS = 1 << 6   # support extended pattern matching operators; shopt "extglob"


_PYTHON_CHAR_CLASSES = {
    'alnum': '0-9A-Za-z',
    'alpha': 'A-Za-z',
    'ascii': r'\x00-\x7f',
    'blank': r'\t ',
    'cntrl': r'\x00-\x1f\x7f',
    'digit': '0-9',
    'graph': r'\x21-\x7e',
    'lower': 'a-z',
    'print': r'\x20-\x7e',
    'punct': r'!-/:-@\[-`{-~',
    'space': r'\t\n\v\f\r ',
    'upper': 'A-Z',
    'word': '0-9A-Z_a-z',
    'xdigit': '0-9A-Fa-f',
}

_REGEXP_META = frozenset(r'\\.+*?()|[]{}^$')


def _quote_regexp(text: str) -> str:
    return ''.join(f'\\{char}' if char in _REGEXP_META else char for char in text)


class PatternSyntaxError(Exception):
    """Raised when a pattern has invalid syntax."""

    def __init__(self, msg: str, err: Exception | None = None) -> None:
        super().__init__(msg)
        self.msg = msg
        self.err = err


# NegExtGlobGroup represents the byte offset range of a single !(expr) group
# within a pattern string. Start is the offset of '!', End is one past ')'.
@dc.dataclass(frozen=True)
class NegExtGlobGroup:
    start: int
    end: int


# NegExtGlobError is returned by Regexp when an extglob negation operator
# !(pattern-list) is encountered, as Go's regexp package does not support
# negative lookahead. Callers can handle this by negating the result of
# matching the inner pattern.
class NegExtGlobError(Exception):
    def __init__(self, groups: list[NegExtGlobGroup]) -> None:
        super().__init__('extglob !(...) is not supported in this scenario')
        self.groups = groups


##


class _StringLexer:
    """Helps tokenize a pattern string."""

    def __init__(self, s: str) -> None:
        self.s = s
        self.i = 0

    def next(self) -> str:
        if self.i >= len(self.s):
            return '\x00'
        c = self.s[self.i]
        self.i += 1
        return c

    def last(self) -> str:
        if self.i < 2:
            return '\x00'
        return self.s[self.i - 2]

    def peek_next(self) -> str:
        if self.i >= len(self.s):
            return '\x00'
        return self.s[self.i]

    def peek_rest(self) -> str:
        return self.s[self.i:]


##


_EOF_SENTINEL = object()


def _regexp_next(sb: io.StringIO, sl: _StringLexer, mode: int) -> object | None:
    """Returns None on success, _EOF_SENTINEL on EOF, or raises on error."""

    c = sl.next()
    if mode & EXTENDED_OPERATORS != 0:
        # Handle extended pattern matching operators separately,
        # given that they can be one of many two-character prefixes.
        # Note that we recurse into the same function in a loop,
        # as each of the patterns in the list separated by '|' is a regular pattern.
        if c in ('!', '?', '*', '+', '@'):
            op = c
            if sl.peek_next() == '(':
                start = sl.i - 1
                group = io.StringIO()
                group.write(sl.next())  # (
                while True:
                    pn = sl.peek_next()
                    if pn == ')':
                        break
                    elif pn == '|':
                        # extended operators support a list of "or" separated expressions
                        group.write(sl.next())
                        continue
                    elif pn == '\x00':
                        # Like Bash, an unclosed group is parsed literally.
                        sl.i = start + 1
                        break
                    result = _regexp_next(group, sl, mode)
                    if result is _EOF_SENTINEL:
                        break
                if sl.peek_next() == ')':
                    group.write(sl.next())  # )
                    sb.write(group.getvalue())
                    if op == '!':
                        byte_start = len(sl.s[:start].encode())
                        byte_end = len(sl.s[:sl.i].encode())
                        raise NegExtGlobError(groups=[NegExtGlobGroup(start=byte_start, end=byte_end)])
                    if op != '@':
                        # @( is GlobOne for matching once; no suffix needed
                        sb.write(op)
                    return None
    if c == '\x00':
        return _EOF_SENTINEL
    elif c == '*':
        if mode & FILENAMES == 0:
            # * - matches anything when not in filename mode
            sb.write('.*')
        else:
            # "**" only acts as globstar if it is alone as a path element.
            single_before = sl.i == 1 or sl.last() == '/'
            handled = False
            if sl.peek_next() == '*':
                sl.i += 1
                single_after = sl.i == len(sl.s) or sl.peek_next() == '/'
                if mode & NO_GLOB_STAR == 0 and single_before and single_after:
                    # ** - match any number of slashes or "*" path elements
                    slash_suffix = sl.peek_next() == '/'
                    if slash_suffix:
                        # **/ - like "**" but requiring a trailing slash when matching
                        sl.i += 1
                        # wrap the expression to ensure that any match has a slash suffix
                        sb.write('(')
                    if mode & GLOB_LEADING_DOT == 0:
                        sb.write('(/|[^/.][^/]*)*')
                    else:
                        # with GlobLeadingDot (dotglob), match anything at all
                        sb.write('.*')
                    if slash_suffix:
                        sb.write('/)?')
                    handled = True
                # else: foo**, **bar, or NoGlobStar - behaves like "*" below
            if not handled:
                # * - matches anything except slashes and leading dots
                if single_before and mode & GLOB_LEADING_DOT == 0:
                    sb.write('([^/.][^/]*)?')
                else:
                    # with GlobLeadingDot (dotglob), match anything except slashes
                    sb.write('[^/]*')
    elif c == '?':
        if mode & FILENAMES != 0:
            sb.write('[^/]')
        else:
            sb.write('.')
    elif c == '\\':
        c2 = sl.next()
        if c2 == '\x00':
            raise PatternSyntaxError(r'\ at end of pattern')
        sb.write(_quote_regexp(c2))
    elif c == '[':
        lit = sl.i
        filenames = mode & FILENAMES != 0
        bracket = io.StringIO()
        bracket.write('[')
        has_slash = False
        deferred_err: PatternSyntaxError | None = None
        class_err: PatternSyntaxError | None = None

        def literal_bracket() -> None:
            sl.i = lit
            sb.write(r'\[')

        c = sl.next()
        if c == '\x00':
            literal_bracket()
            return None
        if c in ('!', '^'):
            bracket.write('^')
            c = sl.next()
            if c == '\x00':
                literal_bracket()
                return None
        if c == ']':
            bracket.write(']')
            c = sl.next()
            if c == '\x00':
                literal_bracket()
                return None
        while True:
            if c == '\x00':
                if class_err is not None:
                    raise class_err
                literal_bracket()
                return None
            elif c == '\\':
                c = sl.next()
                if c == '\x00':
                    continue
                if c == '-':
                    bracket.write(r'\-')
                elif ord(c) > 127:
                    bracket.write(c)
                else:
                    if filenames and c == '/':
                        has_slash = True
                    bracket.write(_quote_regexp(c))
            elif c == '-':
                bracket.write('-')
                range_start = sl.last()
                end = sl.peek_next()
                if end != ']' and range_start > end and deferred_err is None:
                    deferred_err = PatternSyntaxError(f'invalid range: {range_start}-{end}')
            elif c == ']':
                if has_slash:
                    sb.write(_quote_regexp(sl.s[lit - 1:sl.i]))
                    return None
                if deferred_err is not None:
                    raise deferred_err
                bracket.write(']')
                sb.write(bracket.getvalue())
                return None
            elif c == '[':
                rest = sl.peek_rest()
                count, char_class_err = _char_class(rest)
                if char_class_err is not None:
                    if class_err is None:
                        class_err = PatternSyntaxError('charClass invalid', char_class_err)
                    if deferred_err is None:
                        deferred_err = class_err
                if count > 0:
                    bracket.write('[')
                    if filenames and '/' in rest[:count]:
                        has_slash = True
                    bracket.write(rest[:count])
                    sl.i += count
                else:
                    bracket.write(r'\[')
            else:
                if filenames and c == '/':
                    has_slash = True
                bracket.write(c)
            c = sl.next()
    else:
        if ord(c) > 127:
            sb.write(c)
        else:
            sb.write(_quote_regexp(c))
    return None


def _char_class(s: str) -> tuple[int, PatternSyntaxError | None]:
    if s.startswith(('.', '=')):
        sep = f'{s[0]}]'
        end = s.find(sep, 1)
        if end < 0:
            return 0, PatternSyntaxError('collating features not available')
        return end + 2, PatternSyntaxError('collating features not available')
    if not s.startswith(':'):
        return 0, None
    end = s.find(':]', 1)
    if end < 0:
        return 0, PatternSyntaxError('[[: was not matched with a closing :]')
    name = s[1:end]
    consumed = len(name) + 3
    if name not in (
        'alnum', 'alpha', 'ascii', 'blank', 'cntrl', 'digit', 'graph',
        'lower', 'print', 'punct', 'space', 'upper', 'word', 'xdigit',
    ):
        return consumed, PatternSyntaxError(f'invalid character class: {name!r}')
    return consumed, None


def _shortest_regexp(expression: str) -> str:
    result = io.StringIO()
    prefix_end = expression.find(')') + 1
    result.write(expression[:prefix_end])
    in_class = False
    escaped = False
    for char in expression[prefix_end:]:
        result.write(char)
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == '[':
            in_class = True
        elif char == ']':
            in_class = False
        elif not in_class and char in ('*', '+', '?'):
            result.write('?')
    return result.getvalue()


def _replace_posix_classes(expression: str) -> str:
    result = io.StringIO()
    i = 0
    in_bracket = False
    bracket_chars = 0
    while i < len(expression):
        escaped = False
        if expression[i] in ('[', ']'):
            backslashes = 0
            j = i - 1
            while j >= 0 and expression[j] == '\\':
                backslashes += 1
                j -= 1
            escaped = backslashes % 2 == 1
        if expression[i] == '[' and not escaped:
            if in_bracket and i + 1 < len(expression) and expression[i + 1] == ':':
                end = expression.find(':]', i + 2)
                if end >= 0:
                    name = expression[i + 2:end]
                    replacement = _PYTHON_CHAR_CLASSES.get(name)
                    if replacement is not None:
                        result.write(replacement)
                        i = end + 2
                        bracket_chars += 1
                        continue
            elif in_bracket:
                result.write(r'\[')
                bracket_chars += 1
                i += 1
                continue
            else:
                in_bracket = True
                bracket_chars = 0
        elif expression[i] == ']' and not escaped and in_bracket and bracket_chars > 0:
            in_bracket = False
        result.write(expression[i])
        if in_bracket and expression[i] != '[':
            bracket_chars += 1
        i += 1
    return result.getvalue()


# Regexp turns a shell pattern into a regular expression that can be used with
# re.compile. It will raise an error if the input pattern was incorrect.
# Otherwise, the returned expression can be passed to re.compile.
#
# For example, regexp('foo*bar?', 0) returns 'foo.*bar.'.
#
# Note that this function (and quote_meta) should not be directly used with file
# paths if Windows is supported, as the path separator on that platform is the
# same character as the escaping character for shell patterns.
def regexp(pat: str, mode: int) -> str:
    # If there are no special pattern matching or regular expression characters,
    # and we don't need to insert extras for the modes affecting non-special characters,
    # we can directly return the input string as a short-cut.
    if mode & (ENTIRE_STRING | NO_GLOB_CASE) == 0:
        needs_escaping = False
        for r in pat:
            if r in ('*', '?', '[', '\\', '.', '+', '(', ')', '|',
                      ']', '{', '}', '^', '$'):
                # including those that need escaping since they are
                # regular expression metacharacters
                needs_escaping = True
                break
        if not needs_escaping:
            return pat
    sb = io.StringIO()
    # Enable matching `\n` with the `.` metacharacter as globs match `\n`
    sb.write('(?s')
    if mode & NO_GLOB_CASE != 0:
        sb.write('i')
    # Note: Go's regexp.Shortest flag (?U) has no direct Python equivalent;
    # Python uses *? for non-greedy. We skip writing 'U' as Python re doesn't support it.
    sb.write(')')
    if mode & ENTIRE_STRING != 0:
        sb.write('^')
    sl = _StringLexer(s=pat)
    neg_groups: list[NegExtGlobGroup] = []
    while True:
        try:
            result = _regexp_next(sb, sl, mode)
        except NegExtGlobError as e:
            neg_groups.extend(e.groups)
            continue
        if result is _EOF_SENTINEL:
            break
    if len(neg_groups) > 0:
        raise NegExtGlobError(groups=neg_groups)
    if mode & ENTIRE_STRING != 0:
        sb.write('$')
    expression = sb.getvalue()
    expression = _replace_posix_classes(expression)
    expression = expression.replace('[[]', r'[\[]')
    if mode & SHORTEST != 0:
        expression = _shortest_regexp(expression)
    return expression


# HasMeta returns whether a string contains any unescaped pattern
# metacharacters: '*', '?', or '['. When the function returns false, the given
# pattern can only match at most one string.
#
# For example, has_meta(r'foo\*bar') returns False, but has_meta('foo*bar')
# returns True.
#
# This can be useful to avoid extra work, like regexp. Note that this
# function cannot be used to avoid quote_meta, as backslashes are quoted by
# that function but ignored here.
#
# The mode parameter is unused, and will be removed in v4.
def has_meta(pat: str, mode: int = 0) -> bool:
    open_bracket = False
    i = 0
    while i < len(pat):
        c = pat[i]
        if c == '\\':
            i += 1
        elif c in ('*', '?'):
            return True
        elif c == '[':
            open_bracket = True
        elif c == ']' and open_bracket:
            return True
        i += 1
    return False


# QuoteMeta returns a string that quotes all pattern metacharacters in the
# given text. The returned string is a pattern that matches the literal text.
#
# For example, quote_meta('foo*bar?') returns r'foo\*bar\?'.
#
# The mode parameter is unused, and will be removed in v4.
def quote_meta(pat: str, mode: int = 0) -> str:
    needs_escaping = False
    for r in pat:
        if r in ('*', '?', '[', '\\'):
            needs_escaping = True
            break
    if not needs_escaping:  # short-cut without a string copy
        return pat
    sb = io.StringIO()
    for r in pat:
        if r in ('*', '?', '[', '\\'):
            sb.write('\\')
        sb.write(r)
    return sb.getvalue()
