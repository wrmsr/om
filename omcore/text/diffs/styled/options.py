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

    def __post_init__(self) -> None:
        check.arg(isinstance(self.width, int) and not isinstance(self.width, bool) and self.width >= 20)
        check.arg(isinstance(self.tab_size, int) and not isinstance(self.tab_size, bool) and self.tab_size >= 1)
        check.arg(isinstance(self.syntax_highlighting, bool))
        check.in_(self.layout, DIFF_LAYOUTS)
        check.arg(isinstance(self.auto_split_width, int) and not isinstance(self.auto_split_width, bool))

    @property
    def resolved_layout(self) -> ta.Literal['split', 'unified']:
        if self.layout == 'auto':
            return 'split' if self.width >= self.auto_split_width else 'unified'
        return self.layout
