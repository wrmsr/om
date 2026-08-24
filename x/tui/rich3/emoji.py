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

from ._data.emoji import EMOJI
from ._utils.emoji import emoji_replace
from .segment import Segment
from .styles.styles import Style


if ta.TYPE_CHECKING:
    from .console import Console
    from .console import ConsoleOptions
    from .console import RenderResult


EmojiVariant: ta.TypeAlias = ta.Literal['emoji', 'text']


##


class NoEmoji(Exception):
    """No emoji by that name."""


class Emoji:
    __slots__ = (
        'name',
        'style',
        '_char',
        'variant',
    )

    VARIANTS = {
        'text': '\ufe0e',
        'emoji': '\ufe0f',
    }

    def __init__(
            self,
            name: str,
            style: str | Style = 'none',
            variant: EmojiVariant | None = None,
    ) -> None:
        """
        A single emoji character.

        Args:
            name (str): Name of emoji.
            style (Union[str, Style], optional): Optional style. Defaults to None.

        Raises:
            NoEmoji: If the emoji doesn't exist.
        """

        self.name = name
        self.style = style
        self.variant = variant
        try:
            self._char = EMOJI[name]
        except KeyError:
            raise NoEmoji(f'No emoji called {name!r}')
        if variant is not None:
            self._char += self.VARIANTS.get(variant, '')

    @classmethod
    def replace(cls, text: str) -> str:
        """
        Replace emoji markup with corresponding unicode characters.

        Args:
            text (str): A string with emojis codes, e.g. "Hello :smiley:!"

        Returns:
            str: A string with emoji codes replaces with actual emoji.
        """

        return emoji_replace(text)

    def __repr__(self) -> str:
        return f'<emoji {self.name!r}>'

    def __str__(self) -> str:
        return self._char

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(self._char, console.get_style(self.style))
