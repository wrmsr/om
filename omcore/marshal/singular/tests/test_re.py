import re

from ....re import regex_to_string
from ...globals import marshal
from ...globals import unmarshal


def test_datetime_roundtrip():
    pat = re.compile('foo')
    pat2 = unmarshal(marshal(pat), pat)
    assert isinstance(pat2, re.Pattern)
    assert regex_to_string(pat) == 'foo'
