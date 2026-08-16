"""The engine's pure-data feedback surfaces: status for the status bar, decorations for the renderer."""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..docs.positions import Span
from .modes import Mode


##


@dc.dataclass(frozen=True, kw_only=True)
class VimStatus(lang.Final):
    mode: Mode
    pending: str = ''            # keys of an in-progress normal-mode command ('"a2d' ...)
    cmdline: str | None = None   # full command line incl. its ':'/'/'/'?' prefix, when in CMDLINE mode
    message: str = ''            # transient message (errors, ex feedback)
    cursor_count: int = 1        # >1 during multi-cursor (blockwise insert, add_cursor)

    @property
    def mode_text(self) -> str:
        return {
            Mode.NORMAL: '',
            Mode.INSERT: '-- INSERT --',
            Mode.VISUAL: '-- VISUAL --',
            Mode.VISUAL_LINE: '-- VISUAL LINE --',
            Mode.VISUAL_BLOCK: '-- VISUAL BLOCK --',
            Mode.CMDLINE: '',
        }[self.mode]


##


# Decoration tags, resolved to styles by whatever theme the renderer uses.
SELECTION_TAG = 'vim.selection'
CURSOR_TAG = 'vim.cursor'
SEARCH_MATCH_TAG = 'vim.search.match'
SEARCH_CURRENT_TAG = 'vim.search.current'


@dc.dataclass(frozen=True)
class Decoration(lang.Final):
    span: Span
    tag: str


Decorations: ta.TypeAlias = ta.Sequence[Decoration]
