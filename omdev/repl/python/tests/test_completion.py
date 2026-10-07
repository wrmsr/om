import os

from ..completion import complete_python
from ..completion import extract_stem


##


def texts(completions):
    return [c.text for c in completions]


def test_extract_stem():
    assert extract_stem('print(os.pa', 11) == 'os.pa'
    assert extract_stem('x = foo', 7) == 'foo'
    assert extract_stem('x = foo', 3) == ''
    assert extract_stem('a b', 1) == 'a'


def test_bare_names():
    ns = {'alpha': 1, 'alpine': 2, '_private': 3, '__builtins__': {'print': print, 'abs': abs}}
    assert texts(complete_python(ns, 'al', 2)) == ['alpha', 'alpine']
    assert texts(complete_python(ns, 'pri', 3)) == ['print']
    assert texts(complete_python(ns, 'whi', 3)) == ['while']
    assert texts(complete_python(ns, '_p', 2)) == ['_private']
    assert texts(complete_python(ns, 'zzz', 3)) == []
    assert complete_python(ns, '', 0) == []


def test_attributes():
    ns = {'os': os}
    got = texts(complete_python(ns, 'os.pa', 5))
    assert 'os.path' in got
    assert all(t.startswith('os.pa') for t in got)
    assert texts(complete_python(ns, 'os.path.jo', 10)) == ['os.path.join']
    assert texts(complete_python(ns, 'nope.x', 6)) == []
    assert texts(complete_python(ns, 'os.nope.x', 9)) == []
    assert texts(complete_python(ns, 'f().x', 5)) == []  # never evaluates a call


def test_private_attributes_only_when_asked():
    class C:
        pub = 1
        _priv = 2

    ns = {'c': C()}
    assert texts(complete_python(ns, 'c.', 2)) == ['c.pub']
    assert 'c._priv' in texts(complete_python(ns, 'c._', 3))
