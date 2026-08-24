# Copyright (c) 2020 Will McGugan
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
import typing as ta

from ._utils.loops import loop_last
from .segment import Segment
from .styles.styles import StyleType


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import RenderableType
    from .console import RenderResult


##


class Screen:
    """
    A renderable that fills the terminal screen and crops excess.

    Args:
        renderable (RenderableType): Child renderable.
        style (StyleType, optional): Optional background style. Defaults to None.
    """

    renderable: RenderableType

    def __init__(
            self,
            *renderables: RenderableType,
            style: StyleType | None = None,
            application_mode: bool = False,
    ) -> None:
        from .console import Group

        self.renderable = Group(*renderables)
        self.style = style
        self.application_mode = application_mode

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width, height = options.size
        style = console.get_style(self.style) if self.style else None
        render_options = options.update(width=width, height=height)
        lines = console.render_lines(
            self.renderable or '', render_options, style=style, pad=True,
        )
        lines = Segment.set_shape(lines, width, height, style=style)
        new_line = Segment('\n\r') if self.application_mode else Segment.line()
        for last, line in loop_last(lines):
            yield from line
            if not last:
                yield new_line
