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

from .colors import ColorTriplet
from .palettes import Palette


_ColorTuple: ta.TypeAlias = tuple[int, int, int]


##


class TerminalTheme:
    """
    A color theme used when exporting console content.

    Args:
        background (tuple[int, int, int]): The background color.
        foreground (tuple[int, int, int]): The foreground (text) color.
        normal (list[tuple[int, int, int]]): A list of 8 normal intensity colors.
        bright (list[tuple[int, int, int]], optional): A list of 8 bright colors, or None to repeat normal intensity.
            Defaults to None.
    """

    def __init__(
            self,
            background: _ColorTuple,
            foreground: _ColorTuple,
            normal: list[_ColorTuple],
            bright: list[_ColorTuple] | None = None,
    ) -> None:
        self.background_color = ColorTriplet(*background)
        self.foreground_color = ColorTriplet(*foreground)
        self.ansi_colors = Palette(normal + (bright or normal))


