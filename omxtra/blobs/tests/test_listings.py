import datetime

from ..listings import shallow_list
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobVersion


def _infos(*keys):
    return [
        BlobInfo(key=k, size=0, version=BlobVersion(k), last_modified=datetime.datetime.now(tz=datetime.UTC))
        for k in sorted(keys)
    ]


def _render(es):
    return [('P:' + e.prefix) if isinstance(e, BlobPrefix) else e.key for e in es]


def test_nested():
    infos = _infos('a/b', 'a/c/d', 'a/c/e', 'a/f', 'a/g/h/i')
    assert _render(shallow_list(infos, prefix='a/', delimiter='/')) == ['a/b', 'P:a/c/', 'a/f', 'P:a/g/']


def test_prefix_without_delimiter():
    infos = _infos('a/b', 'ab/c', 'abc', 'ab')
    assert _render(shallow_list(infos, prefix='a', delimiter='/')) == ['P:a/', 'ab', 'P:ab/', 'abc']


def test_prefix_is_key():
    infos = _infos('a', 'a/b')
    assert _render(shallow_list(infos, prefix='a', delimiter='/')) == ['a', 'P:a/']


def test_other_delimiter():
    infos = _infos('x|y|z', 'x|w', 'xy')
    assert _render(shallow_list(infos, prefix='x|', delimiter='|')) == ['x|w', 'P:x|y|']
    assert _render(shallow_list(infos, prefix='', delimiter='|')) == ['xy', 'P:x|']
