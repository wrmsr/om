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
import functools
import math
import typing as ta

from .colors import ColorTriplet


##


class Palette:
    """A palette of available colors."""

    def __init__(self, colors: ta.Sequence[tuple[int, int, int]]):
        self._colors = colors

    def __getitem__(self, number: int) -> ColorTriplet:
        return ColorTriplet(*self._colors[number])

    # This is somewhat inefficient and needs caching
    @functools.lru_cache(maxsize=1024)
    def match(self, color: tuple[int, int, int]) -> int:
        """
        Find a color from a palette that most closely matches a given color.

        Args:
            color (tuple[int, int, int]): RGB components in range 0 > 255.

        Returns:
            int: Index of closes matching color.
        """

        red1, green1, blue1 = color
        _sqrt = math.sqrt
        get_color = self._colors.__getitem__

        def get_color_distance(index: int) -> float:
            """Get the distance to a color."""

            red2, green2, blue2 = get_color(index)
            red_mean = (red1 + red2) // 2
            red = red1 - red2
            green = green1 - green2
            blue = blue1 - blue2
            return _sqrt(
                (((512 + red_mean) * red * red) >> 8) +
                4 * green * green +
                (((767 - red_mean) * blue * blue) >> 8),
            )

        min_index = min(range(len(self._colors)), key=get_color_distance)
        return min_index
