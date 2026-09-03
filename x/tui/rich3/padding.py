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
from .segment import Segment
from .styles.styles import Style


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import RenderableType
    from .console import RenderResult


##


PaddingDimensions: ta.TypeAlias = ta.Union[  # noqa
    int,
    tuple[int],
    tuple[int, int],
    tuple[int, int, int, int],
]


class Padding:
    """
    Draw space around content.

    Example:
        >>> print(Padding("Hello", (2, 4), style="on blue"))

    Args:
        renderable (RenderableType): String or other renderable.
        pad (Union[int, tuple[int]]): Padding for top, right, bottom, and left borders. May be specified with 1, 2, or 4
            integers (CSS style).
        style (Union[str, Style], optional): Style for padding characters. Defaults to "none".
        expand (bool, optional): Expand padding to fit available width. Defaults to True.
    """

    def __init__(
        self,
        renderable: RenderableType,
        pad: PaddingDimensions = (0, 0, 0, 0),
        *,
        style: str | Style = 'none',
        expand: bool = True,
    ) -> None:
        super().__init__()

        self.renderable = renderable
        self.top, self.right, self.bottom, self.left = self.unpack(pad)
        self.style = style
        self.expand = expand

    @classmethod
    def indent(cls, renderable: RenderableType, level: int) -> Padding:
        """
        Make padding instance to render an indent.

        Args:
            renderable (RenderableType): String or other renderable.
            level (int): Number of characters to indent.

        Returns:
            Padding: A Padding instance.
        """

        return Padding(renderable, pad=(0, 0, 0, level), expand=False)

    @staticmethod
    def unpack(pad: PaddingDimensions) -> tuple[int, int, int, int]:
        """Unpack padding specified in CSS style."""

        if isinstance(pad, int):
            return (pad, pad, pad, pad)
        if len(pad) == 1:
            _pad = pad[0]
            return (_pad, _pad, _pad, _pad)
        if len(pad) == 2:
            pad_top, pad_right = pad
            return (pad_top, pad_right, pad_top, pad_right)
        if len(pad) == 4:
            top, right, bottom, left = pad
            return (top, right, bottom, left)
        raise ValueError(f'1, 2 or 4 integers required for padding; {len(pad)} given')

    def __repr__(self) -> str:
        return f'Padding({self.renderable!r}, ({self.top},{self.right},{self.bottom},{self.left}))'

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        style = console.get_style(self.style)
        if self.expand:
            width = options.max_width
        else:
            width = min(
                Measurement.get(console, options, self.renderable).maximum +
                self.left +
                self.right,
                options.max_width,
            )

        render_options = options.update_width(width - self.left - self.right)
        if render_options.height is not None:
            render_options = render_options.update_height(height=render_options.height - self.top - self.bottom)

        lines = console.render_lines(
            self.renderable,
            render_options,
            style=style,
            pad=True,
        )

        _Segment = Segment

        left = _Segment(' ' * self.left, style) if self.left else None

        right = (
            [_Segment(f'{" " * self.right}', style), _Segment.line()]
            if self.right
            else [_Segment.line()]
        )

        blank_line: list[Segment] | None = None
        if self.top:
            blank_line = [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.top

        if left:
            for line in lines:
                yield left
                yield from line
                yield from right

        else:
            for line in lines:
                yield from line
                yield from right

        if self.bottom:
            blank_line = blank_line or [_Segment(f'{" " * width}\n', style)]
            yield from blank_line * self.bottom

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        max_width = options.max_width
        extra_width = self.left + self.right
        if max_width - extra_width < 1:
            return Measurement(max_width, max_width)
        measure_min, measure_max = Measurement.get(console, options, self.renderable)
        measurement = Measurement(measure_min + extra_width, measure_max + extra_width)
        measurement = measurement.with_maximum(max_width)
        return measurement
