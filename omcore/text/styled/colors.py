"""Target-neutral color values."""
from ... import dataclasses as dc
from ... import lang


##


class Color(lang.Abstract):
    """A target-neutral color value."""


@dc.dataclass(frozen=True)
class RgbColor(Color, lang.Final):
    """An RGB color with eight-bit channels."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel in (self.r, self.g, self.b):
            if not isinstance(channel, int) or isinstance(channel, bool) or not 0 <= channel <= 255:
                raise ValueError(channel)

    @property
    def hex(self) -> str:
        return f'#{self.r:02x}{self.g:02x}{self.b:02x}'


def parse_rgb(s: str) -> RgbColor:
    """Parse a `#RRGGBB` or shorthand `#RGB` color."""

    if not isinstance(s, str) or not s.startswith('#'):
        raise ValueError(s)

    hx = s[1:]
    if len(hx) == 3:
        hx = ''.join(c * 2 for c in hx)
    if len(hx) != 6:
        raise ValueError(s)

    try:
        return RgbColor(
            int(hx[0:2], 16),
            int(hx[2:4], 16),
            int(hx[4:6], 16),
        )
    except ValueError:
        raise ValueError(s) from None
