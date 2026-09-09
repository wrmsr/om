# ruff: noqa: PT009 UP006 UP007 UP045
# @om-lite
import os
import os.path
import shutil
import subprocess
import tempfile
import typing as ta
import unittest

from ..ignore import GITIGNORE_GLOB_CHAR_CLASSES
from ..ignore import GitignoreBlankLine
from ..ignore import GitignoreCommentLine
from ..ignore import GitignoreDoubleStarSegment
from ..ignore import GitignoreFilter
from ..ignore import GitignoreGlobCharClass
from ..ignore import GitignoreGlobLiteral
from ..ignore import GitignoreGlobPart
from ..ignore import GitignoreGlobQuestionMark
from ..ignore import GitignoreGlobSegment
from ..ignore import GitignoreGlobStar
from ..ignore import GitignoreInvalidLine
from ..ignore import GitignoreLine
from ..ignore import GitignoreMatch
from ..ignore import GitignorePathError
from ..ignore import GitignorePattern
from ..ignore import GitignorePatternError
from ..ignore import GitignorePatternLine
from ..ignore import GitignorePatternMatcher
from ..ignore import parse_gitignore
from ..ignore import parse_gitignore_pattern
from ..ignore import split_gitignore_path


##


_STAR = GitignoreGlobStar()
_QM = GitignoreGlobQuestionMark()
_DSTAR = GitignoreDoubleStarSegment()

_CHAR = GitignoreGlobCharClass.Char
_RANGE = GitignoreGlobCharClass.Range
_NAMED = GitignoreGlobCharClass.Named


def _lit(text: str) -> GitignoreGlobLiteral:
    return GitignoreGlobLiteral(text)


def _cc(*items: GitignoreGlobCharClass.Item, negated: bool = False) -> GitignoreGlobCharClass:
    return GitignoreGlobCharClass(items, negated=negated)


def _seg(*parts: GitignoreGlobPart) -> GitignoreGlobSegment:
    return GitignoreGlobSegment(parts)


def _pat(
        *segments: ta.Any,
        negated: bool = False,
        anchored: bool = False,
        dir_only: bool = False,
) -> GitignorePattern:
    return GitignorePattern(
        segments,
        negated=negated,
        anchored=anchored,
        dir_only=dir_only,
    )


##


class TestGitignoreIr(unittest.TestCase):
    def test_abstract_bases(self):
        for cls in [
            GitignoreGlobPart,
            GitignoreGlobCharClass.Item,
            GitignoreLine,
        ]:
            with self.assertRaises(TypeError):
                cls()

    def test_validation(self):
        with self.assertRaises(Exception):  # noqa
            GitignoreGlobLiteral('')
        with self.assertRaises(Exception):  # noqa
            GitignoreGlobLiteral('a/b')

        with self.assertRaises(Exception):  # noqa
            _CHAR('ab')
        with self.assertRaises(Exception):  # noqa
            _RANGE('a', 'bc')
        with self.assertRaises(Exception):  # noqa
            _NAMED('bogus')

        with self.assertRaises(Exception):  # noqa
            GitignorePattern(())
        with self.assertRaises(Exception):  # noqa
            GitignorePattern((_seg(_lit('a')), _seg(_lit('b'))), anchored=False)
        GitignorePattern((_seg(_lit('a')), _seg(_lit('b'))), anchored=True)

        with self.assertRaises(Exception):  # noqa
            GitignoreBlankLine(1, 'x')
        with self.assertRaises(Exception):  # noqa
            GitignoreCommentLine(1, 'x')
        with self.assertRaises(Exception):  # noqa
            GitignoreCommentLine(0, '#x')
        with self.assertRaises(Exception):  # noqa
            GitignoreCommentLine(1, '#x\n')

    def test_hashable(self):
        p = parse_gitignore_pattern('a/**/[!x-z]?*')
        self.assertEqual(hash(p), hash(parse_gitignore_pattern('a/**/[!x-z]?*')))
        self.assertEqual({p}, {parse_gitignore_pattern('a/**/[!x-z]?*')})

    def test_char_classes(self):
        self.assertEqual(len(GITIGNORE_GLOB_CHAR_CLASSES['graph']), 94)
        self.assertEqual(len(GITIGNORE_GLOB_CHAR_CLASSES['print']), 95)
        self.assertEqual(len(GITIGNORE_GLOB_CHAR_CLASSES['cntrl']), 33)
        self.assertEqual(len(GITIGNORE_GLOB_CHAR_CLASSES['punct']), 32)
        self.assertEqual(
            GITIGNORE_GLOB_CHAR_CLASSES['graph'],
            GITIGNORE_GLOB_CHAR_CLASSES['alnum'] | GITIGNORE_GLOB_CHAR_CLASSES['punct'],
        )
        for cs in GITIGNORE_GLOB_CHAR_CLASSES.values():
            self.assertTrue(all(ord(c) < 0x80 for c in cs))


##


