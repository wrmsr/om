"""
The repl's theme tags: layered over minitui's default theme by `REPL_THEME`, or merged into a host app's own theme via
`REPL_STYLES`.

Highlighters emit `code.*` tags, which the default theme paints on a code-block background - right for markdown fences,
wrong for an input box. Rather than untint `code.*` globally (a host app's fences would lose their background), the
input's highlighter is wrapped to re-emit its tags under `repl.code.*`, defined here untinted.
"""
import typing as ta

from ...minitui.text.styles import Style
from ...minitui.text.styles import Theme
from ...minitui.text.themes import CODE_FG
from ...minitui.text.themes import DEFAULT_THEME
from ...minitui.text.themes import FOREGROUND
from ...minitui.text.themes import PRIMARY
from ...minitui.text.themes import TEXT_ERROR
from ...minitui.text.themes import TEXT_PRIMARY
from ...minitui.text.themes import TEXT_SECONDARY


##


CODE_TAG_PREFIX = 'repl.'

_CODE_TAGS: ta.Sequence[str] = (
    'code.keyword',
    'code.builtin',
    'code.def',
    'code.string',
    'code.comment',
    'code.number',
    'code.decorator',
    'code.type',
    'code.diff.add',
    'code.diff.del',
    'code.diff.hunk',
    'code.diff.meta',
)


def _untinted_code_styles() -> dict[str, Style]:
    out: dict[str, Style] = {}
    for tag in _CODE_TAGS:
        style = DEFAULT_THEME.resolve(tag)
        out[CODE_TAG_PREFIX + tag] = Style(fg=style.fg, bold=style.bold, italic=style.italic)
    return out


REPL_STYLES: ta.Mapping[str, Style] = {
    'repl.prompt': Style(fg=TEXT_PRIMARY, bold=True),
    'repl.language': Style(fg=PRIMARY, bold=True),
    'repl.echo': Style(fg=CODE_FG),
    'repl.stdout': Style(fg=FOREGROUND),
    'repl.result': Style(fg=TEXT_PRIMARY),
    'repl.error': Style(fg=TEXT_ERROR),
    'repl.note': Style(fg=TEXT_SECONDARY, italic=True),
    **_untinted_code_styles(),
}

REPL_THEME: Theme = DEFAULT_THEME.extend(REPL_STYLES)
