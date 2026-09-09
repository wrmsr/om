# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
A parser and path filter for gitignore files.

Gitignore content is parsed into a small dataclass IR - a sequence of lines, each blank, a comment, a pattern, or
invalid - and patterns are matched against slash-separated paths relative to the directory of the gitignore file they
came from. Semantics follow git's own implementation (dir.c and wildmatch.c) as closely as is practical, including in
the corners its documentation leaves unspecified. See:

 - https://git-scm.com/docs/gitignore
 - https://github.com/git/git/blob/master/dir.c
 - https://github.com/git/git/blob/master/wildmatch.c

Pattern format:

 - A blank line matches nothing. A line starting with `#` is a comment. Trailing spaces - but not tabs - are trimmed
   unless escaped with a backslash.
 - A leading `!` negates the pattern, re-including a path excluded by an earlier pattern. A path can not be re-included
   if one of its parent directories is excluded, as git never descends into excluded directories.
 - A trailing `/` restricts the pattern to directories.
 - A `/` at the beginning or in the middle of the pattern anchors it to the gitignore's directory. A pattern with no
   such slash is matched against the path's basename alone, and so matches at any depth.
 - `*` matches any run of characters not containing a `/`, `?` matches any single character other than `/`, and a
   bracket expression like `[abc]`, `[a-z]`, `[!abc]`, or `[[:alpha:]]` matches any single character in it other than
   `/`.
 - A `**` alone between slashes, or at the beginning or end of the pattern, matches zero or more directories - except
   at the end of a pattern, where it matches everything inside the preceding directory but not that directory itself.
   Consecutive asterisks anywhere else are equivalent to a single `*`.
 - A backslash escapes the following character.

Deviations from and notes on git's behavior:

 - Matching operates on str code points rather than on utf-8 bytes, so `?` and bracket expressions consume a whole
   character rather than a single byte of a multibyte one.
 - Matching is always case sensitive - `core.ignorecase` is not honored.
 - Git's own non-wildcard-prefix optimization causes a run of asterisks immediately following the literal prefix of an
   anchored pattern - as in `a**/b` or `a/b**` - to unintentionally match across directories. Such runs are treated
   here as its documentation describes: as a single `*`.
 - Git silently accepts patterns which can never match anything due to a trailing backslash, an unterminated bracket
   expression, or an unknown `[:name:]` class. These are parsed as GitignoreInvalidLine's - which likewise never match -
   rather than as patterns, and are rejected outright in strict mode.