class TestGitignorePatternParsing(unittest.TestCase):
    def test_flags(self):
        for s, e in [
            ('foo', _pat(_seg(_lit('foo')))),
            ('/foo', _pat(_seg(_lit('foo')), anchored=True)),
            ('foo/', _pat(_seg(_lit('foo')), dir_only=True)),
            ('/foo/', _pat(_seg(_lit('foo')), anchored=True, dir_only=True)),
            ('!foo', _pat(_seg(_lit('foo')), negated=True)),
            ('!/foo/', _pat(_seg(_lit('foo')), negated=True, anchored=True, dir_only=True)),
            ('!!foo', _pat(_seg(_lit('!foo')), negated=True)),
            ('\\!foo', _pat(_seg(_lit('!foo')))),
            ('\\#foo', _pat(_seg(_lit('#foo')))),
            ('foo/bar', _pat(_seg(_lit('foo')), _seg(_lit('bar')), anchored=True)),
            ('foo/bar/', _pat(_seg(_lit('foo')), _seg(_lit('bar')), anchored=True, dir_only=True)),
            ('/foo/bar', _pat(_seg(_lit('foo')), _seg(_lit('bar')), anchored=True)),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_double_stars(self):
        for s, e in [
            ('**/foo', _pat(_DSTAR, _seg(_lit('foo')), anchored=True)),
            ('foo/**', _pat(_seg(_lit('foo')), _DSTAR, anchored=True)),
            ('a/**/b', _pat(_seg(_lit('a')), _DSTAR, _seg(_lit('b')), anchored=True)),
            ('a/***/b', _pat(_seg(_lit('a')), _DSTAR, _seg(_lit('b')), anchored=True)),
            ('**', _pat(_DSTAR)),
            ('***', _pat(_DSTAR)),
            ('/**', _pat(_DSTAR, anchored=True)),
            ('**/', _pat(_DSTAR, dir_only=True)),
            ('**/**', _pat(_DSTAR, _DSTAR, anchored=True)),
            ('\\/**', _pat(_seg(), _DSTAR, anchored=True)),
            ('**\\/x', _pat(_DSTAR, _seg(_lit('x')), anchored=True)),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_wildcards(self):
        for s, e in [
            ('*', _pat(_seg(_STAR))),
            ('*.py', _pat(_seg(_STAR, _lit('.py')))),
            ('a*b', _pat(_seg(_lit('a'), _STAR, _lit('b')))),
            ('a**b', _pat(_seg(_lit('a'), _STAR, _lit('b')))),
            ('***x', _pat(_seg(_STAR, _lit('x')))),
            ('x***', _pat(_seg(_lit('x'), _STAR))),
            ('a/**b', _pat(_seg(_lit('a')), _seg(_STAR, _lit('b')), anchored=True)),
            ('?', _pat(_seg(_QM))),
            ('a?b*c', _pat(_seg(_lit('a'), _QM, _lit('b'), _STAR, _lit('c')))),
            ('??*', _pat(_seg(_QM, _QM, _STAR))),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_escapes(self):
        for s, e in [
            ('\\*', _pat(_seg(_lit('*')))),
            ('\\**', _pat(_seg(_lit('*'), _STAR))),
            ('*\\**', _pat(_seg(_STAR, _lit('*'), _STAR))),
            ('\\?', _pat(_seg(_lit('?')))),
            ('\\[a]', _pat(_seg(_lit('[a]')))),
            ('\\\\', _pat(_seg(_lit('\\')))),
            ('a\\ ', _pat(_seg(_lit('a ')))),
            ('a\\/b', _pat(_seg(_lit('a')), _seg(_lit('b')), anchored=True)),
            ('a\\\\/b', _pat(_seg(_lit('a\\')), _seg(_lit('b')), anchored=True)),
            ('\\a', _pat(_seg(_lit('a')))),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_char_classes(self):
        for s, e in [
            ('[abc]', _pat(_seg(_cc(_CHAR('a'), _CHAR('b'), _CHAR('c'))))),
            ('[a-z]', _pat(_seg(_cc(_RANGE('a', 'z'))))),
            ('[!a-z]', _pat(_seg(_cc(_RANGE('a', 'z'), negated=True)))),
            ('[^a-z]', _pat(_seg(_cc(_RANGE('a', 'z'), negated=True)))),
            ('[]a]', _pat(_seg(_cc(_CHAR(']'), _CHAR('a'))))),
            ('[]]', _pat(_seg(_cc(_CHAR(']'))))),
            ('[!]a]', _pat(_seg(_cc(_CHAR(']'), _CHAR('a'), negated=True)))),
            ('[!!]', _pat(_seg(_cc(_CHAR('!'), negated=True)))),
            ('[a-]', _pat(_seg(_cc(_CHAR('a'), _CHAR('-'))))),
            ('[-a]', _pat(_seg(_cc(_CHAR('-'), _CHAR('a'))))),
            ('[a-c-e]', _pat(_seg(_cc(_RANGE('a', 'c'), _CHAR('-'), _CHAR('e'))))),
            ('[a-\\]]', _pat(_seg(_cc(_RANGE('a', ']'))))),
            ('[\\[-a]', _pat(_seg(_cc(_RANGE('[', 'a'))))),
            ('[\\]]', _pat(_seg(_cc(_CHAR(']'))))),
            ('[\\a]', _pat(_seg(_cc(_CHAR('a'))))),
            ('[[]', _pat(_seg(_cc(_CHAR('['))))),
            ('[[:alpha:]]', _pat(_seg(_cc(_NAMED('alpha'))))),
            ('[[:alpha:]_]', _pat(_seg(_cc(_NAMED('alpha'), _CHAR('_'))))),
            ('[![:digit:]]', _pat(_seg(_cc(_NAMED('digit'), negated=True)))),
            ('[[:alpha:][:digit:]]', _pat(_seg(_cc(_NAMED('alpha'), _NAMED('digit'))))),
            (
                '[[:alpha]',
                _pat(_seg(_cc(
                    _CHAR('['), _CHAR(':'), _CHAR('a'), _CHAR('l'), _CHAR('p'), _CHAR('h'), _CHAR('a'),
                ))),
            ),
            ('[[:]', _pat(_seg(_cc(_CHAR('['), _CHAR(':'))))),
            ('[[:-a]', _pat(_seg(_cc(_CHAR('['), _RANGE(':', 'a'))))),
            ('a[/x]b', _pat(_seg(_lit('a'), _cc(_CHAR('/'), _CHAR('x')), _lit('b')), anchored=True)),
            ('[a][b]', _pat(_seg(_cc(_CHAR('a')), _cc(_CHAR('b'))))),
            ('x[a]y', _pat(_seg(_lit('x'), _cc(_CHAR('a')), _lit('y')))),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_degenerate(self):
        for s, e in [
            ('', _pat(_seg())),
            ('!', _pat(_seg(), negated=True)),
            ('/', _pat(_seg(), dir_only=True)),
            ('//', _pat(_seg(), anchored=True, dir_only=True)),
            ('///', _pat(_seg(), _seg(), anchored=True, dir_only=True)),
            ('a//b', _pat(_seg(_lit('a')), _seg(), _seg(_lit('b')), anchored=True)),
            ('//a', _pat(_seg(), _seg(_lit('a')), anchored=True)),
            ('\t', _pat(_seg(_lit('\t')))),
            (' ', _pat(_seg(_lit(' ')))),
            ('foo ', _pat(_seg(_lit('foo ')))),
            (' foo', _pat(_seg(_lit(' foo')))),
            ('#foo', _pat(_seg(_lit('#foo')))),
        ]:
            self.assertEqual(parse_gitignore_pattern(s), e, s)

    def test_errors(self):
        for s, m in [
            ('foo\\', 'trailing backslash'),
            ('\\', 'trailing backslash'),
            ('!\\', 'trailing backslash'),
            ('foo\\/', 'trailing backslash'),
            ('foo[', 'unterminated bracket expression'),
            ('[', 'unterminated bracket expression'),
            ('[!', 'unterminated bracket expression'),
            ('[^', 'unterminated bracket expression'),
            ('[]', 'unterminated bracket expression'),
            ('[!]', 'unterminated bracket expression'),
            ('[a', 'unterminated bracket expression'),
            ('[a-', 'unterminated bracket expression'),
            ('[a-\\', 'unterminated bracket expression'),
            ('[\\', 'unterminated bracket expression'),
            ('[\\]', 'unterminated bracket expression'),
            ('a[/', 'unterminated bracket expression'),
            ('[[:alpha:]', 'unterminated bracket expression'),
            ('[[:alpha:', 'unterminated bracket expression'),
            ('[[:foo:]]', "unknown character class 'foo'"),
            ('[[::]]', "unknown character class ''"),
            ('[[:ALPHA:]]', "unknown character class 'ALPHA'"),
        ]:
            with self.assertRaises(GitignorePatternError) as cm:
                parse_gitignore_pattern(s)
            self.assertEqual(cm.exception.message, m, s)
            self.assertEqual(cm.exception.pattern, s, s)
            self.assertIsNone(cm.exception.line_no, s)
            self.assertEqual(str(cm.exception), f'{m}: {s!r}')


##


class TestGitignoreFileParsing(unittest.TestCase):
    def test_lines(self):
        f = parse_gitignore(
            '# a comment\n'
            '\n'
            'foo\n'
            '   \n'
            'bar/   \n'
            'baz\\ \n'
            'qux \\\n'
            'bad[\n'
            '\\#not a comment\n'
            ' #also not a comment\n'
            '#\n'
            '!neg\r\n'
            '\ttab\t\n'
            '\r\n'
            '\n'
            'last',
        )

        self.assertEqual(f.lines, (
            GitignoreCommentLine(1, '# a comment'),
            GitignoreBlankLine(2, ''),
            GitignorePatternLine(3, 'foo', _pat(_seg(_lit('foo')))),
            GitignorePatternLine(4, '   ', _pat(_seg())),
            GitignorePatternLine(5, 'bar/   ', _pat(_seg(_lit('bar')), dir_only=True)),
            GitignorePatternLine(6, 'baz\\ ', _pat(_seg(_lit('baz ')))),
            GitignoreInvalidLine(7, 'qux \\', 'trailing backslash'),
            GitignoreInvalidLine(8, 'bad[', 'unterminated bracket expression'),
            GitignorePatternLine(9, '\\#not a comment', _pat(_seg(_lit('#not a comment')))),
            GitignorePatternLine(10, ' #also not a comment', _pat(_seg(_lit(' #also not a comment')))),
            GitignoreCommentLine(11, '#'),
            GitignorePatternLine(12, '!neg', _pat(_seg(_lit('neg')), negated=True)),
            GitignorePatternLine(13, '\ttab\t', _pat(_seg(_lit('\ttab\t')))),
            GitignoreBlankLine(14, ''),
            GitignoreBlankLine(15, ''),
            GitignorePatternLine(16, 'last', _pat(_seg(_lit('last')))),
        ))

        self.assertEqual(f.patterns, [
            l.pattern for l in f.lines if isinstance(l, GitignorePatternLine)
        ])
        self.assertEqual(len(f.patterns), 9)

        self.assertEqual(f.lines[0].text, ' a comment')  # type: ignore[attr-defined]

    def test_line_splitting(self):
        self.assertEqual(parse_gitignore('').lines, ())
        self.assertEqual(parse_gitignore('\n').lines, (GitignoreBlankLine(1, ''),))
        self.assertEqual(parse_gitignore('\n\n').lines, (GitignoreBlankLine(1, ''), GitignoreBlankLine(2, '')))
        self.assertEqual(parse_gitignore('a').lines, (GitignorePatternLine(1, 'a', _pat(_seg(_lit('a')))),))
        self.assertEqual(parse_gitignore('a\n').lines, (GitignorePatternLine(1, 'a', _pat(_seg(_lit('a')))),))
        self.assertEqual(
            parse_gitignore('a\n\n').lines,
            (GitignorePatternLine(1, 'a', _pat(_seg(_lit('a')))), GitignoreBlankLine(2, '')),
        )
        self.assertEqual(
            parse_gitignore('a\r\nb\r\n').lines,
            (
                GitignorePatternLine(1, 'a', _pat(_seg(_lit('a')))),
                GitignorePatternLine(2, 'b', _pat(_seg(_lit('b')))),
            ),
        )

        # Only line feeds separate lines - not, as str.splitlines has it, form feeds, lone carriage returns, or the
        # like.
        self.assertEqual(
            parse_gitignore('a\x0cb\rc\x85d\u2028e\n').lines,
            (GitignorePatternLine(1, 'a\x0cb\rc\x85d\u2028e', _pat(_seg(_lit('a\x0cb\rc\x85d\u2028e')))),),
        )

    def test_bom(self):
        self.assertEqual(
            parse_gitignore('\ufeff# c\nfoo\n').lines,
            (
                GitignoreCommentLine(1, '# c'),
                GitignorePatternLine(2, 'foo', _pat(_seg(_lit('foo')))),
            ),
        )

        # Only a leading one is a bom.
        self.assertEqual(
            parse_gitignore('foo\n\ufeffbar\n').lines,
            (
                GitignorePatternLine(1, 'foo', _pat(_seg(_lit('foo')))),
                GitignorePatternLine(2, '\ufeffbar', _pat(_seg(_lit('\ufeffbar')))),
            ),
        )

    def test_strict(self):
        parse_gitignore('ok\nbad[\n')

        with self.assertRaises(GitignorePatternError) as cm:
            parse_gitignore('ok\nbad[  \n', strict=True)
        self.assertEqual(cm.exception.message, 'unterminated bracket expression')
        self.assertEqual(cm.exception.pattern, 'bad[  ')
        self.assertEqual(cm.exception.line_no, 2)
        self.assertEqual(str(cm.exception), "line 2: unterminated bracket expression: 'bad[  '")


##


class TestGitignorePatternMatcher(unittest.TestCase):
    def _check(self, pattern: str, cases: ta.Sequence[ta.Tuple[str, bool, bool]]) -> None:
        m = GitignorePatternMatcher(parse_gitignore_pattern(pattern))
        for path, is_dir, expected in cases:
            self.assertEqual(
                m.matches(path, is_dir=is_dir),
                expected,
                f'pattern {pattern!r} path {path!r} is_dir {is_dir}',
            )

    def test_literals(self):
        self._check('foo', [
            ('foo', False, True),
            ('foo', True, True),
            ('a/foo', False, True),
            ('a/b/foo', False, True),
            ('foobar', False, False),
            ('barfoo', False, False),
            ('foo/bar', False, False),
            ('Foo', False, False),
        ])
        self._check('/foo', [
            ('foo', False, True),
            ('foo', True, True),
            ('a/foo', False, False),
            ('foo/bar', False, False),
        ])
        self._check('foo/', [
            ('foo', True, True),
            ('foo', False, False),
            ('a/foo', True, True),
            ('a/foo', False, False),
            ('foo/bar', False, False),
            ('foo/bar', True, False),
        ])
        self._check('/foo/', [
            ('foo', True, True),
            ('foo', False, False),
            ('a/foo', True, False),
        ])
        self._check('foo/bar', [
            ('foo/bar', False, True),
            ('foo/bar', True, True),
            ('a/foo/bar', False, False),
            ('foo/bar/baz', False, False),
            ('foo', True, False),
            ('bar', False, False),
        ])
        self._check('.*', [
            ('.git', True, True),
            ('a/.hidden', False, True),
            ('a.b', False, False),
        ])

    def test_double_stars(self):
        self._check('**/foo', [
            ('foo', False, True),
            ('a/foo', False, True),
            ('a/b/foo', False, True),
            ('foo/x', False, False),
            ('afoo', False, False),
        ])
        self._check('**/foo/bar', [
            ('foo/bar', False, True),
            ('a/foo/bar', False, True),
            ('a/b/foo/bar', False, True),
            ('a/foo/x/bar', False, False),
            ('bar', False, False),
        ])
        self._check('foo/**', [
            ('foo', True, False),
            ('foo', False, False),
            ('foo/a', False, True),
            ('foo/a', True, True),
            ('foo/a/b', False, True),
            ('a/foo/b', False, False),
            ('foobar/a', False, False),
        ])
        self._check('a/**/b', [
            ('a/b', False, True),
            ('a/x/b', False, True),
            ('a/x/y/b', False, True),
            ('a/x/b/b', False, True),
            ('a', True, False),
            ('a/b/c', False, False),
            ('x/a/b', False, False),
            ('a/xb', False, False),
        ])
        self._check('a/***/b', [
            ('a/b', False, True),
            ('a/x/y/b', False, True),
        ])
        self._check('**', [
            ('a', False, True),
            ('a', True, True),
            ('a/b', False, True),
        ])
        self._check('/**', [
            ('a', False, True),
            ('a', True, True),
            ('a/b', False, True),
            ('a/b/c', True, True),
        ])
        self._check('**/', [
            ('a', True, True),
            ('a', False, False),
            ('a/b', True, True),
        ])
        self._check('**/**', [
            ('a', False, True),
            ('a/b', False, True),
        ])
        self._check('**/foo/**', [
            ('foo', True, False),
            ('foo/a', False, True),
            ('x/foo/a/b', False, True),
            ('x/foo', True, False),
            ('x/foo/a', True, True),
        ])
        self._check('a/**/', [
            ('a', True, False),
            ('a/b', True, True),
            ('a/b', False, False),
            ('a/b/c', True, True),
        ])

    def test_non_boundary_double_stars(self):
        # Consecutive asterisks not alone between slashes are just a single asterisk.
        self._check('a**b', [
            ('ab', False, True),
            ('axyb', False, True),
            ('x/axyb', False, True),
            ('a/b', False, False),
        ])
        self._check('a/**b', [
            ('a/b', False, True),
            ('a/xb', False, True),
            ('a/x/b', False, False),
        ])
        self._check('a**/b', [
            ('a/b', False, True),
            ('ax/b', False, True),
            ('ax/y/b', False, False),
        ])
        self._check('a/b**', [
            ('a/b', False, True),
            ('a/bx', False, True),
            ('a/bx/y', False, False),
        ])

    def test_wildcards(self):
        self._check('*', [
            ('a', False, True),
            ('a/b', False, True),
            ('a', True, True),
        ])
        self._check('*.py', [
            ('a.py', False, True),
            ('x/a.py', False, True),
            ('.py', False, True),
            ('a.pyc', False, False),
            ('a.py/b', False, False),
        ])
        self._check('*/tmp', [
            ('a/tmp', False, True),
            ('a/b/tmp', False, False),
            ('tmp', False, False),
        ])
        self._check('a*', [
            ('a', False, True),
            ('abc', False, True),
            ('ba', False, False),
            ('x/abc', False, True),
        ])
        self._check('a*b*c', [
            ('abc', False, True),
            ('axbxc', False, True),
            ('axxbxxcxxbxxc', False, True),
            ('acb', False, False),
        ])
        self._check('a?c', [
            ('abc', False, True),
            ('ac', False, False),
            ('abbc', False, False),
            ('a/c', False, False),
        ])
        self._check('?', [
            ('a', False, True),
            ('ab', False, False),
            ('x/a', False, True),
        ])
        self._check('a/?', [
            ('a/b', False, True),
            ('a/bc', False, False),
            ('a', True, False),
        ])
        self._check('??*', [
            ('a', False, False),
            ('ab', False, True),
            ('abc', False, True),
        ])

    def test_char_classes(self):
        self._check('[abc]x', [
            ('ax', False, True),
            ('bx', False, True),
            ('cx', False, True),
            ('dx', False, False),
            ('x', False, False),
            ('abx', False, False),
        ])
        self._check('[!abc]x', [
            ('ax', False, False),
            ('dx', False, True),
            ('x', False, False),
        ])
        self._check('[^abc]x', [
            ('ax', False, False),
            ('dx', False, True),
        ])
        self._check('[a-c]x', [
            ('ax', False, True),
            ('bx', False, True),
            ('cx', False, True),
            ('dx', False, False),
            ('Bx', False, False),
        ])
        self._check('[c-a]x', [
            ('ax', False, False),
            ('bx', False, False),
            ('cx', False, False),
        ])
        self._check('[]]x', [
            (']x', False, True),
            ('ax', False, False),
        ])
        self._check('[!]]x', [
            (']x', False, False),
            ('ax', False, True),
        ])
        self._check('[a-]x', [
            ('ax', False, True),
            ('-x', False, True),
            ('bx', False, False),
        ])
        self._check('[-a]x', [
            ('ax', False, True),
            ('-x', False, True),
            ('bx', False, False),
        ])
        self._check('[a-c-e]x', [
            ('bx', False, True),
            ('-x', False, True),
            ('ex', False, True),
            ('dx', False, False),
        ])
        self._check('[Z-\\]]x', [
            ('Zx', False, True),
            ('[x', False, True),
            ('\\x', False, True),
            (']x', False, True),
            ('^x', False, False),
        ])
        self._check('[[:digit:]]x', [
            ('1x', False, True),
            ('ax', False, False),
            ('\u0663x', False, False),
        ])
        self._check('[[:alpha:]_]x', [
            ('ax', False, True),
            ('Zx', False, True),
            ('_x', False, True),
            ('1x', False, False),
            ('\u00e9x', False, False),
        ])
        self._check('[![:space:]]', [
            ('a', False, True),
            (' ', False, False),
            ('\t', False, False),
        ])
        self._check('[[:alpha]', [
            ('[', False, True),
            (':', False, True),
            ('a', False, True),
            ('h', False, True),
            ('b', False, False),
            ('alpha', False, False),
        ])
        self._check('a[/x]b', [
            ('axb', False, True),
            ('a/b', False, False),
            ('s/axb', False, False),
        ])
        self._check('[a][b]', [
            ('ab', False, True),
            ('ba', False, False),
        ])

    def test_escapes(self):
        self._check('\\#x', [
            ('#x', False, True),
        ])
        self._check('\\!x', [
            ('!x', False, True),
            ('x', False, False),
        ])
        self._check('\\*', [
            ('*', False, True),
            ('a', False, False),
        ])
        self._check('\\?', [
            ('?', False, True),
            ('a', False, False),
        ])
        self._check('\\[a]', [
            ('[a]', False, True),
            ('a', False, False),
        ])
        self._check('a\\ ', [
            ('a ', False, True),
            ('a', False, False),
        ])
        self._check('a\\/b', [
            ('a/b', False, True),
            ('a', True, False),
            ('x/a/b', False, False),
        ])
        self._check('\\\\', [
            ('\\', False, True),
        ])

    def test_degenerate(self):
        for p in ['', '!', '/', '//', '///', 'a//b', '//a']:
            self._check(p, [
                ('a', False, False),
                ('a', True, False),
                ('a/b', False, False),
                ('a/b', True, False),
            ])

    def test_unicode(self):
        self._check('caf\u00e9', [
            ('caf\u00e9', False, True),
            ('cafe', False, False),
        ])
        self._check('caf?', [
            ('caf\u00e9', False, True),
        ])
        self._check('[\u00e9]', [
            ('\u00e9', False, True),
            ('e', False, False),
        ])

    def test_paths(self):
        for p in ['', '/', '/a', 'a/', 'a//b', '.', '..', './a', 'a/./b', 'a/../b', '../a']:
            with self.assertRaises(GitignorePathError):
                split_gitignore_path(p)

        self.assertEqual(split_gitignore_path('a'), ['a'])
        self.assertEqual(split_gitignore_path('a/b/c'), ['a', 'b', 'c'])
        self.assertEqual(split_gitignore_path('.a/..b/c.'), ['.a', '..b', 'c.'])
        self.assertEqual(split_gitignore_path('\\'), ['\\'])


##


class TestGitignoreFilter(unittest.TestCase):
    def _filter(self, text: str) -> GitignoreFilter:
        return GitignoreFilter(parse_gitignore(text).patterns)

    def test_last_match_wins(self):
        f = self._filter('*.py\n!keep.py\n')
        self.assertTrue(f.is_ignored('a.py'))
        self.assertTrue(f.is_ignored('x/a.py'))
        self.assertFalse(f.is_ignored('keep.py'))
        self.assertFalse(f.is_ignored('x/keep.py'))
        self.assertFalse(f.is_ignored('a.txt'))

        f = self._filter('!keep.py\n*.py\n')
        self.assertTrue(f.is_ignored('keep.py'))

        f = self._filter('*.py\n!keep.py\nkeep.py\n')
        self.assertTrue(f.is_ignored('keep.py'))

    def test_match(self):
        f = self._filter('*.py\n!keep.py\n')
        p_all, p_keep = f.patterns

        self.assertIsNone(f.match('a.txt'))
        self.assertEqual(f.match('a.py'), GitignoreMatch(p_all, 'a.py', is_dir=False))
        self.assertEqual(f.match('x/a.py', is_dir=True), GitignoreMatch(p_all, 'x/a.py', is_dir=True))

        m = f.match('keep.py')
        self.assertEqual(m, GitignoreMatch(p_keep, 'keep.py', is_dir=False))
        self.assertFalse(m.ignored)  # type: ignore[union-attr]

    def test_excluded_parents(self):
        f = self._filter('build/\n!build/keep.txt\n')
        p_build, _ = f.patterns
        self.assertTrue(f.is_ignored('build', is_dir=True))
        self.assertFalse(f.is_ignored('build', is_dir=False))
        self.assertTrue(f.is_ignored('build/x.o'))
        self.assertTrue(f.is_ignored('build/keep.txt'))
        self.assertTrue(f.is_ignored('build/sub/keep.txt'))
        self.assertTrue(f.is_ignored('a/build/keep.txt'))
        self.assertEqual(f.match('build/sub/keep.txt'), GitignoreMatch(p_build, 'build', is_dir=True))
        self.assertEqual(f.match('a/build/sub/keep.txt'), GitignoreMatch(p_build, 'a/build', is_dir=True))

        # Excluding a directory's contents rather than the directory itself allows re-inclusion.
        f = self._filter('build/**\n!build/keep.txt\n')
        self.assertFalse(f.is_ignored('build', is_dir=True))
        self.assertTrue(f.is_ignored('build/x.o'))
        self.assertFalse(f.is_ignored('build/keep.txt'))
        self.assertTrue(f.is_ignored('build/sub', is_dir=True))
        self.assertTrue(f.is_ignored('build/sub/keep.txt'))

        # A negated match on a parent does not decide anything for its children.
        f = self._filter('build/\n!build/\n*.o\n')
        self.assertFalse(f.is_ignored('build', is_dir=True))
        self.assertTrue(f.is_ignored('build/x.o'))
        self.assertFalse(f.is_ignored('build/x.c'))

    def test_ignore_everything_but(self):
        # The idiom for ignoring everything but files of a given type at any depth.
        f = self._filter('*\n!*/\n!*.txt\n')
        self.assertFalse(f.is_ignored('a', is_dir=True))
        self.assertFalse(f.is_ignored('a/b', is_dir=True))
        self.assertFalse(f.is_ignored('a/b/c.txt'))
        self.assertTrue(f.is_ignored('a/b/c.md'))
        self.assertTrue(f.is_ignored('c.md'))
        self.assertFalse(f.is_ignored('c.txt'))

        # Without the directory re-inclusion, nothing nested survives.
        f = self._filter('*\n!*.txt\n')
        self.assertFalse(f.is_ignored('c.txt'))
        self.assertTrue(f.is_ignored('a', is_dir=True))
        self.assertTrue(f.is_ignored('a/c.txt'))

    def test_invalid_lines_never_match(self):
        f = self._filter('foo[\nbar\\\n[[:nope:]]\n')
        self.assertEqual(f.patterns, ())
        self.assertFalse(f.is_ignored('foo['))
        self.assertFalse(f.is_ignored('bar\\'))
        self.assertFalse(f.is_ignored('foo'))

    def test_filter_paths(self):
        f = self._filter('*.pyc\nbuild/\n')

        paths = ['a.py', 'a.pyc', 'build', 'build/x', 'x/build/y', 'buildfile']
        self.assertEqual(
            list(f.filter_paths(paths)),
            ['a.py', 'build', 'buildfile'],
        )
        self.assertEqual(
            list(f.filter_paths(paths, is_dir=lambda p: p == 'build')),
            ['a.py', 'buildfile'],
        )
        self.assertEqual(list(f.filter_paths([])), [])

    def test_paths(self):
        f = self._filter('foo\n')
        for p in ['', '/foo', 'foo/', 'a//foo', './foo', 'a/../foo']:
            with self.assertRaises(GitignorePathError):
                f.is_ignored(p)


##


class TestGitignoreAgainstGit(unittest.TestCase):
    """
    Cross-validates against a real git, building a repo containing a gitignore and a tree of files and directories and
    comparing every verdict - and the line number of the pattern responsible - with those of `git check-ignore`.
    """

    def _run_git(self, *args: str, cwd: str, env: ta.Mapping[str, str], input: bytes = b'') -> bytes:  # noqa
        proc = subprocess.run(  # noqa
            ['git', *args],
            cwd=cwd,
            env=env,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # check-ignore exits 1 when no path is ignored.
        if proc.returncode not in (0, 1):
            raise RuntimeError(f'git {args!r} failed with {proc.returncode}: {proc.stderr.decode()}')

        return proc.stdout

    def _check(self, gitignore: str, tree: ta.Sequence[str]) -> None:
        if shutil.which('git') is None:
            self.skipTest('no git')

        base_dir = tempfile.mkdtemp()

        # Keep any global or system configuration - especially a core.excludesFile - well away from the results.
        home_dir = os.path.join(base_dir, 'home')
        os.mkdir(home_dir)
        env = {
            **os.environ,
            'HOME': home_dir,
            'XDG_CONFIG_HOME': os.path.join(home_dir, '.config'),
            'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_CONFIG_NOSYSTEM': '1',
        }

        repo_dir = os.path.join(base_dir, 'repo')
        os.mkdir(repo_dir)

        self._run_git('init', '-q', cwd=repo_dir, env=env)
        self._run_git('config', 'core.ignorecase', 'false', cwd=repo_dir, env=env)

        with open(os.path.join(repo_dir, '.gitignore'), 'w', newline='') as f:
            f.write(gitignore)

        for p in tree:
            fp = os.path.join(repo_dir, p)
            if p.endswith('/'):
                os.makedirs(fp, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, 'w'):
                    pass

        #

        paths = [p.rstrip('/') for p in tree]

        out = self._run_git(
            'check-ignore',
            '--no-index',
            '--verbose',
            '--non-matching',
            '-z',
            '--stdin',
            cwd=repo_dir,
            env=env,
            input=b''.join(p.encode('utf-8') + b'\0' for p in paths),
        )

        fields = out.decode('utf-8').split('\0')
        self.assertEqual(fields[-1], '')
        fields.pop()
        self.assertEqual(len(fields), len(paths) * 4)

        git_results: ta.Dict[str, ta.Tuple[ta.Optional[int], bool]] = {}
        for i in range(0, len(fields), 4):
            source, line_no, pattern, path = fields[i:i + 4]
            if source:
                self.assertEqual(source, '.gitignore')
                git_results[path] = (int(line_no), not pattern.startswith('!'))
            else:
                git_results[path] = (None, False)
        self.assertEqual(set(git_results), set(paths))

        #

        gf = parse_gitignore(gitignore)
        line_nos_by_pattern_id = {
            id(l.pattern): l.line_no
            for l in gf.lines
            if isinstance(l, GitignorePatternLine)
        }
        flt = GitignoreFilter(gf.patterns)

        for p in tree:
            path = p.rstrip('/')
            m = flt.match(path, is_dir=p.endswith('/'))
            if m is not None:
                result: ta.Tuple[ta.Optional[int], bool] = (line_nos_by_pattern_id[id(m.pattern)], m.ignored)
            else:
                result = (None, False)

            self.assertEqual(result, git_results[path], f'path {path!r} in gitignore {gitignore!r}')

        #

        shutil.rmtree(base_dir)

    def test_basics(self):
        self._check(
            '# a comment\n'
            '\n'
            '*.pyc\n'
            '/build/\n'
            '!build/keep.txt\n'
            'dist/**\n'
            '!dist/keep\n'
            '!dist/keep/**\n'
            '**/node_modules/\n'
            'logs/*.log\n'
            '!logs/important.log\n'
            'docs/**/*.md\n'
            'spaced   \n'
            '   \n',
            [
                'a.pyc',
                'a.py',
                'sub/b.pyc',
                'sub/c.py',
                'build/',
                'build/keep.txt',
                'build/x.o',
                'build/sub/',
                'build/sub/keep.txt',
                'other/build/',
                'other/build/y',
                'dist/',
                'dist/a.tar',
                'dist/keep/',
                'dist/keep/z',
                'dist/keep/sub/',
                'dist/keep/sub/w',
                'node_modules/',
                'node_modules/m.js',
                'x/node_modules/',
                'x/node_modules/n.js',
                'x/node_modules.txt',
                'logs/',
                'logs/a.log',
                'logs/important.log',
                'logs/sub/',
                'logs/sub/b.log',
                'docs/',
                'docs/a.md',
                'docs/x/',
                'docs/x/b.md',
                'docs/x/c.txt',
                'docs/x/y/',
                'docs/x/y/d.md',
                'spaced',
                'spaced   ',
            ],
        )

    def test_wildcards(self):
        self._check(
            'foo?\n'
            '[abc]x\n'
            '[!abc]y\n'
            '[a-c]z\n'
            '[[:digit:]]d\n'
            '[]]q\n'
            '[!]]r\n'
            '[a-]s\n'
            '\\#hash\n'
            '\\!bang\n'
            'trailing\\ \n'
            'lib/*/gen\n'
            'a/**/b\n'
            '*.log*\n'
            'weird**\n'
            '**weird\n'
            'in**side\n'
            '\ttab\t\n'
            'esc\\*\n'
            'q\\?\n',
            [
                'foo1',
                'foo',
                'foo12',
                'sub/foo1',
                'ax',
                'dx',
                'xx',
                'ay',
                'dy',
                'bz',
                'dz',
                '5d',
                'xd',
                ']q',
                'aq',
                ']r',
                'ar',
                'as',
                '-s',
                'bs',
                '#hash',
                '!bang',
                'bang',
                'trailing ',
                'trailing',
                'lib/',
                'lib/gen',
                'lib/x/',
                'lib/x/gen',
                'lib/x/y/',
                'lib/x/y/gen',
                'a/',
                'a/b',
                'a/x/',
                'a/x/b',
                'a/x/y/',
                'a/x/y/b',
                'x/a/',
                'x/a/b',
                'q.log',
                'q.logs',
                'q.lo',
                'weird',
                'weirdx',
                'xweird',
                'xweirdx',
                'inXside',
                'inside',
                'in/',
                'in/side',
                '\ttab\t',
                'tab',
                'esc*',
                'escx',
                'q?',
                'qx',
            ],
        )

    def test_anchoring(self):
        self._check(
            'foo\n'
            '/bar\n'
            'baz/\n'
            'qux/quux\n'
            '*/tmp\n'
            '**/deep\n'
            'deep2/**\n'
            '!deep2/kept\n'
            '**/\n'
            '!**/\n'
            '/\n'
            '!\n',
            [
                'foo',
                'Foo',
                's/foo',
                's/t/foo',
                'bar',
                's/bar',
                'baz/',
                'baz/inner',
                's/baz/',
                's/baz/inner',
                't/baz',
                'qux/',
                'qux/quux',
                's/qux/',
                's/qux/quux',
                'tmp/',
                'x/tmp/',
                'x/tmp/f',
                'x/y/tmp/',
                'deep',
                's/deep',
                'deep2/',
                'deep2/a',
                'deep2/kept',
                'deep2/sub/',
                'deep2/sub/b',
                'deep2/sub/kept',
            ],
        )

    def test_invalid_and_crlf(self):
        self._check(
            '\ufeff'
            '# bom and crlf\r\n'
            'a//b\r\n'
            'foo[\r\n'
            'bar\\\r\n'
            '[[:foo:]]\r\n'
            'ok\r\n'
            '\r\n'
            'ws  \r\n',
            [
                'a/',
                'a/b',
                'foo[',
                'foo',
                'bar\\',
                'bar',
                'ok',
                'ws',
            ],
        )
