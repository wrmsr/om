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


if ta.TYPE_CHECKING:
    from .console import RenderableType


##


_GIBBERISH = """aihwerij235234ljsdnp34ksodfipwoe234234jlskjdf"""


def is_renderable(check_object: ta.Any) -> bool:
    """Check if an object may be rendered by Rich."""

    return (
        isinstance(check_object, str) or
        hasattr(check_object, '__rich__') or
        hasattr(check_object, '__rich_console__')
    )


def rich_cast(renderable: object) -> RenderableType:
    """
    Cast an object to a renderable by calling __rich__ if present.

    Args:
        renderable (object): A potentially renderable object

    Returns:
        object: The result of recursively calling __rich__.
    """

    from .console import RenderableType

    rich_visited_set: set[type] = set()  # Prevent potential infinite loop
    while hasattr(renderable, '__rich__') and not isinstance(renderable, type):
        # Detect object which claim to have all the attributes
        if hasattr(renderable, _GIBBERISH):
            return repr(renderable)
        cast_method = getattr(renderable, '__rich__')
        renderable = cast_method()
        renderable_type = type(renderable)
        if renderable_type in rich_visited_set:
            break
        rich_visited_set.add(renderable_type)

    return ta.cast(RenderableType, renderable)
