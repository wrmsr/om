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
import itertools
import typing as ta

from .cells import cell_len
from .measure import Measurement


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import JustifyMethod
    from .console import OverflowMethod
    from .console import RenderableType
    from .console import RenderResult
    from .text import Text


T = ta.TypeVar('T')


##


class Renderables:
    """A list subclass which renders its contents to the console."""

    def __init__(
            self,
            renderables: ta.Iterable[RenderableType] | None = None,
    ) -> None:
        self._renderables: list[RenderableType] = (
            list(renderables) if renderables is not None else []
        )

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Console render method to insert line-breaks."""

        yield from self._renderables

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        dimensions = [
            Measurement.get(console, options, renderable)
            for renderable in self._renderables
        ]
        if not dimensions:
            return Measurement(1, 1)
        _min = max(dimension.minimum for dimension in dimensions)
        _max = max(dimension.maximum for dimension in dimensions)
        return Measurement(_min, _max)

    def append(self, renderable: RenderableType) -> None:
        self._renderables.append(renderable)

    def __iter__(self) -> ta.Iterable[RenderableType]:
        return iter(self._renderables)


class Lines:
    """A list subclass which can render to the console."""

    def __init__(self, lines: ta.Iterable[Text] = ()) -> None:
        self._lines: list[Text] = list(lines)

    def __repr__(self) -> str:
        return f'Lines({self._lines!r})'

    def __iter__(self) -> ta.Iterator[Text]:
        return iter(self._lines)

    @ta.overload
    def __getitem__(self, index: int) -> Text:
        ...

    @ta.overload
    def __getitem__(self, index: slice) -> list[Text]:
        ...

    def __getitem__(self, index: slice | int) -> Text | list[Text]:
        return self._lines[index]

    def __setitem__(self, index: int, value: Text) -> Lines:
        self._lines[index] = value
        return self

    def __len__(self) -> int:
        return self._lines.__len__()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Console render method to insert line-breaks."""

        yield from self._lines

    def append(self, line: Text) -> None:
        self._lines.append(line)

    def extend(self, lines: ta.Iterable[Text]) -> None:
        self._lines.extend(lines)

    def pop(self, index: int = -1) -> Text:
        return self._lines.pop(index)

    def justify(
            self,
            console: Console,
            width: int,
            justify: JustifyMethod = 'left',
            overflow: OverflowMethod = 'fold',
    ) -> None:
        """
        Justify and overflow text to a given width.

        Args:
            console (Console): Console instance.
            width (int): Number of cells available per line.
            justify (str, optional): Default justify method for text: "left", "center", "full" or "right". Defaults to "left".
            overflow (str, optional): Default overflow for text: "crop", "fold", or "ellipsis". Defaults to "fold".
        """

        from .text import Text

        if justify == 'left':
            for line in self._lines:
                line.truncate(width, overflow=overflow, pad=True)

        elif justify == 'center':
            for line in self._lines:
                line.rstrip()
                line.truncate(width, overflow=overflow)
                line.pad_left((width - cell_len(line.plain)) // 2)
                line.pad_right(width - cell_len(line.plain))

        elif justify == 'right':
            for line in self._lines:
                line.rstrip()
                line.truncate(width, overflow=overflow)
                line.pad_left(width - cell_len(line.plain))

        elif justify == 'full':
            for line_index, line in enumerate(self._lines):
                if line_index == len(self._lines) - 1:
                    break

                words = line.split(' ')
                words_size = sum(cell_len(word.plain) for word in words)
                num_spaces = len(words) - 1
                spaces = [1 for _ in range(num_spaces)]
                index = 0
                if spaces:
                    while words_size + num_spaces < width:
                        spaces[len(spaces) - index - 1] += 1
                        num_spaces += 1
                        index = (index + 1) % len(spaces)

                tokens: list[Text] = []
                for index, (word, next_word) in enumerate(
                    itertools.zip_longest(words, words[1:]),
                ):
                    tokens.append(word)
                    if index < len(spaces):
                        style = word.get_style_at_offset(console, -1)
                        next_style = next_word.get_style_at_offset(console, 0)
                        space_style = style if style == next_style else line.style
                        tokens.append(Text(' ' * spaces[index], style=space_style))

                self[line_index] = Text('').join(tokens)
