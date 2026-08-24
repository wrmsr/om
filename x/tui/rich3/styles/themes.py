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

from omcore import lang

from .styles import Style
from .styles import StyleType


with lang.auto_proxy_import(globals()):
    from .defaults import styles as style_defaults


##


class Theme:
    """
    A container for style information, used by :class:`~rich.console.Console`.

    Args:
        styles (dict[str, Style], optional): A mapping of style names on to styles. Defaults to None for a theme with no styles.
        inherit (bool, optional): Inherit default styles. Defaults to True.
    """

    styles: dict[str, Style]

    def __init__(
            self,
            styles: ta.Mapping[str, StyleType] | None = None,
            inherit: bool = True,
    ):
        self.styles = style_defaults.DEFAULT_STYLES.copy() if inherit else {}
        if styles is not None:
            self.styles.update({
                name: style if isinstance(style, Style) else Style.parse(style)
                for name, style in styles.items()
            })

    @property
    def config(self) -> str:
        """Get contents of a config file for this theme."""

        config = '[styles]\n' + '\n'.join(
            f'{name} = {style}'
            for name, style in sorted(self.styles.items())
        )
        return config

    @classmethod
    def from_file(
            cls,
            config_file: ta.IO[str],
            source: str | None = None,
            inherit: bool = True,
    ) -> Theme:
        """
        Load a theme from a text mode file.

        Args:
            config_file (IO[str]): An open conf file.
            source (str, optional): The filename of the open file. Defaults to None.
            inherit (bool, optional): Inherit default styles. Defaults to True.

        Returns:
            Theme: A New theme instance.
        """

        import configparser

        config = configparser.ConfigParser()
        config.read_file(config_file, source=source)
        styles = {name: Style.parse(value) for name, value in config.items('styles')}
        theme = Theme(styles, inherit=inherit)
        return theme

    @classmethod
    def read(
            cls,
            path: str,
            inherit: bool = True,
            encoding: str | None = None,
    ) -> Theme:
        """
        Read a theme from a path.

        Args:
            path (str): Path to a config file readable by Python configparser module.
            inherit (bool, optional): Inherit default styles. Defaults to True.
            encoding (str, optional): Encoding of the config file. Defaults to None.

        Returns:
            Theme: A new theme instance.
        """

        with open(path, encoding=encoding) as config_file:
            return cls.from_file(config_file, source=path, inherit=inherit)


class ThemeStackError(Exception):
    """Base exception for errors related to the theme stack."""


class ThemeStack:
    """
    A stack of themes.

    Args:
        theme (Theme): A theme instance
    """

    def __init__(self, theme: Theme) -> None:
        self._entries: list[dict[str, Style]] = [theme.styles]
        self.get = self._entries[-1].get

    def push_theme(self, theme: Theme, inherit: bool = True) -> None:
        """
        Push a theme on the top of the stack.

        Args:
            theme (Theme): A Theme instance.
            inherit (boolean, optional): Inherit styles from current top of stack.
        """

        styles: dict[str, Style]
        styles = (
            {**self._entries[-1], **theme.styles} if inherit else theme.styles.copy()
        )
        self._entries.append(styles)
        self.get = self._entries[-1].get

    def pop_theme(self) -> None:
        """Pop (and discard) the top-most theme."""

        if len(self._entries) == 1:
            raise ThemeStackError('Unable to pop base theme')
        self._entries.pop()
        self.get = self._entries[-1].get
