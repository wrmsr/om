import io

from ..optionfile import Parser


_CFG_FILE = r"""
[default]
string = foo
quoted = "bar"
single_quoted = 'foobar'
skip-slave-start
"""


def test_string():
    parser = Parser()
    parser.read_file(io.StringIO(_CFG_FILE))
    assert parser.get('default', 'string') == 'foo'
    assert parser.get('default', 'quoted') == 'bar'
    assert parser.get('default', 'single-quoted') == 'foobar'
