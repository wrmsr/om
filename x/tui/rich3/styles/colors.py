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
import colorsys
import enum
import functools
import re
import typing as ta

from omcore import check
from omcore import lang


with lang.auto_proxy_import(globals()):
    from .defaults import palettes as palette_defaults
    from .defaults import terminal as terminal_defaults


if ta.TYPE_CHECKING:  # pragma: no cover
    from ..text import Text
    from .terminal import TerminalTheme


##


class ColorTriplet(ta.NamedTuple):
    """The red, green, and blue components of a color."""

    # Red component in 0 to 255 range.
    red: int

    # Green component in 0 to 255 range.
    green: int

    # Blue component in 0 to 255 range.
    blue: int

    @property
    def hex(self) -> str:
        """get the color triplet in CSS style."""

        red, green, blue = self
        return f'#{red:02x}{green:02x}{blue:02x}'

    @property
    def rgb(self) -> str:
        """
        The color in RGB format.

        Returns:
            str: An rgb color, e.g. ``"rgb(100,23,255)"``.
        """

        red, green, blue = self
        return f'rgb({red},{green},{blue})'

    @property
    def normalized(self) -> tuple[float, float, float]:
        """
        Convert components into floats between 0 and 1.

        Returns:
            tuple[float, float, float]: A tuple of three normalized colour components.
        """

        red, green, blue = self
        return red / 255.0, green / 255.0, blue / 255.0


