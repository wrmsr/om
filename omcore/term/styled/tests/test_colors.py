from ....text import styled as st
from ..colors import BRIGHT_RED
from ..colors import ColorDepth
from ..colors import IndexedColor
from ..colors import NamedColor
from ..colors import detect_color_depth
from ..colors import downgrade_color
from ..colors import rgb_to_indexed


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
    c = st.parse_rgb('#71AC84')
    assert isinstance(downgrade_color(c, ColorDepth.TRUE), st.RgbColor)
    assert isinstance(downgrade_color(c, ColorDepth.ANSI_256), IndexedColor)
    assert isinstance(downgrade_color(c, ColorDepth.ANSI_16), NamedColor)
    assert downgrade_color(c, ColorDepth.MONO) is None


def test_downgrade_specifics():
    red = st.RgbColor(255, 0, 0)
    assert rgb_to_indexed(red) == IndexedColor(196)
    assert downgrade_color(red, ColorDepth.ANSI_16) == BRIGHT_RED
    assert downgrade_color(IndexedColor(196), ColorDepth.ANSI_16) == BRIGHT_RED
    assert downgrade_color(NamedColor(3), ColorDepth.ANSI_256) == NamedColor(3)
    assert rgb_to_indexed(st.RgbColor(0, 0, 0)) == IndexedColor(16)
    assert rgb_to_indexed(st.RgbColor(255, 255, 255)) == IndexedColor(231)
