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

from .measure import Measurement


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import RenderableType
    from .console import RenderResult


##


class Constrain:
    """
    Constrain the width of a renderable to a given number of characters.

    Args:
        renderable (RenderableType): A renderable object.
        width (int, optional): The maximum width (in characters) to render. Defaults to 80.
    """

    def __init__(self, renderable: RenderableType, width: int | None = 80) -> None:
        self.renderable = renderable
        self.width = width

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        if self.width is None:
            yield self.renderable
        else:
            child_options = options.update_width(min(self.width, options.max_width))
            yield from console.render(self.renderable, child_options)

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        if self.width is not None:
            options = options.update_width(self.width)
        measurement = Measurement.get(console, options, self.renderable)
        return measurement