def parse_rgb_hex(hex_color: str) -> ColorTriplet:
    """Parse six hex characters in to RGB triplet."""

    check.equal(len(hex_color), 6, 'must be 6 characters')
    color = ColorTriplet(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
    return color


def blend_rgb(
        color1: ColorTriplet,
        color2: ColorTriplet,
        cross_fade: float = 0.5,
) -> ColorTriplet:
    """Blend one RGB color in to another."""

    r1, g1, b1 = color1
    r2, g2, b2 = color2
    new_color = ColorTriplet(
        int(r1 + (r2 - r1) * cross_fade),
        int(g1 + (g2 - g1) * cross_fade),
        int(b1 + (b2 - b1) * cross_fade),
    )
    return new_color


##


class ColorSystem(enum.IntEnum):
    """One of the 3 color system supported by terminals."""

    STANDARD = 1
    EIGHT_BIT = 2
    TRUECOLOR = 3
    WINDOWS = 4

    def __repr__(self) -> str:
        return f'ColorSystem.{self.name}'

    def __str__(self) -> str:
        return repr(self)


class ColorType(enum.IntEnum):
    """Type of color stored in Color class."""

    DEFAULT = 0
    STANDARD = 1
    EIGHT_BIT = 2
    TRUECOLOR = 3
    WINDOWS = 4

    def __repr__(self) -> str:
        return f'ColorType.{self.name}'


ANSI_COLOR_NAMES = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'white': 7,
    'bright_black': 8,
    'bright_red': 9,
    'bright_green': 10,
    'bright_yellow': 11,
    'bright_blue': 12,
    'bright_magenta': 13,
    'bright_cyan': 14,
    'bright_white': 15,
    'grey0': 16,
    'gray0': 16,
    'navy_blue': 17,
    'dark_blue': 18,
    'blue3': 20,
    'blue1': 21,
    'dark_green': 22,
    'deep_sky_blue4': 25,
    'dodger_blue3': 26,
    'dodger_blue2': 27,
    'green4': 28,
    'spring_green4': 29,
    'turquoise4': 30,
    'deep_sky_blue3': 32,
    'dodger_blue1': 33,
    'green3': 40,
    'spring_green3': 41,
    'dark_cyan': 36,
    'light_sea_green': 37,
    'deep_sky_blue2': 38,
    'deep_sky_blue1': 39,
    'spring_green2': 47,
    'cyan3': 43,
    'dark_turquoise': 44,
    'turquoise2': 45,
    'green1': 46,
    'spring_green1': 48,
    'medium_spring_green': 49,
    'cyan2': 50,
    'cyan1': 51,
    'dark_red': 88,
    'deep_pink4': 125,
    'purple4': 55,
    'purple3': 56,
    'blue_violet': 57,
    'orange4': 94,
    'grey37': 59,
    'gray37': 59,
    'medium_purple4': 60,
    'slate_blue3': 62,
    'royal_blue1': 63,
    'chartreuse4': 64,
    'dark_sea_green4': 71,
    'pale_turquoise4': 66,
    'steel_blue': 67,
    'steel_blue3': 68,
    'cornflower_blue': 69,
    'chartreuse3': 76,
    'cadet_blue': 73,
    'sky_blue3': 74,
    'steel_blue1': 81,
    'pale_green3': 114,
    'sea_green3': 78,
    'aquamarine3': 79,
    'medium_turquoise': 80,
    'chartreuse2': 112,
    'sea_green2': 83,
    'sea_green1': 85,
    'aquamarine1': 122,
    'dark_slate_gray2': 87,
    'dark_magenta': 91,
    'dark_violet': 128,
    'purple': 129,
    'light_pink4': 95,
    'plum4': 96,
    'medium_purple3': 98,
    'slate_blue1': 99,
    'yellow4': 106,
    'wheat4': 101,
    'grey53': 102,
    'gray53': 102,
    'light_slate_grey': 103,
    'light_slate_gray': 103,
    'medium_purple': 104,
    'light_slate_blue': 105,
    'dark_olive_green3': 149,
    'dark_sea_green': 108,
    'light_sky_blue3': 110,
    'sky_blue2': 111,
    'dark_sea_green3': 150,
    'dark_slate_gray3': 116,
    'sky_blue1': 117,
    'chartreuse1': 118,
    'light_green': 120,
    'pale_green1': 156,
    'dark_slate_gray1': 123,
    'red3': 160,
    'medium_violet_red': 126,
    'magenta3': 164,
    'dark_orange3': 166,
    'indian_red': 167,
    'hot_pink3': 168,
    'medium_orchid3': 133,
    'medium_orchid': 134,
    'medium_purple2': 140,
    'dark_goldenrod': 136,
    'light_salmon3': 173,
    'rosy_brown': 138,
    'grey63': 139,
    'gray63': 139,
    'medium_purple1': 141,
    'gold3': 178,
    'dark_khaki': 143,
    'navajo_white3': 144,
    'grey69': 145,
    'gray69': 145,
    'light_steel_blue3': 146,
    'light_steel_blue': 147,
    'yellow3': 184,
    'dark_sea_green2': 157,
    'light_cyan3': 152,
    'light_sky_blue1': 153,
    'green_yellow': 154,
    'dark_olive_green2': 155,
    'dark_sea_green1': 193,
    'pale_turquoise1': 159,
    'deep_pink3': 162,
    'magenta2': 200,
    'hot_pink2': 169,
    'orchid': 170,
    'medium_orchid1': 207,
    'orange3': 172,
    'light_pink3': 174,
    'pink3': 175,
    'plum3': 176,
    'violet': 177,
    'light_goldenrod3': 179,
    'tan': 180,
    'misty_rose3': 181,
    'thistle3': 182,
    'plum2': 183,
    'khaki3': 185,
    'light_goldenrod2': 222,
    'light_yellow3': 187,
    'grey84': 188,
    'gray84': 188,
    'light_steel_blue1': 189,
    'yellow2': 190,
    'dark_olive_green1': 192,
    'honeydew2': 194,
    'light_cyan1': 195,
    'red1': 196,
    'deep_pink2': 197,
    'deep_pink1': 199,
    'magenta1': 201,
    'orange_red1': 202,
    'indian_red1': 204,
    'hot_pink': 206,
    'dark_orange': 208,
    'salmon1': 209,
    'light_coral': 210,
    'pale_violet_red1': 211,
    'orchid2': 212,
    'orchid1': 213,
    'orange1': 214,
    'sandy_brown': 215,
    'light_salmon1': 216,
    'light_pink1': 217,
    'pink1': 218,
    'plum1': 219,
    'gold1': 220,
    'navajo_white1': 223,
    'misty_rose1': 224,
    'thistle1': 225,
    'yellow1': 226,
    'light_goldenrod1': 227,
    'khaki1': 228,
    'wheat1': 229,
    'cornsilk1': 230,
    'grey100': 231,
    'gray100': 231,
    'grey3': 232,
    'gray3': 232,
    'grey7': 233,
    'gray7': 233,
    'grey11': 234,
    'gray11': 234,
    'grey15': 235,
    'gray15': 235,
    'grey19': 236,
    'gray19': 236,
    'grey23': 237,
    'gray23': 237,
    'grey27': 238,
    'gray27': 238,
    'grey30': 239,
    'gray30': 239,
    'grey35': 240,
    'gray35': 240,
    'grey39': 241,
    'gray39': 241,
    'grey42': 242,
    'gray42': 242,
    'grey46': 243,
    'gray46': 243,
    'grey50': 244,
    'gray50': 244,
    'grey54': 245,
    'gray54': 245,
    'grey58': 246,
    'gray58': 246,
    'grey62': 247,
    'gray62': 247,
    'grey66': 248,
    'gray66': 248,
    'grey70': 249,
    'gray70': 249,
    'grey74': 250,
    'gray74': 250,
    'grey78': 251,
    'gray78': 251,
    'grey82': 252,
    'gray82': 252,
    'grey85': 253,
    'gray85': 253,
    'grey89': 254,
    'gray89': 254,
    'grey93': 255,
    'gray93': 255,
}


