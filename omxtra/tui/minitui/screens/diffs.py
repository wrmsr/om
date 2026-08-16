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
# Derived from x/term/pyrepl's render.py diff + unix/console.py refresh planning (themselves from cpython's _pyrepl).
# Notable changes: the ich1/dch1 single-character insert/delete update kinds are dropped (they optimize for baud-rate
# constraints that no longer exist; the diff already reduces typing to a small span rewrite) - updates are uniformly
# "move, write cells, maybe erase-to-eol". 'controls' cell handling is gone with the controls cells themselves.
"""
Retained-frame diffing: the correctness ground truth of the renderer.

Every present() diffs the new frame against the retained previous frame and emits only changed spans. Upstream damage
tracking (controls marking themselves dirty) may *skip re-rendering*, but never skips this diff - a spurious
invalidation costs a re-render and an empty diff, not visible output.
"""
import dataclasses as dc

from .cells import Cell
from .cells import CursorXY
from .cells import Frame
from .cells import Line


##


@dc.dataclass(frozen=True, slots=True)
class LineUpdate:
    """
    One changed span within one row: move to (start_x, y), write `cells`, optionally erase to end of line.

    `clear_eol` is set when the new row is narrower than the old one, so stale cells to the right must be erased.
    """

    y: int
    start_x: int
    cells: tuple[Cell, ...]
    clear_eol: bool = False

    @property
    def width(self) -> int:
        return sum(cell.width for cell in self.cells)


def diff_lines(old: Line, new: Line, y: int) -> LineUpdate | None:
    """Return the minimal update turning `old` into `new` on row `y`, or None if identical."""

    if old == new:
        return None

    old_cells = old.cells
    new_cells = new.cells

    prefix = 0
    start_x = 0
    max_prefix = min(len(old_cells), len(new_cells))
    while prefix < max_prefix and old_cells[prefix] == new_cells[prefix]:
        start_x += old_cells[prefix].width
        prefix += 1

    old_suffix = len(old_cells)
    new_suffix = len(new_cells)
    while old_suffix > prefix and new_suffix > prefix:
        if old_cells[old_suffix - 1] != new_cells[new_suffix - 1]:
            break
        old_suffix -= 1
        new_suffix -= 1

    # Never split a base character from its trailing zero-width combiners... which cannot happen here, since combining
    # characters are merged into their base Cell upstream. What *can* differ is width: if the changed spans cover
    # different column counts, everything from the change onward must be rewritten.
    old_changed = old_cells[prefix:old_suffix]
    new_changed = new_cells[prefix:new_suffix]

    old_changed_width = sum(cell.width for cell in old_changed)
    new_changed_width = sum(cell.width for cell in new_changed)

    if old_changed_width == new_changed_width:
        return LineUpdate(
            y=y,
            start_x=start_x,
            cells=new_changed,
        )

    return LineUpdate(
        y=y,
        start_x=start_x,
        cells=new_cells[prefix:],
        clear_eol=old.width > new.width,
    )


##


@dc.dataclass(frozen=True, slots=True)
class FrameDiff:
    """
    The plan for turning the displayed (retained) frame into a new one.

    `line_updates` cover rows present in both frames; `appended` rows extend the live region downward (the surface
    creates them, forcing terminal scroll as needed); `shrink` rows are erased from the bottom. Application order:
    grow, update, shrink, cursor.
    """

    old_height: int
    height: int
    line_updates: tuple[LineUpdate, ...]
    appended: tuple[Line, ...]
    cursor: CursorXY
    cursor_visible: bool

    @property
    def shrink(self) -> int:
        return max(self.old_height - self.height, 0)

    @property
    def is_empty(self) -> bool:
        return not self.line_updates and not self.appended and self.shrink == 0


def diff_frames(old: Frame, new: Frame) -> FrameDiff:
    common = min(old.height, new.height)

    line_updates: list[LineUpdate] = []
    for y in range(common):
        if (update := diff_lines(old.lines[y], new.lines[y], y)) is not None:
            line_updates.append(update)

    # Rows the old frame had beyond the new height are handled as shrink; rows the new frame adds are appends.
    return FrameDiff(
        old_height=old.height,
        height=new.height,
        line_updates=tuple(line_updates),
        appended=new.lines[common:] if new.height > old.height else (),
        cursor=new.cursor,
        cursor_visible=new.cursor_visible,
    )
