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

from .colors import Color
from .colors import parse_rgb
from .styles import Style
from .styles import Theme


##


# The textual-dark palette (see module docstring for provenance).
PRIMARY = parse_rgb('#0178D4')
SECONDARY = parse_rgb('#004578')
FOREGROUND = parse_rgb('#E0E0E0')
BACKGROUND = parse_rgb('#121212')
SURFACE = parse_rgb('#1E1E1E')
WARNING = parse_rgb('#FEA62B')
ERROR = parse_rgb('#B93C5B')

TEXT_PRIMARY = parse_rgb('#57A5E2')
TEXT_SECONDARY = parse_rgb('#5684A5')
TEXT_WARNING = parse_rgb('#FFC473')
TEXT_ERROR = parse_rgb('#D17E92')

MUTED = parse_rgb('#8D8D8D')          # foreground at 60% alpha, pre-blended
SUCCESS = parse_rgb('#71AC84')        # textual's constant-green; the scheme's soft "good" color
STRING_GREEN = parse_rgb('#8AD4A1')
COMMENT_GREY = parse_rgb('#9F9F9F')

CODE_FG = parse_rgb('#D2D2D2')
CODE_INLINE_FG = parse_rgb('#F3BB6E')
CODE_INLINE_BG = parse_rgb('#292014')
QUOTE_BORDER = parse_rgb('#345B7A')


##


def _code(fg: Color | None = None, **kwargs: ta.Any) -> Style:
    return Style(fg=fg, bg=SURFACE, **kwargs)


DARK_THEME = Theme({
    # markdown
    'md.h1': Style(fg=PRIMARY, bold=True),
    'md.h2': Style(fg=PRIMARY, underline=True),
    'md.h3': Style(fg=PRIMARY, bold=True),
    'md.h4': Style(fg=FOREGROUND, bold=True, underline=True),
    'md.h5': Style(fg=FOREGROUND, bold=True),
    'md.h6': Style(fg=MUTED, bold=True),
    'md.bold': Style(bold=True),
    'md.italic': Style(italic=True),
    'md.strike': Style(strike=True),
    'md.code': Style(fg=CODE_FG, bg=SURFACE),
    'md.code.inline': Style(fg=CODE_INLINE_FG, bg=CODE_INLINE_BG),
    'md.quote': Style(fg=MUTED, italic=True),
    'md.quote.marker': Style(fg=QUOTE_BORDER),
    'md.list.marker': Style(fg=TEXT_PRIMARY),
    'md.link': Style(fg=TEXT_PRIMARY, underline=True),
    'md.link.url': Style(fg=TEXT_SECONDARY),
    'md.rule': Style(fg=TEXT_SECONDARY, dim=True),
    'md.table.head': Style(bold=True),
    'md.table.border': Style(fg=TEXT_SECONDARY, dim=True),

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
    'card.expander': Style(fg=TEXT_SECONDARY),
    'card.summary': Style(bold=True),
    'card.summary.dim': Style(fg=TEXT_SECONDARY),
    'card.detail': Style(fg=MUTED),
    'card.glyph.pending': Style(fg=TEXT_SECONDARY),
    'card.glyph.confirming': Style(fg=WARNING),
    'card.glyph.running': Style(fg=TEXT_PRIMARY),
    'card.glyph.complete': Style(fg=SUCCESS),
    'card.glyph.denied': Style(fg=TEXT_ERROR),
    'card.glyph.failed': Style(fg=TEXT_ERROR),
    'card.glyph.cancelled': Style(fg=TEXT_SECONDARY),
    'card.allow': Style(fg=BACKGROUND, bg=SUCCESS, bold=True),
    'card.deny': Style(fg=FOREGROUND, bg=ERROR, bold=True),

    # suggestion popups
    'popup.label': Style(fg=FOREGROUND, bg=SURFACE),
    'popup.desc': Style(fg=TEXT_SECONDARY, bg=SURFACE),
    'popup.selected': Style(fg=FOREGROUND, bg=SECONDARY, bold=True),
    'popup.selected.desc': Style(fg=TEXT_PRIMARY, bg=SECONDARY),

    # vim decorations
    'vim.selection': Style(bg=SECONDARY),
    'vim.cursor': Style(reverse=True),
    'vim.search.match': Style(fg=TEXT_WARNING, bg=CODE_INLINE_BG),
    'vim.search.current': Style(fg=BACKGROUND, bg=WARNING),

    # status line / input (bg-less: inline-friendly; bar-style apps extend with surface-backed variants)
    'status.mode': Style(fg=PRIMARY, bold=True),
    'status.file': Style(fg=FOREGROUND, bold=True),
    'status.spinner': Style(fg=TEXT_PRIMARY),
    'status.dim': Style(fg=TEXT_SECONDARY),
    'status.text': Style(fg=TEXT_SECONDARY),
    'input.glyph': Style(fg=TEXT_PRIMARY, bold=True),
    'error': Style(fg=TEXT_ERROR, bold=True),
})

DEFAULT_THEME = DARK_THEME