"""
import dataclasses as dc
import string
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.check import check


##


class GitignoreError(Exception):
    pass


class GitignorePatternError(GitignoreError):
    """Raised for a pattern which git would silently accept but which can never match - see the module docstring."""

    def __init__(self, message: str, pattern: str, *, line_no: ta.Optional[int] = None) -> None:
        super().__init__(message, pattern, line_no)

        self.message = message
        self.pattern = pattern
        self.line_no = line_no

    def __str__(self) -> str:
        return ''.join([
            f'line {self.line_no}: ' if self.line_no is not None else '',
            f'{self.message}: {self.pattern!r}',
        ])


class GitignorePathError(GitignoreError):
    """Raised for a path which is not relative, slash-separated, and normalized - see split_gitignore_path."""

    def __init__(self, message: str, path: str) -> None:
        super().__init__(message, path)

        self.message = message
        self.path = path

    def __str__(self) -> str:
        return f'{self.message}: {self.path!r}'


##
# Glob IR


# The `[:name:]` classes accepted in bracket expressions. Git's wildmatch implements these with ascii-only ctype
# predicates, so they are ascii-only here too.
GITIGNORE_GLOB_CHAR_CLASSES: ta.Mapping[str, ta.FrozenSet[str]] = {
    'alnum': frozenset(string.ascii_letters + string.digits),
    'alpha': frozenset(string.ascii_letters),
    'blank': frozenset(' \t'),
    'cntrl': frozenset(map(chr, range(0x20))) | frozenset('\x7f'),
    'digit': frozenset(string.digits),
    'graph': frozenset(map(chr, range(0x21, 0x7f))),
    'lower': frozenset(string.ascii_lowercase),
    'print': frozenset(map(chr, range(0x20, 0x7f))),
    'punct': frozenset(string.punctuation),
    'space': frozenset(string.whitespace),
    'upper': frozenset(string.ascii_uppercase),
    'xdigit': frozenset(string.hexdigits),
}


class GitignoreGlobPart(Abstract):
    """An element of a glob, which is matched against a single path component."""


@dc.dataclass(frozen=True)
class GitignoreGlobLiteral(GitignoreGlobPart):
    """
    A run of literal characters, with any backslash escapes already resolved. Never contains a slash: as an escaped
    slash can only ever match a real one it separates segments just as an unescaped one does.
    """

    text: str

    def __post_init__(self) -> None:
        check.non_empty_str(self.text)
        check.arg('/' not in self.text)


@dc.dataclass(frozen=True)
class GitignoreGlobStar(GitignoreGlobPart):
    """A `*`, matching zero or more characters. The parser collapses consecutive asterisks into one of these."""


@dc.dataclass(frozen=True)
class GitignoreGlobQuestionMark(GitignoreGlobPart):
    """A `?`, matching exactly one character."""


@dc.dataclass(frozen=True)
class GitignoreGlobCharClass(GitignoreGlobPart):
    """
    A bracket expression, matching exactly one character. A `/` may be listed in one but, as path components never
    contain one, can never match.
    """

    class Item(Abstract):
        pass

    @dc.dataclass(frozen=True)
    class Char(Item):
        c: str

        def __post_init__(self) -> None:
            check.arg(len(self.c) == 1)

    @dc.dataclass(frozen=True)
    class Range(Item):
        """An inclusive range. A range whose `lo` is greater than its `hi` matches nothing, as in git."""

        lo: str
        hi: str

        def __post_init__(self) -> None:
            check.arg(len(self.lo) == 1)
            check.arg(len(self.hi) == 1)

    @dc.dataclass(frozen=True)
    class Named(Item):
        """A posix-style `[:name:]` class - one of the keys of GITIGNORE_GLOB_CHAR_CLASSES."""

        name: str

        def __post_init__(self) -> None:
            check.in_(self.name, GITIGNORE_GLOB_CHAR_CLASSES)

    items: ta.Sequence[Item]
    negated: bool = False


##
# Segment IR


class GitignoreSegment(Abstract):
    """A slash-delimited portion of a pattern."""


@dc.dataclass(frozen=True)
class GitignoreGlobSegment(GitignoreSegment):
    """
    A glob, matched against exactly one path component. An empty glob - from an empty pattern, or from an empty portion
    of one like the middle of `a//b` - can only match an empty component, and so never matches.
    """

    parts: ta.Sequence[GitignoreGlobPart]


@dc.dataclass(frozen=True)
class GitignoreDoubleStarSegment(GitignoreSegment):
    """
    A `**` (or longer run of asterisks) alone between slashes. Matches zero or more path components, except as the last
    segment of a pattern where it matches one or more: `a/**` matches everything inside `a`, but not `a` itself.
    """


##
# Pattern IR


@dc.dataclass(frozen=True)
class GitignorePattern:
    """
    A parsed pattern. The segments of an anchored pattern - one written with a leading or interior slash - are matched
    against a path's components starting from the directory of the gitignore file. An unanchored pattern has exactly
    one segment, which is matched against a path's basename alone, and so matches at any depth.
    """

    segments: ta.Sequence[GitignoreSegment]

    negated: bool = False
    anchored: bool = False
    dir_only: bool = False

    def __post_init__(self) -> None:
        check.not_empty(self.segments)
        if not self.anchored:
            check.arg(len(self.segments) == 1)


##
# Line IR


@dc.dataclass(frozen=True)
class GitignoreLine(Abstract):
    line_no: int
    raw: str

    def __post_init__(self) -> None:
        check.arg(self.line_no >= 1)
        check.arg('\n' not in self.raw)


@dc.dataclass(frozen=True)
class GitignoreBlankLine(GitignoreLine):
    def __post_init__(self) -> None:
        super().__post_init__()

        check.arg(not self.raw)


@dc.dataclass(frozen=True)
class GitignoreCommentLine(GitignoreLine):
    def __post_init__(self) -> None:
        super().__post_init__()

        check.arg(self.raw.startswith('#'))

    @property
    def text(self) -> str:
        return self.raw[1:]


@dc.dataclass(frozen=True)
class GitignorePatternLine(GitignoreLine):
    pattern: GitignorePattern


@dc.dataclass(frozen=True)
class GitignoreInvalidLine(GitignoreLine):
    """A line git would accept as a pattern but which can never match - see GitignorePatternError."""

    message: str


@dc.dataclass(frozen=True)
class GitignoreFile:
    lines: ta.Sequence[GitignoreLine]

    @property
    def patterns(self) -> ta.Sequence[GitignorePattern]:
        return [l.pattern for l in self.lines if isinstance(l, GitignorePatternLine)]


##
# Parsing


class GitignoreParser:
    """
    Parses gitignore content into its IR, mirroring git's own reading of pattern files: `parse_pattern` corresponds to
    dir.c's `parse_path_pattern`, `parse_line` to the per-line handling of its `add_patterns_from_buffer`, and `parse`
    to that function as a whole.
    """

    def __init__(self, *, strict: bool = False) -> None:
        super().__init__()

        self._strict = strict

    #

    def _parse_char_class(self, s: str, i: int) -> ta.Tuple[GitignoreGlobCharClass, int]:
        """Parses the bracket expression whose `[` is at `s[i - 1]`, returning it and the index following its `]`."""

        n = len(s)

        negated = False
        if i < n and s[i] in '!^':
            negated = True
            i += 1

        items: ta.List[GitignoreGlobCharClass.Item] = []

        # The first character of an expression is always taken as a member, so `[]]` and `[!]]` are well formed.
        first = True

        while True:
            if i >= n:
                raise GitignorePatternError('unterminated bracket expression', s)

            c = s[i]

            if c == ']' and not first:
                return GitignoreGlobCharClass(tuple(items), negated=negated), i + 1

            first = False

            if c == '\\':
                if i + 1 >= n:
                    raise GitignorePatternError('unterminated bracket expression', s)

                items.append(GitignoreGlobCharClass.Char(s[i + 1]))
                i += 2

            elif (
                    c == '-' and
                    items and
                    isinstance(items[-1], GitignoreGlobCharClass.Char) and
                    i + 1 < n and
                    s[i + 1] != ']'
            ):
                # A `-` only denotes a range when both immediately preceded by a plain character and followed by
                # something other than the closing `]` - so `[a-]`, `[-a]`, and the second `-` of `[a-c-e]` are all
                # literal members.
                lo = check.isinstance(items.pop(), GitignoreGlobCharClass.Char).c

                i += 1
                hi = s[i]
                if hi == '\\':
                    i += 1
                    if i >= n:
                        raise GitignorePatternError('unterminated bracket expression', s)
                    hi = s[i]

                items.append(GitignoreGlobCharClass.Range(lo, hi))
                i += 1

            elif c == '[' and s.startswith('[:', i):
                # A `[:name:]` class extends to the first `]`, and requires a `:` immediately before it - otherwise
                # the `[` is just a literal member, and parsing resumes at the `:` following it.
                j = s.find(']', i + 2)
                if j < 0:
                    raise GitignorePatternError('unterminated bracket expression', s)

                if j == i + 2 or s[j - 1] != ':':
                    items.append(GitignoreGlobCharClass.Char('['))
                    i += 1

                else:
                    name = s[i + 2:j - 1]
                    if name not in GITIGNORE_GLOB_CHAR_CLASSES:
                        raise GitignorePatternError(f'unknown character class {name!r}', s)

                    items.append(GitignoreGlobCharClass.Named(name))
                    i = j + 1

            else:
                items.append(GitignoreGlobCharClass.Char(c))
                i += 1

    def _tokenize_segments(self, s: str) -> ta.List[ta.List[GitignoreGlobPart]]:
        """
        Splits a pattern body on its separating slashes and tokenizes each of the resulting segments into
        single-character literals and wildcards, from which `_build_segment` then makes proper segments.
        """

        segments: ta.List[ta.List[GitignoreGlobPart]] = [[]]

        i = 0
        n = len(s)
        while i < n:
            c = s[i]

            if c == '/':
                segments.append([])
                i += 1

            elif c == '\\':
                if i + 1 >= n:
                    raise GitignorePatternError('trailing backslash', s)

                e = s[i + 1]
                if e == '/':
                    # An escaped slash can only ever match a real one - see GitignoreGlobLiteral.
                    segments.append([])
                else:
                    segments[-1].append(GitignoreGlobLiteral(e))
                i += 2

            elif c == '*':
                segments[-1].append(GitignoreGlobStar())
                i += 1

            elif c == '?':
                segments[-1].append(GitignoreGlobQuestionMark())
                i += 1

            elif c == '[':
                cc, i = self._parse_char_class(s, i + 1)
                segments[-1].append(cc)

            else:
                segments[-1].append(GitignoreGlobLiteral(c))
                i += 1

        return segments

    def _build_segment(self, tokens: ta.Sequence[GitignoreGlobPart]) -> GitignoreSegment:
        if len(tokens) >= 2 and all(isinstance(t, GitignoreGlobStar) for t in tokens):
            return GitignoreDoubleStarSegment()

        parts: ta.List[GitignoreGlobPart] = []
        for t in tokens:
            last = parts[-1] if parts else None

            if isinstance(t, GitignoreGlobLiteral) and isinstance(last, GitignoreGlobLiteral):
                parts[-1] = GitignoreGlobLiteral(last.text + t.text)

            elif isinstance(t, GitignoreGlobStar) and isinstance(last, GitignoreGlobStar):
                pass

            else:
                parts.append(t)

        return GitignoreGlobSegment(tuple(parts))

    def parse_pattern(self, s: str) -> GitignorePattern:
        """
        Parses a single pattern as git's `parse_path_pattern` does. Comment and blank line handling and the trimming of
        trailing spaces are the concern of `parse_line`, not this.
        """

        body = s

        negated = False
        if body.startswith('!'):  # noqa: FURB188
            negated = True
            body = body[1:]

        dir_only = False
        if body.endswith('/'):  # noqa: FURB188
            dir_only = True
            body = body[:-1]

        # Any remaining slash anchors the pattern - even one escaped or inside a bracket expression, exactly as in git.
        anchored = '/' in body
        if body.startswith('/'):  # noqa: FURB188
            body = body[1:]

        try:
            segments = tuple(self._build_segment(ts) for ts in self._tokenize_segments(body))
        except GitignorePatternError as e:
            raise GitignorePatternError(e.message, s) from None

        return GitignorePattern(
            segments,
            negated=negated,
            anchored=anchored,
            dir_only=dir_only,
        )

    #

    def _trim_trailing_spaces(self, s: str) -> str:
        """
        Trims unescaped trailing spaces - and only spaces - as git's `trim_trailing_spaces` does, including its quirk
        of trimming nothing at all from a line ending in a lone backslash.
        """

        last_space: ta.Optional[int] = None

        i = 0
        n = len(s)
        while i < n:
            c = s[i]

            if c == ' ':
                if last_space is None:
                    last_space = i

            elif c == '\\':
                i += 1
                if i >= n:
                    return s
                last_space = None

            else:
                last_space = None

            i += 1

        return s[:last_space] if last_space is not None else s

    def parse_line(self, raw: str, *, line_no: int) -> GitignoreLine:
        """Parses a single line of a gitignore file, sans its line feed. A trailing carriage return is discarded."""

        if raw.endswith('\r'):  # noqa: FURB188
            raw = raw[:-1]

        if not raw:
            return GitignoreBlankLine(line_no, raw)

        if raw.startswith('#'):
            return GitignoreCommentLine(line_no, raw)

        try:
            pattern = self.parse_pattern(self._trim_trailing_spaces(raw))
        except GitignorePatternError as e:
            if self._strict:
                raise GitignorePatternError(e.message, raw, line_no=line_no) from e
            return GitignoreInvalidLine(line_no, raw, e.message)

        return GitignorePatternLine(line_no, raw, pattern)

    def parse(self, text: str) -> GitignoreFile:
        if text.startswith('\ufeff'):  # noqa: FURB188
            text = text[1:]

        # Git splits only on line feeds - unlike str.splitlines - and reads a file as though it always ended with one.
        raws = text.split('\n')
        if raws[-1] == '':
            raws.pop()

        return GitignoreFile(tuple(
            self.parse_line(raw, line_no=line_no)
            for line_no, raw in enumerate(raws, 1)
        ))


##
# Matching


def split_gitignore_path(path: str) -> ta.List[str]:
    """
    Splits a path into its components, requiring it to be relative, slash-separated, and normalized - with no leading,
    trailing, or repeated slashes and no `.` or `..` components - as the paths git handles always are.
    """

    if not path:
        raise GitignorePathError('empty path', path)

    components = path.split('/')
    for c in components:
        if not c:
            raise GitignorePathError('empty path component', path)
        if c in ('.', '..'):
            raise GitignorePathError('dot path component', path)

    return components


class GitignorePatternMatcher:
    """
    Matches a single pattern against paths relative to the directory of its gitignore file. This is solely the matching
    of a pattern against a path in isolation - the interplay of multiple patterns, and of a path with its excluded
    parent directories, is the concern of GitignoreFilter.
    """

    def __init__(self, pattern: GitignorePattern) -> None:
        super().__init__()

        self._pattern = pattern

    @property
    def pattern(self) -> GitignorePattern:
        return self._pattern

    #

    def _match_char_class(self, cc: GitignoreGlobCharClass, c: str) -> bool:
        matched = False

        for item in cc.items:
            if isinstance(item, GitignoreGlobCharClass.Char):
                matched = c == item.c

            elif isinstance(item, GitignoreGlobCharClass.Range):
                matched = item.lo <= c <= item.hi

            elif isinstance(item, GitignoreGlobCharClass.Named):
                matched = c in GITIGNORE_GLOB_CHAR_CLASSES[item.name]

            else:
                raise TypeError(item)

            if matched:
                break

        return matched != cc.negated

    def _match_glob_from(self, parts: ta.Sequence[GitignoreGlobPart], pi: int, s: str, si: int) -> bool:
        while pi < len(parts):
            part = parts[pi]

            if isinstance(part, GitignoreGlobLiteral):
                if not s.startswith(part.text, si):
                    return False
                si += len(part.text)

            elif isinstance(part, GitignoreGlobQuestionMark):
                if si >= len(s):
                    return False
                si += 1

            elif isinstance(part, GitignoreGlobCharClass):
                if si >= len(s) or not self._match_char_class(part, s[si]):
                    return False
                si += 1

            elif isinstance(part, GitignoreGlobStar):
                if pi + 1 == len(parts):
                    return True

                # Otherwise try every possible length of the star's match, backtracking on failure.
                return any(
                    self._match_glob_from(parts, pi + 1, s, k)
                    for k in range(si, len(s) + 1)
                )

            else:
                raise TypeError(part)

            pi += 1

        return si == len(s)

    def _match_glob(self, parts: ta.Sequence[GitignoreGlobPart], component: str) -> bool:
        return self._match_glob_from(parts, 0, component, 0)

    def _match_segments_from(
            self,
            segments: ta.Sequence[GitignoreSegment],
            si: int,
            components: ta.Sequence[str],
            ci: int,
    ) -> bool:
        while si < len(segments):
            segment = segments[si]

            if isinstance(segment, GitignoreGlobSegment):
                if ci >= len(components) or not self._match_glob(segment.parts, components[ci]):
                    return False
                ci += 1

            elif isinstance(segment, GitignoreDoubleStarSegment):
                if si + 1 == len(segments):
                    return ci < len(components)

                # Otherwise try every possible number of components for the double star to match, backtracking on
                # failure.
                return any(
                    self._match_segments_from(segments, si + 1, components, k)
                    for k in range(ci, len(components) + 1)
                )

            else:
                raise TypeError(segment)

            si += 1

        return ci == len(components)

    #

    def matches_components(self, components: ta.Sequence[str], *, is_dir: bool = False) -> bool:
        p = self._pattern

        if p.dir_only and not is_dir:
            return False

        if not p.anchored:
            segment = check.single(p.segments)

            if isinstance(segment, GitignoreDoubleStarSegment):
                # Outside of an anchored pattern a `**` has no special meaning, and is just a `*`.
                return True

            return self._match_glob(check.isinstance(segment, GitignoreGlobSegment).parts, components[-1])

        return self._match_segments_from(p.segments, 0, components, 0)

    def matches(self, path: str, *, is_dir: bool = False) -> bool:
        return self.matches_components(split_gitignore_path(path), is_dir=is_dir)


##
# Filtering


@dc.dataclass(frozen=True)
class GitignoreMatch:
    """
    The pattern deciding a path's fate: the last pattern matching either the path itself or - taking precedence - the
    shallowest of its parent directories to be excluded, along with which of those it was that matched.
    """

    pattern: GitignorePattern
    path: str
    is_dir: bool

    @property
    def ignored(self) -> bool:
        return not self.pattern.negated


class GitignoreFilter:
    """
    Applies a sequence of patterns with git's semantics: the last matching pattern wins, and a path with an excluded
    parent directory is itself excluded regardless of any negating pattern, as git never descends into excluded
    directories.
    """

    def __init__(self, patterns: ta.Iterable[GitignorePattern]) -> None:
        super().__init__()

        self._patterns: ta.Sequence[GitignorePattern] = tuple(patterns)
        self._matchers = [GitignorePatternMatcher(p) for p in self._patterns]

    @property
    def patterns(self) -> ta.Sequence[GitignorePattern]:
        return self._patterns

    #

    def _last_matching_pattern(
            self,
            components: ta.Sequence[str],
            *,
            is_dir: bool,
    ) -> ta.Optional[GitignorePattern]:
        for m in reversed(self._matchers):
            if m.matches_components(components, is_dir=is_dir):
                return m.pattern
        return None

    def match(self, path: str, *, is_dir: bool = False) -> ta.Optional[GitignoreMatch]:
        components = split_gitignore_path(path)

        for i in range(1, len(components)):
            parent = components[:i]
            pattern = self._last_matching_pattern(parent, is_dir=True)
            if pattern is not None and not pattern.negated:
                return GitignoreMatch(pattern, '/'.join(parent), is_dir=True)

        pattern = self._last_matching_pattern(components, is_dir=is_dir)
        if pattern is None:
            return None

        return GitignoreMatch(pattern, path, is_dir=is_dir)

    def is_ignored(self, path: str, *, is_dir: bool = False) -> bool:
        m = self.match(path, is_dir=is_dir)
        return m is not None and m.ignored

    def filter_paths(
            self,
            paths: ta.Iterable[str],
            *,
            is_dir: ta.Optional[ta.Callable[[str], bool]] = None,
    ) -> ta.Iterator[str]:
        """Yields the given paths which are not ignored, each taken to be a file unless `is_dir` says otherwise."""

        for path in paths:
            if not self.is_ignored(path, is_dir=is_dir(path) if is_dir is not None else False):
                yield path


##


def parse_gitignore_pattern(s: str) -> GitignorePattern:
    return GitignoreParser().parse_pattern(s)


def parse_gitignore(text: str, *, strict: bool = False) -> GitignoreFile:
    return GitignoreParser(strict=strict).parse(text)
