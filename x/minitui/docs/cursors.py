"""
Cursor state.

Cursors are held as a tuple, primary first, from day one - single-cursor code reads `cursors[0]` - so multi-cursor
support is an implementation project later, not an architecture project. `want` is vim's curswant: the column j/k
aim for; `WANT_EOL`-large values pin to end of line.
"""
from omcore import dataclasses as dc
from omcore import lang

from .positions import Pos


##


@dc.dataclass(frozen=True)
class Cursor(lang.Final):
    pos: Pos

    _: dc.KW_ONLY

    want: int = 0
