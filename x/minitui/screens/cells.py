# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and the Individual or Organization
# ("Licensee") accessing and otherwise using this software ("Python") in source or binary form and its associated
# documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby grants Licensee a nonexclusive,
# royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative
# works, distribute, and otherwise use Python alone or in any derivative version, provided, however, that PSF's License
# Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
# 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 Python Software Foundation; All Rights Reserved" are retained in Python
# alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or incorporates Python or any part thereof, and
# wants to make the derivative work available to others as provided herein, then Licensee hereby agrees to include in
# any such work a brief summary of the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS" basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES,
# EXPRESS OR IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY
# OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT INFRINGE ANY THIRD PARTY
# RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL
# DAMAGES OR LOSS AS A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF
# ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any relationship of agency, partnership, or joint
# venture between PSF and Licensee.  This License Agreement does not grant permission to use PSF trademarks or trade
# name in a trademark sense to endorse or promote products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee agrees to be bound by the terms and conditions of this
# License Agreement.
# Derived from x/term/pyrepl/render.py (itself from cpython's _pyrepl), restructured onto minitui's structured Style
# model. Notable changes: embedded escape sequences ('controls' cells) are gone entirely - frames hold only structured
# content - and rendered SGR strings are produced on demand per color depth rather than cached on the line.
"""
The frame model: one terminal cell / row / screenful of structured, resolved content.

A `Cell` is one displayed grapheme (a base character plus any trailing zero-width combining characters), its column
width, and its fully-resolved `Style` (semantic tags are resolved by a theme *before* this layer). A `Line` is a row
of cells; a `Frame` is the whole live region: lines plus cursor state. All frozen, all comparable - diffing (see
`diffs.py`) is plain structural comparison.
"""
import dataclasses as dc
import typing as ta

from omcore import check

from ..text.colors import ColorDepth
from ..text.segments import Segments
from ..text.sgr import RESET_SGR
from ..text.sgr import style_sgr
from ..text.styles import EMPTY_STYLE
from ..text.styles import Style
from ..text.styles import Theme
from ..text.widths import char_width


CursorXY: ta.TypeAlias = tuple[int, int]  # (column, row)


##


@dc.dataclass(frozen=True, slots=True)
class Cell:
    """
    One terminal cell: a grapheme, its column width, and its resolved style.

    A screen row like ``>>> def`` is a sequence of cells::

        >  >  >     d  e  f
       ╰─╯╰─╯╰─╯╰─╯╰─╯╰─╯╰─╯
    """

    text: str
    width: int
    style: Style = EMPTY_STYLE


@dc.dataclass(frozen=True, slots=True)
class Line:
    """One screen row as a tuple of cells. `width` is the total visible column count."""

    cells: tuple[Cell, ...]
    width: int

    @classmethod
    def from_cells(cls, cells: ta.Iterable[Cell]) -> Line:
        cell_tuple = tuple(cells)
        return cls(
            cells=cell_tuple,
            width=sum(cell.width for cell in cell_tuple),
        )

    @property
    def text(self) -> str:
        return ''.join(cell.text for cell in self.cells)


EMPTY_LINE = Line(cells=(), width=0)


@dc.dataclass(frozen=True, slots=True)
class Frame:
    """
    The complete live-region content: rows of cells plus cursor state.

    Row 0 is the top of the live region; all coordinates are live-region-relative. Frames are final composed content -
    overlay compositing (popups etc.) happens upstream in the controls layer.
    """

    lines: tuple[Line, ...]
    cursor: CursorXY = (0, 0)
    cursor_visible: bool = True

    @property
    def height(self) -> int:
        return len(self.lines)

    @classmethod
    def empty(cls) -> Frame:
        return cls(())


EMPTY_FRAME = Frame.empty()


##


def cells_from_text(text: str, style: Style = EMPTY_STYLE) -> ta.Iterator[Cell]:
    """
    Convert plain printable text into cells, merging zero-width combining characters into their base cell.

    The text must be pre-sanitized: no escapes, newlines, tabs, or control characters.
    """

    pending: Cell | None = None
    for c in text:
        w = char_width(c)
        if w == 0 and pending is not None:
            pending = Cell(pending.text + c, pending.width, pending.style)
            continue
        if pending is not None:
            yield pending
        pending = Cell(c, w, style)
    if pending is not None:
        yield pending


def line_from_segments(segments: Segments, theme: Theme) -> Line:
    cells: list[Cell] = []
    for segment in segments:
        cells.extend(cells_from_text(segment.text, theme.resolve(segment.style)))
    return Line.from_cells(cells)


##


def render_cells(
        cells: ta.Iterable[Cell],
        depth: ColorDepth = ColorDepth.TRUE,
        *,
        debug_style: str | None = None,
) -> str:
    """
    Render cells into a terminal string with SGR escapes.

    Tracks the active style to emit escapes only on change, minimizing output bytes. If `debug_style` is given (redraw
    visualization), it is appended to every emitted escape.
    """

    rendered: list[str] = []
    active = ''
    for cell in cells:
        check.state(bool(cell.text))
        target = style_sgr(cell.style, depth)
        if debug_style is not None:
            target = (target or RESET_SGR) + debug_style
        if target != active:
            if active and not target:
                rendered.append(RESET_SGR)
            elif target:
                rendered.append(target)
            active = target
        rendered.append(cell.text)

    if active:
        rendered.append(RESET_SGR)
    return ''.join(rendered)
