from ..plain import render_plain
from ..styles import StylePatch
from ..text import StyledText


def test_render_plain():
    text = StyledText('<hello>\nworld').styled(StylePatch(bold=True))

    assert render_plain(text) == '<hello>\nworld'
    assert render_plain('plain') == 'plain'
