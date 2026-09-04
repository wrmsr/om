"""
The built-in theme: a soft dark scheme derived from Textual's default "textual-dark" (v8.1.1).

Color values are copied from the resolved dump at `omdev/tui/rich/textual/dark.py` (Textual's `$variable` references and
alpha blending pre-computed against its `#121212` page background) - minitui does not import omdev. Colors are authored
as truecolor and downgrade automatically on lesser terminals via `colors.downgrade_color`; surfaces pick the depth from
the environment (`colors.detect_color_depth`).

Deliberate divergences from the dump, for terminal reality:

  * The code-block background uses the `surface` tint (#1E1E1E) rather than Textual's fence #101010 - darker-than-page
    is invisible on the near-black terminals this assumes-dark scheme targets.
  * `code.def` trades Textual's underline for bold - underline is noisy in editable textareas.
  * Syntax styles carry the code-block background themselves (fence content is tagged only `code.*`; there is no
    bg-inheritance rule). Fullscreen-editor apps that want untinted syntax override `code.*` via `Theme.extend`.

Apps layer their local tags over `DEFAULT_THEME` with `Theme.extend`.
"""
import typing as ta

from omcore.text import styled as st

from .styles import Theme


##


# The textual-dark palette (see module docstring for provenance).
PRIMARY = st.parse_rgb('#0178D4')
SECONDARY = st.parse_rgb('#004578')
FOREGROUND = st.parse_rgb('#E0E0E0')
BACKGROUND = st.parse_rgb('#121212')
SURFACE = st.parse_rgb('#1E1E1E')
WARNING = st.parse_rgb('#FEA62B')
ERROR = st.parse_rgb('#B93C5B')

TEXT_PRIMARY = st.parse_rgb('#57A5E2')
TEXT_SECONDARY = st.parse_rgb('#5684A5')
TEXT_WARNING = st.parse_rgb('#FFC473')
TEXT_ERROR = st.parse_rgb('#D17E92')

MUTED = st.parse_rgb('#8D8D8D')          # foreground at 60% alpha, pre-blended
SUCCESS = st.parse_rgb('#71AC84')        # textual's constant-green; the scheme's soft "good" color
STRING_GREEN = st.parse_rgb('#8AD4A1')
COMMENT_GREY = st.parse_rgb('#9F9F9F')

CODE_FG = st.parse_rgb('#D2D2D2')
CODE_INLINE_FG = st.parse_rgb('#F3BB6E')
CODE_INLINE_BG = st.parse_rgb('#292014')
QUOTE_BORDER = st.parse_rgb('#345B7A')


##


def _code(fg: st.Color | None = None, **kwargs: ta.Any) -> st.StylePatch:
    return st.StylePatch(fg=fg, bg=SURFACE, **kwargs)


DARK_THEME = Theme({
    # markdown
    'md.h1': st.StylePatch(fg=PRIMARY, bold=True),
    'md.h2': st.StylePatch(fg=PRIMARY, underline=True),
    'md.h3': st.StylePatch(fg=PRIMARY, bold=True),
    'md.h4': st.StylePatch(fg=FOREGROUND, bold=True, underline=True),
    'md.h5': st.StylePatch(fg=FOREGROUND, bold=True),
    'md.h6': st.StylePatch(fg=MUTED, bold=True),
    'md.bold': st.StylePatch(bold=True),
    'md.italic': st.StylePatch(italic=True),
    'md.strike': st.StylePatch(strike=True),
    'md.code': st.StylePatch(fg=CODE_FG, bg=SURFACE),
    'md.code.inline': st.StylePatch(fg=CODE_INLINE_FG, bg=CODE_INLINE_BG),
    'md.quote': st.StylePatch(fg=MUTED, italic=True),
    'md.quote.marker': st.StylePatch(fg=QUOTE_BORDER),
    'md.list.marker': st.StylePatch(fg=TEXT_PRIMARY),
    'md.link': st.StylePatch(fg=TEXT_PRIMARY, underline=True),
    'md.link.url': st.StylePatch(fg=TEXT_SECONDARY),
    'md.rule': st.StylePatch(fg=TEXT_SECONDARY, dim=True),
    'md.table.head': st.StylePatch(bold=True),
    'md.table.border': st.StylePatch(fg=TEXT_SECONDARY, dim=True),

    # syntax (from the dump's resolved pygments token styles)
    'code.keyword': _code(TEXT_WARNING),
    'code.builtin': _code(TEXT_WARNING),
    'code.def': _code(TEXT_WARNING, bold=True),
    'code.string': _code(STRING_GREEN),
    'code.comment': _code(COMMENT_GREY, italic=True),
    'code.number': _code(TEXT_WARNING),
    'code.decorator': _code(TEXT_PRIMARY, bold=True),
    'code.type': _code(SUCCESS, bold=True),
    'code.diff.add': _code(STRING_GREEN),
    'code.diff.del': _code(TEXT_ERROR),
    'code.diff.hunk': _code(TEXT_PRIMARY),
    'code.diff.meta': _code(COMMENT_GREY),

    # tool cards
    'card.expander': st.StylePatch(fg=TEXT_SECONDARY),
    'card.summary': st.StylePatch(bold=True),
    'card.summary.dim': st.StylePatch(fg=TEXT_SECONDARY),
    'card.detail': st.StylePatch(fg=MUTED),
    'card.glyph.pending': st.StylePatch(fg=TEXT_SECONDARY),
    'card.glyph.confirming': st.StylePatch(fg=WARNING),
    'card.glyph.running': st.StylePatch(fg=TEXT_PRIMARY),
    'card.glyph.complete': st.StylePatch(fg=SUCCESS),
    'card.glyph.denied': st.StylePatch(fg=TEXT_ERROR),
    'card.glyph.failed': st.StylePatch(fg=TEXT_ERROR),
    'card.glyph.cancelled': st.StylePatch(fg=TEXT_SECONDARY),
    'card.allow': st.StylePatch(fg=BACKGROUND, bg=SUCCESS, bold=True),
    'card.deny': st.StylePatch(fg=FOREGROUND, bg=ERROR, bold=True),

    # suggestion popups
    'popup.label': st.StylePatch(fg=FOREGROUND, bg=SURFACE),
    'popup.desc': st.StylePatch(fg=TEXT_SECONDARY, bg=SURFACE),
    'popup.selected': st.StylePatch(fg=FOREGROUND, bg=SECONDARY, bold=True),
    'popup.selected.desc': st.StylePatch(fg=TEXT_PRIMARY, bg=SECONDARY),

    # vim decorations
    'vim.selection': st.StylePatch(bg=SECONDARY),
    'vim.cursor': st.StylePatch(reverse=True),
    'vim.search.match': st.StylePatch(fg=TEXT_WARNING, bg=CODE_INLINE_BG),
    'vim.search.current': st.StylePatch(fg=BACKGROUND, bg=WARNING),
    'vim.linenr': st.StylePatch(fg=TEXT_SECONDARY),

    # status line / input (bg-less: inline-friendly; bar-style apps extend with surface-backed variants)
    'status.mode': st.StylePatch(fg=PRIMARY, bold=True),
    'status.file': st.StylePatch(fg=FOREGROUND, bold=True),
    'status.spinner': st.StylePatch(fg=TEXT_PRIMARY),
    'status.dim': st.StylePatch(fg=TEXT_SECONDARY),
    'status.text': st.StylePatch(fg=TEXT_SECONDARY),
    'input.glyph': st.StylePatch(fg=TEXT_PRIMARY, bold=True),
    'error': st.StylePatch(fg=TEXT_ERROR, bold=True),
})

DEFAULT_THEME = DARK_THEME
