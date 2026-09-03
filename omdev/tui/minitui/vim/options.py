"""
Editor options - the vim trio (tabstop / shiftwidth / expandtab), autoindent, and the line number column - plus a small
language registry.

This is deliberately a carveout, not a full 'set' system: a general-purpose code editor isn't the point, but the
stack shouldn't preclude one. Language profiles mirror the highlighter registry's alias style (text/highlights.py):
names resolve leniently and unknown names get the defaults, since chat-adjacent callers feed arbitrary strings.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class VimOptions(lang.Final):
    tabstop: int = 4         # display width of a literal tab
    shiftwidth: int = 4      # indent step for < / >
    expandtab: bool = True   # insert-mode tab inserts spaces (to the next tabstop column)
    autoindent: bool = True  # insert-mode Enter carries the current line's leading whitespace
    number: bool = False     # show a line number column (a view concern - the engine never reads it)
    numberwidth: int = 4     # that column's minimum width, trailing space included; grows to fit the last line number


DEFAULT_OPTIONS = VimOptions()


##


_TAB_OPTIONS = VimOptions(expandtab=False)
_TWO_SPACE_OPTIONS = VimOptions(tabstop=2, shiftwidth=2)

_LANGUAGE_OPTIONS: ta.Mapping[str, VimOptions] = {
    'go': _TAB_OPTIONS,
    'golang': _TAB_OPTIONS,
    'make': _TAB_OPTIONS,
    'makefile': _TAB_OPTIONS,

    'yaml': _TWO_SPACE_OPTIONS,
    'yml': _TWO_SPACE_OPTIONS,
    'json': _TWO_SPACE_OPTIONS,
}


def get_language_options(name: str | None = None) -> VimOptions:
    """Options for a language name ('go' -> real tabs, 'yaml' -> 2-space); unknown or None -> the 4-space defaults."""

    if name is None:
        return DEFAULT_OPTIONS
    return _LANGUAGE_OPTIONS.get(name.strip().lower(), DEFAULT_OPTIONS)


##


def indent_columns(indent: str, tabstop: int) -> int:
    """The display width of a leading-whitespace string: tabs advance to the next tabstop multiple."""

    cols = 0
    for c in indent:
        cols = (cols // tabstop + 1) * tabstop if c == '\t' else cols + 1
    return cols


def make_indent(cols: int, options: VimOptions) -> str:
    """The indent string for a column width, per expandtab: spaces, or tabs plus a space remainder."""

    if cols <= 0:
        return ''
    if options.expandtab:
        return ' ' * cols
    return '\t' * (cols // options.tabstop) + ' ' * (cols % options.tabstop)