class ColorParseError(Exception):
    """The color could not be parsed."""


COLOR_PAT = re.compile(
    r"""^
\#([0-9a-f]{6})$|
color\(([0-9]{1,3})\)$|
rgb\(([\d\s,]+)\)$
""",
    re.VERBOSE,
)


class Color(ta.NamedTuple):
    """Terminal color definition."""

    # The name of the color (typically the input to Color.parse)."""
    name: str

    # The type of the color.
    type: ColorType

    # The color number, if a standard color, or None.
    number: int | None = None

    # A triplet of color components, if an RGB color.
    triplet: ColorTriplet | None = None

    def __rich__(self) -> Text:
        """Displays the actual color if Rich printed."""

        from ..text import Text
        from .styles import Style

        return Text.assemble(
            f'<color {self.name!r} ({self.type.name.lower()})',
            ('⬤', Style(color=self)),
            ' >',
        )

    @property
    def system(self) -> ColorSystem:
        """Get the native color system for this color."""

        if self.type == ColorType.DEFAULT:
            return ColorSystem.STANDARD
        return ColorSystem(int(self.type))

    @property
    def is_system_defined(self) -> bool:
        """Check if the color is ultimately defined by the system."""

        return self.system not in (ColorSystem.EIGHT_BIT, ColorSystem.TRUECOLOR)

    @property
    def is_default(self) -> bool:
        """Check if the color is a default color."""

        return self.type == ColorType.DEFAULT

    def get_truecolor(
            self,
            theme: TerminalTheme | None = None,
            foreground: bool = True,
    ) -> ColorTriplet:
        """
        Get an equivalent color triplet for this color.

        Args:
            theme (TerminalTheme, optional): Optional terminal theme, or None to use default. Defaults to None.
            foreground (bool, optional): True for a foreground color, or False for background. Defaults to True.

        Returns:
            ColorTriplet: A color triplet containing RGB components.
        """

        if theme is None:
            theme = terminal_defaults.DEFAULT_TERMINAL_THEME
        if self.type == ColorType.TRUECOLOR:
            return check.not_none(self.triplet)
        elif self.type == ColorType.EIGHT_BIT:
            return palette_defaults.EIGHT_BIT_PALETTE[check.not_none(self.number)]
        elif self.type == ColorType.STANDARD:
            return theme.ansi_colors[check.not_none(self.number)]
        elif self.type == ColorType.WINDOWS:
            return palette_defaults.WINDOWS_PALETTE[check.not_none(self.number)]
        else:  # self.type == ColorType.DEFAULT:
            check.none(self.number)
            return theme.foreground_color if foreground else theme.background_color

    @classmethod
    def from_ansi(cls, number: int) -> Color:
        """
        Create a Color number from it's 8-bit ansi number.

        Args:
            number (int): A number between 0-255 inclusive.

        Returns:
            Color: A new Color instance.
        """

        return cls(
            name=f'color({number})',
            type=(ColorType.STANDARD if number < 16 else ColorType.EIGHT_BIT),
            number=number,
        )

    @classmethod
    def from_triplet(cls, triplet: ColorTriplet) -> Color:
        """
        Create a truecolor RGB color from a triplet of values.

        Args:
            triplet (ColorTriplet): A color triplet containing red, green and blue components.

        Returns:
            Color: A new color object.
        """

        return cls(name=triplet.hex, type=ColorType.TRUECOLOR, triplet=triplet)

    @classmethod
    def from_rgb(cls, red: float, green: float, blue: float) -> Color:
        """
        Create a truecolor from three color components in the range(0->255).

        Args:
            red (float): Red component in range 0-255.
            green (float): Green component in range 0-255.
            blue (float): Blue component in range 0-255.

        Returns:
            Color: A new color object.
        """

        return cls.from_triplet(ColorTriplet(int(red), int(green), int(blue)))

    @classmethod
    def default(cls) -> Color:
        """
        Get a Color instance representing the default color.

        Returns:
            Color: Default color.
        """

        return cls(name='default', type=ColorType.DEFAULT)

    @classmethod
    @functools.lru_cache(maxsize=1024)
    def parse(cls, color: str) -> Color:
        """Parse a color definition."""

        original_color = color
        color = color.lower().strip()

        if color == 'default':
            return cls(color, type=ColorType.DEFAULT)

        color_number = ANSI_COLOR_NAMES.get(color)
        if color_number is not None:
            return cls(
                color,
                type=(ColorType.STANDARD if color_number < 16 else ColorType.EIGHT_BIT),
                number=color_number,
            )

        color_match = COLOR_PAT.match(color)
        if color_match is None:
            raise ColorParseError(f'{original_color!r} is not a valid color')

        color_24, color_8, color_rgb = color_match.groups()
        if color_24:
            triplet = ColorTriplet(
                int(color_24[0:2], 16),
                int(color_24[2:4], 16),
                int(color_24[4:6], 16),
            )
            return cls(color, ColorType.TRUECOLOR, triplet=triplet)

        elif color_8:
            number = int(color_8)
            if number > 255:
                raise ColorParseError(f'color number must be <= 255 in {color!r}')
            return cls(
                color,
                type=(ColorType.STANDARD if number < 16 else ColorType.EIGHT_BIT),
                number=number,
            )

        else:  #  color_rgb:
            components = color_rgb.split(',')
            if len(components) != 3:
                raise ColorParseError(
                    f'expected three components in {original_color!r}',
                )
            red, green, blue = components
            triplet = ColorTriplet(int(red), int(green), int(blue))
            if not all(component <= 255 for component in triplet):
                raise ColorParseError(f'color components must be <= 255 in {original_color!r}')
            return cls(color, ColorType.TRUECOLOR, triplet=triplet)

    @functools.lru_cache(maxsize=1024)
    def get_ansi_codes(self, foreground: bool = True) -> tuple[str, ...]:
        """Get the ANSI escape codes for this color."""

        _type = self.type
        if _type == ColorType.DEFAULT:
            return ('39' if foreground else '49',)

        elif _type == ColorType.WINDOWS:
            number = check.not_none(self.number)
            fore, back = (30, 40) if number < 8 else (82, 92)
            return (str(fore + number if foreground else back + number),)

        elif _type == ColorType.STANDARD:
            number = check.not_none(self.number)
            fore, back = (30, 40) if number < 8 else (82, 92)
            return (str(fore + number if foreground else back + number),)

        elif _type == ColorType.EIGHT_BIT:
            number = check.not_none(self.number)
            return ('38' if foreground else '48', '5', str(number))

        else:  # self.standard == ColorStandard.TRUECOLOR:
            red, green, blue = check.not_none(self.triplet)
            return ('38' if foreground else '48', '2', str(red), str(green), str(blue))

    @functools.lru_cache(maxsize=1024)
    def downgrade(self, system: ColorSystem) -> Color:
        """Downgrade a color system to a system with fewer colors."""

        if self.type in (ColorType.DEFAULT, system):
            return self
        # Convert to 8-bit color from truecolor color
        if system == ColorSystem.EIGHT_BIT and self.system == ColorSystem.TRUECOLOR:
            triplet = check.not_none(self.triplet)
            _h, l, s = colorsys.rgb_to_hls(*triplet.normalized)
            # If saturation is under 15% assume it is grayscale
            if s < 0.15:
                gray = round(l * 25.0)
                if gray == 0:
                    color_number = 16
                elif gray == 25:
                    color_number = 231
                else:
                    color_number = 231 + gray
                return Color(self.name, ColorType.EIGHT_BIT, number=color_number)

            red, green, blue = triplet
            six_red = red / 95 if red < 95 else 1 + (red - 95) / 40
            six_green = green / 95 if green < 95 else 1 + (green - 95) / 40
            six_blue = blue / 95 if blue < 95 else 1 + (blue - 95) / 40

            color_number = (
                16 +
                36 * round(six_red) +
                6 * round(six_green) +
                round(six_blue)
            )
            return Color(self.name, ColorType.EIGHT_BIT, number=color_number)

        # Convert to standard from truecolor or 8-bit
        elif system == ColorSystem.STANDARD:
            if self.system == ColorSystem.TRUECOLOR:
                triplet = check.not_none(self.triplet)
            else:  # self.system == ColorSystem.EIGHT_BIT
                number = check.not_none(self.number)
                triplet = ColorTriplet(*palette_defaults.EIGHT_BIT_PALETTE[number])

            color_number = palette_defaults.STANDARD_PALETTE.match(triplet)
            return Color(self.name, ColorType.STANDARD, number=color_number)

        elif system == ColorSystem.WINDOWS:
            if self.system == ColorSystem.TRUECOLOR:
                triplet = check.not_none(self.triplet)
            else:  # self.system == ColorSystem.EIGHT_BIT
                number = check.not_none(self.number)
                if number < 16:
                    return Color(self.name, ColorType.WINDOWS, number=number)
                triplet = ColorTriplet(*palette_defaults.EIGHT_BIT_PALETTE[number])

            color_number = palette_defaults.WINDOWS_PALETTE.match(triplet)
            return Color(self.name, ColorType.WINDOWS, number=color_number)

        return self


