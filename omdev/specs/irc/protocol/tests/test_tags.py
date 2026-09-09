import itertools

from omcore import dataclasses as dc

from ..tags import escape_tag_value
from ..tags import parse_tags
from ..tags import unescape_tag_value


##


@dc.dataclass(frozen=True)
class TagsTestData:
    escaped: str
    unescaped: str


TAGS_TESTS = list(itertools.starmap(TagsTestData, [
    ('te\\nst', 'te\nst'),
    ('tes\\\\st', 'tes\\st'),
    ('te😃st', 'te😃st'),
]))


def test_escape_tags():
    for td in TAGS_TESTS:
        val = escape_tag_value(td.unescaped)
        assert val == td.escaped


##


UNESCAPE_TAGS_TESTS = list(itertools.starmap(TagsTestData, [
    ('te\\n\\kst', 'te\nkst'),
    ('te\\n\\kst\\', 'te\nkst'),
    ('te\\\\nst', 'te\\nst'),
    ('te😃st', 'te😃st'),
    ('0\\n1\\n2\\n3\\n4\\n5\\n6\\n\\', '0\n1\n2\n3\n4\n5\n6\n'),
    ('test\\', 'test'),
    ('te\\:st\\', 'te;st'),
    ('te\\:\\st\\', 'te; t'),
    ('\\\\te\\:\\st', '\\te; t'),
    ('test\\', 'test'),
    ('\\', ''),
    ('', ''),
]))


def test_unescape_tags():
    for td in TAGS_TESTS:
        val = unescape_tag_value(td.escaped)
        assert val == td.unescaped

    for td in UNESCAPE_TAGS_TESTS:
        val = unescape_tag_value(td.escaped)
        assert val == td.unescaped


##


@dc.dataclass(frozen=True)
class TagsDecodeTestData:
    raw: str
    tags: dict[str, str]


TAGS_DECODE_DATA_TESTS = list(itertools.starmap(TagsDecodeTestData, [
    ('', {}),
    ('time=12732;re', {'time': '12732', 're': ''}),
    ('time=12732;re=;asdf=5678', {'time': '12732', 're': '', 'asdf': '5678'}),
    ('time=12732;draft/label=b;re=;asdf=5678', {'time': '12732', 're': '', 'asdf': '5678', 'draft/label': 'b'}),
    ('=these;time=12732;=shouldbe;re=;asdf=5678;=ignored', {'time': '12732', 're': '', 'asdf': '5678'}),
    ('dolphin=🐬;time=123456', {'dolphin': '🐬', 'time': '123456'}),
    ('+dolphin=🐬;+draft/fox=f🦊x', {'+dolphin': '🐬', '+draft/fox': 'f🦊x'}),
    ('+dolphin=🐬;+draft/f🦊x=fox', {'+dolphin': '🐬'}),
    ('+dolphin=🐬;+f🦊x=fox', {'+dolphin': '🐬'}),
    ('+dolphin=🐬;f🦊x=fox', {'+dolphin': '🐬'}),
    ('dolphin=🐬;f🦊x=fox', {'dolphin': '🐬'}),
    ('f🦊x=fox;+oragono.io/dolphin=🐬', {'+oragono.io/dolphin': '🐬'}),
    ('a=b;\\/=.', {'a': 'b'}),
]))


def test_decode_tags():
    for td in TAGS_DECODE_DATA_TESTS:
        tags = parse_tags(td.raw)
        assert tags == td.tags


##


# INVALID_TAG_DATA_TESTS = [
#     "label=\xff;batch=c",
#     "label=a\xffb;batch=c",
#     "label=a\xffb",
#     "label=a\xff",
#     "label=a\xff",
#     "label=a\xf0a",
# ]
#
#
# def test_invalid_tags():
#     for td in INVALID_TAG_DATA_TESTS:
#         with pytest.raises(InvalidTagContentError):
#             parse_line_strict(f'@{td} PRIVMSG #chan hi\r\n', True, None)
