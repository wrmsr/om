import pytest

from omcore.text import styled as st

from ..colors import ColorDepth
from ..colors import IndexedColor
from ..colors import NamedColor
from ..colors import RgbColor
from ..colors import detect_color_depth
from ..colors import downgrade_color
from ..colors import parse_rgb


def test_parse_rgb():
    assert RgbColor is st.RgbColor
    assert parse_rgb('#0178D4') == RgbColor(0x01, 0x78, 0xD4)
    assert parse_rgb('#000000') == RgbColor(0, 0, 0)
    assert parse_rgb('#ffffff') == RgbColor(255, 255, 255)
    assert parse_rgb('#abc') == RgbColor(0xAA, 0xBB, 0xCC)


def test_parse_rgb_rejects():
    for bad in ('0178D4', '#0178D', '#0178D4FF', '#12', '', '#'):
        with pytest.raises(Exception):  # noqa: B017, PT011
            parse_rgb(bad)


def test_detect_color_depth():
    assert detect_color_depth({'COLORTERM': 'truecolor'}) is ColorDepth.TRUE
    assert detect_color_depth({'COLORTERM': '24bit', 'TERM': 'xterm'}) is ColorDepth.TRUE
    assert detect_color_depth({'TERM': 'xterm-256color'}) is ColorDepth.ANSI_256
    assert detect_color_depth({'TERM': 'screen-256color'}) is ColorDepth.ANSI_256
    assert detect_color_depth({'TERM': 'xterm-direct'}) is ColorDepth.TRUE
    assert detect_color_depth({'TERM': 'dumb'}) is ColorDepth.MONO
    assert detect_color_depth({'TERM': 'vt100'}) is ColorDepth.ANSI_16
    assert detect_color_depth({}) is ColorDepth.ANSI_16


def test_parsed_rgb_downgrades():
    c = parse_rgb('#71AC84')
    assert isinstance(downgrade_color(c, ColorDepth.TRUE), RgbColor)
    assert isinstance(downgrade_color(c, ColorDepth.ANSI_256), IndexedColor)
    assert isinstance(downgrade_color(c, ColorDepth.ANSI_16), NamedColor)
    assert downgrade_color(c, ColorDepth.MONO) is None
