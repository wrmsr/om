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
import operator
import typing as ta

from .errors import NotRenderableError
from .protocol import is_renderable
from .protocol import rich_cast


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import RenderableType


##


class Measurement(ta.NamedTuple):
    """Stores the minimum and maximum widths (in characters) required to render an object."""

    # Minimum number of cells required to render.
    minimum: int

    # Maximum number of cells required to render.
    maximum: int

    @property
    def span(self) -> int:
        """Get difference between maximum and minimum."""

        return self.maximum - self.minimum

    def normalize(self) -> Measurement:
        """
        Get measurement that ensures that minimum <= maximum and minimum >= 0

        Returns:
            Measurement: A normalized measurement.
        """

        minimum, maximum = self
        minimum = min(max(0, minimum), maximum)
        return Measurement(max(0, minimum), max(0, max(minimum, maximum)))

    def with_maximum(self, width: int) -> Measurement:
        """
        Get a RenderableWith where the widths are <= width.

        Args:
            width (int): Maximum desired width.

        Returns:
            Measurement: New Measurement object.
        """

        minimum, maximum = self
        return Measurement(min(minimum, width), min(maximum, width))

    def with_minimum(self, width: int) -> Measurement:
        """
        Get a RenderableWith where the widths are >= width.

        Args:
            width (int): Minimum desired width.

        Returns:
            Measurement: New Measurement object.
        """

        minimum, maximum = self
        width = max(0, width)
        return Measurement(max(minimum, width), max(maximum, width))

    def clamp(
            self,
            min_width: int | None = None,
            max_width: int | None = None,
    ) -> Measurement:
        """
        Clamp a measurement within the specified range.

        Args:
            min_width (int): Minimum desired width, or ``None`` for no minimum. Defaults to None.
            max_width (int): Maximum desired width, or ``None`` for no maximum. Defaults to None.

        Returns:
            Measurement: New Measurement object.
        """

        measurement = self
        if min_width is not None:
            measurement = measurement.with_minimum(min_width)
        if max_width is not None:
            measurement = measurement.with_maximum(max_width)
        return measurement

    @classmethod
    def get(
            cls,
            console: Console,
            options: ConsoleOptions,
            renderable: RenderableType,
    ) -> Measurement:
        """
        Get a measurement for a renderable.

        Args:
            console (~rich.console.Console): Console instance.
            options (~rich.console.ConsoleOptions): Console options.
            renderable (RenderableType): An object that may be rendered with Rich.

        Raises:
            NotRenderableError: If the object is not renderable.

        Returns:
            Measurement: Measurement object containing range of character widths required to render the object.
        """

        _max_width = options.max_width
        if _max_width < 1:
            return Measurement(0, 0)
        if isinstance(renderable, str):
            renderable = console.render_str(
                renderable, markup=options.markup, highlight=False,
            )
        renderable = rich_cast(renderable)
        if is_renderable(renderable):
            get_console_width: ta.Callable[[Console, ConsoleOptions], Measurement] | None
            get_console_width = getattr(renderable, '__rich_measure__', None)
            if get_console_width is not None:
                render_width = (
                    get_console_width(console, options)
                    .normalize()
                    .with_maximum(_max_width)
                )
                if render_width.maximum < 1:
                    return Measurement(0, 0)

                return render_width.normalize()

            else:
                return Measurement(0, _max_width)

        else:
            raise NotRenderableError(
                f'Unable to get render width for {renderable!r}; '
                'a str, Segment, or object with __rich_console__ method is required',
            )


def measure_renderables(
        console: Console,
        options: ConsoleOptions,
        renderables: ta.Sequence[RenderableType],
) -> Measurement:
    """
    Get a measurement that would fit a number of renderables.

    Args:
        console (~rich.console.Console): Console instance.
        options (~rich.console.ConsoleOptions): Console options.
        renderables (Iterable[RenderableType]): One or more renderable objects.

    Returns:
        Measurement: Measurement object containing range of character widths required to
            contain all given renderables.
    """

    if not renderables:
        return Measurement(0, 0)
    get_measurement = Measurement.get
    measurements = [
        get_measurement(console, options, renderable) for renderable in renderables
    ]
    measured_width = Measurement(
        max(measurements, key=operator.itemgetter(0)).minimum,
        max(measurements, key=operator.itemgetter(1)).maximum,
    )
    return measured_width
