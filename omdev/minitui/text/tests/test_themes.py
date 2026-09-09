"""DEFAULT_THEME must cover the full library tag vocabulary with soft (non-ANSI-named) colors."""
from omcore.term.styled import NamedColor

from ...controls.cards import CardState
from ..styles import EMPTY_STYLE
from ..styles import Style
from ..themes import DEFAULT_THEME


# Every tag emitted by library (non-app) code. Additions to the library vocabulary belong here AND in DEFAULT_THEME.
LIBRARY_TAGS = (
    *(f'md.h{i}' for i in range(1, 7)),
    'md.bold',
    'md.italic',
    'md.strike',
    'md.code',
    'md.code.inline',
    'md.quote',
    'md.quote.marker',
    'md.list.marker',
    'md.link',
    'md.link.url',
    'md.rule',

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

    'card.expander',
    'card.summary',
    'card.summary.dim',
    'card.detail',
    'card.allow',
    'card.deny',
    *(f'card.glyph.{state.name.lower()}' for state in CardState),

    'popup.label',
    'popup.desc',
    'popup.selected',
    'popup.selected.desc',

    'vim.selection',
    'vim.cursor',
    'vim.search.match',
    'vim.search.current',
)


def test_default_theme_covers_library_tags():
    missing = [tag for tag in LIBRARY_TAGS if DEFAULT_THEME.resolve(tag) == EMPTY_STYLE]
    assert not missing, f'DEFAULT_THEME misses library tags: {missing}'


def test_default_theme_uses_no_ansi_named_colors():
    # The whole point: no bright ANSI red/green anywhere - everything is authored truecolor.
    offenders = [
        tag
        for tag in LIBRARY_TAGS
        for style in [DEFAULT_THEME.resolve(tag)]
        if isinstance(style.fg, NamedColor) or isinstance(style.bg, NamedColor)
    ]
    assert not offenders, f'named ANSI colors in: {offenders}'


def test_extend_overlays():
    t = DEFAULT_THEME.extend({'md.h1': Style(bold=True), 'app.local': Style(italic=True)})
    assert t.resolve('md.h1') == Style(bold=True)
    assert t.resolve('app.local') == Style(italic=True)
    assert t.resolve('md.h2') == DEFAULT_THEME.resolve('md.h2')
