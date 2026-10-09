# Copyright (c) 2025 Darren Burns
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""Options for laying out a patch set as a styled document."""
import typing as ta

from .... import check
from .... import dataclasses as dc
from .... import lang


DiffLayout: ta.TypeAlias = ta.Literal[
    'auto',
    'split',
    'unified',
]


##


DIFF_LAYOUTS: ta.Sequence[DiffLayout] = ta.get_args(DiffLayout)


def _check_limit(value: int | None) -> None:
    if value is not None:
        check.arg(isinstance(value, int) and not isinstance(value, bool) and value >= 0)


@dc.dataclass(frozen=True, kw_only=True)
class DiffContextLimits(lang.Final):
    """
    How big a file a document will highlight whole, for context its hunks lack on their own. Whole-file highlighting
    takes time in proportion to the file - some tens of microseconds a line, in a terminal ui on its event loop - so a
    bigger file's hunks are highlighted on their own instead. None is no limit.
    """

    # About 80ms of highlighting.
    max_lines: int | None = 2_000

    # A catch for few, long lines - minified or generated text - which a line count lets through.
    max_bytes: int | None = 256 * 1024

    def __post_init__(self) -> None:
        _check_limit(self.max_lines)
        _check_limit(self.max_bytes)

    def admits_size(self, size: int) -> bool:
        return self.max_bytes is None or size <= self.max_bytes

    def admits(self, lines: ta.Sequence[str]) -> bool:
        if self.max_lines is not None and len(lines) > self.max_lines:
            return False

        if self.max_bytes is not None:
            size = 0
            for line in lines:
                size += len(line.encode('utf-8', 'surrogatepass')) + 1
                if size > self.max_bytes:
                    return False

        return True


@dc.dataclass(frozen=True)
class DiffStyledDocOptions(lang.Final):
    width: int = 80
    tab_size: int = 4
    syntax_highlighting: bool = True

    _: dc.KW_ONLY

    # How each hunk's lines are laid out: old and new side by side ('split'), or one beneath the other with every line
    # given the full width ('unified'). Under 'auto', split from `auto_split_width` up and unified below it.
    layout: DiffLayout = 'auto'

    # Below this width the split layout's halves keep fewer than about 75 columns of code each, and truncation sets in
    # on ordinary lines. Unified never truncates sooner than split, so it gets everything narrower.
    auto_split_width: int = 160

    context_limits: DiffContextLimits = DiffContextLimits()

    def __post_init__(self) -> None:
        check.arg(isinstance(self.width, int) and not isinstance(self.width, bool) and self.width >= 20)
        check.arg(isinstance(self.tab_size, int) and not isinstance(self.tab_size, bool) and self.tab_size >= 1)
        check.arg(isinstance(self.syntax_highlighting, bool))
        check.in_(self.layout, DIFF_LAYOUTS)
        check.arg(isinstance(self.auto_split_width, int) and not isinstance(self.auto_split_width, bool))
        check.isinstance(self.context_limits, DiffContextLimits)

    @property
    def resolved_layout(self) -> ta.Literal['split', 'unified']:
        if self.layout == 'auto':
            return 'split' if self.width >= self.auto_split_width else 'unified'
        return self.layout
