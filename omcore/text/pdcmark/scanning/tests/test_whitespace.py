from ..whitespace import is_blank_line
from ..whitespace import scan_ch_repeat


def test_scan_ch_repeat():
    assert scan_ch_repeat('====', 0, '=') == 4
    assert scan_ch_repeat('=== abc', 0, '=') == 3
    assert scan_ch_repeat('x===', 0, '=') == 0
    assert scan_ch_repeat('x===', 1, '=') == 3


def test_is_blank_line():
    assert is_blank_line('')
    assert is_blank_line('   ')
    assert is_blank_line('\t \t')
    assert not is_blank_line('a')
    assert not is_blank_line('  a')
