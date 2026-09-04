"""The target-neutral semantic theme for diff documents."""
from omcore.text import styled as st


##


def _blend(first: st.RgbColor, second: st.RgbColor, amount: float) -> st.RgbColor:
    return st.RgbColor(*(
        round(a + (b - a) * amount)
        for a, b in zip(
            (first.r, first.g, first.b),
            (second.r, second.g, second.b),
        )
    ))


DIFF_BACKGROUND = st.parse_rgb('#0d0f0b')
CODE_BACKGROUND = st.parse_rgb('#272822')
CODE_FOREGROUND = st.parse_rgb('#f8f8f2')
BORDER = st.parse_rgb('#3e4036')

RED = st.parse_rgb('#f92672')
GREEN = st.parse_rgb('#a6e22e')
BLUE = st.parse_rgb('#66d9ef')
CYAN = st.parse_rgb('#66d9ef')
PURPLE = st.parse_rgb('#ae81ff')
YELLOW = st.parse_rgb('#e6db74')
COMMENT = st.parse_rgb('#75715e')

REMOVED_BACKGROUND = _blend(st.RgbColor(255, 0, 0), CODE_BACKGROUND, .85)
ADDED_BACKGROUND = _blend(st.RgbColor(0, 255, 0), CODE_BACKGROUND, .85)
REMOVED_INTRALINE_BACKGROUND = _blend(st.RgbColor(255, 0, 0), CODE_BACKGROUND, .6)
ADDED_INTRALINE_BACKGROUND = _blend(st.RgbColor(0, 255, 0), CODE_BACKGROUND, .6)
REMOVED_INTRALINE_FOREGROUND = _blend(REMOVED_INTRALINE_BACKGROUND, st.RgbColor(255, 255, 255), .8)
ADDED_INTRALINE_FOREGROUND = _blend(ADDED_INTRALINE_BACKGROUND, st.RgbColor(255, 255, 255), .8)


DIFF_STYLE_THEME = st.StyleTheme({
    'diff.summary.changed': st.StylePatch(fg=BLUE),
    'diff.summary.added': st.StylePatch(fg=GREEN),
    'diff.summary.removed': st.StylePatch(fg=RED),
    'diff.summary.count': st.StylePatch(bold=True),
    'diff.bar.added': st.StylePatch(fg=GREEN, bold=True),
    'diff.bar.removed': st.StylePatch(fg=RED, bold=True),

    'diff.header.added': st.StylePatch(fg=GREEN, bold=True),
    'diff.header.old-path': st.StylePatch(dim=True, strike=True),
    'diff.header.path': st.StylePatch(bold=True),
    'diff.header.additions': st.StylePatch(fg=GREEN),
    'diff.header.removals': st.StylePatch(fg=RED),

    'diff.border': st.StylePatch(fg=BORDER),
    'diff.hatched': st.StylePatch(fg=CODE_BACKGROUND, bg=DIFF_BACKGROUND),
    'diff.message.removed': st.StylePatch(fg=RED),
    'diff.message.binary': st.StylePatch(fg=BLUE),
    'diff.message.renamed': st.StylePatch(fg=CYAN),

    'diff.hunk': st.StylePatch(fg=CODE_BACKGROUND, bg=DIFF_BACKGROUND),
    'diff.hunk.marker': st.StylePatch(dim=True),
    'diff.hunk.remove': st.StylePatch(fg=RED, bold=True),
    'diff.hunk.add': st.StylePatch(fg=GREEN, bold=True),
    'diff.hunk.section': st.StylePatch(dim=True),

    'diff.code': st.StylePatch(fg=CODE_FOREGROUND, bg=CODE_BACKGROUND),
    'diff.gutter': st.StylePatch(fg=COMMENT, dim=True),
    'diff.indent': st.StylePatch(fg=COMMENT, dim=True),
    'diff.padding': st.StylePatch(fg=CODE_BACKGROUND, bg=DIFF_BACKGROUND),
    'diff.line.remove': st.StylePatch(bg=REMOVED_BACKGROUND),
    'diff.line.add': st.StylePatch(bg=ADDED_BACKGROUND),
    'diff.intraline.remove': st.StylePatch(
        fg=REMOVED_INTRALINE_FOREGROUND,
        bg=REMOVED_INTRALINE_BACKGROUND,
    ),
    'diff.intraline.add': st.StylePatch(
        fg=ADDED_INTRALINE_FOREGROUND,
        bg=ADDED_INTRALINE_BACKGROUND,
    ),

    # Syntax highlighters use minitui's shared semantic vocabulary. These entries intentionally omit a background so
    # additions/removals remain visible underneath syntax colors.
    'code.keyword': st.StylePatch(fg=RED),
    'code.builtin': st.StylePatch(fg=BLUE),
    'code.def': st.StylePatch(fg=GREEN),
    'code.string': st.StylePatch(fg=YELLOW),
    'code.comment': st.StylePatch(fg=COMMENT, italic=True),
    'code.number': st.StylePatch(fg=PURPLE),
    'code.decorator': st.StylePatch(fg=GREEN),
    'code.type': st.StylePatch(fg=BLUE),
})
