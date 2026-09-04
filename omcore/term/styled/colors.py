"""
Terminal color model and depth downgrading.

Colors are structured values, never raw SGR strings. The named-16 and indexed-256 palettes are terminal concepts and
so live here rather than in the target-neutral core, as `Color` subclasses. Downgrade paths (rgb -> 256 -> 16) follow
the well-known analytic approaches: the 6x6x6 cube's non-linear ramp with a greyscale branch for low-saturation colors,
and nearest-match over a concrete palette table for 16-color terminals (excluding greys for saturated colors so they
don't wash out).
"""
import colorsys
import enum
import functools
import os
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...text import styled as st


##


class ColorDepth(enum.Enum):
    MONO = enum.auto()
    ANSI_16 = enum.auto()
    ANSI_256 = enum.auto()
    TRUE = enum.auto()


@ta.final
@dc.dataclass(frozen=True)
class NamedColor(st.Color, lang.Final):
    """One of the 16 classic ansi colors, by index (0-7 normal, 8-15 bright)."""

    index: int

    def __post_init__(self) -> None:
        check.arg(0 <= self.index <= 15)


@ta.final
@dc.dataclass(frozen=True)
class IndexedColor(st.Color, lang.Final):
    """An xterm 256-palette color, by index."""

    index: int

    def __post_init__(self) -> None:
        check.arg(0 <= self.index <= 255)


##


def detect_color_depth(environ: ta.Mapping[str, str] | None = None) -> ColorDepth:
    """
    Sniff the terminal's color depth from the environment - the modern consensus heuristics: COLORTERM for truecolor, a
    `256color` TERM for the indexed palette, `dumb` for none, 16 colors otherwise.
    """

    env = environ if environ is not None else os.environ

    if env.get('COLORTERM', '').lower() in ('truecolor', '24bit'):
        return ColorDepth.TRUE

    term = env.get('TERM', '').lower()
    if term == 'dumb':
        return ColorDepth.MONO
    if '256color' in term:
        return ColorDepth.ANSI_256
    if 'truecolor' in term or 'direct' in term:
        return ColorDepth.TRUE

    return ColorDepth.ANSI_16


##


BLACK = NamedColor(0)
RED = NamedColor(1)
GREEN = NamedColor(2)
YELLOW = NamedColor(3)
BLUE = NamedColor(4)
MAGENTA = NamedColor(5)
CYAN = NamedColor(6)
WHITE = NamedColor(7)

BRIGHT_BLACK = NamedColor(8)
BRIGHT_RED = NamedColor(9)
BRIGHT_GREEN = NamedColor(10)
BRIGHT_YELLOW = NamedColor(11)
BRIGHT_BLUE = NamedColor(12)
BRIGHT_MAGENTA = NamedColor(13)
BRIGHT_CYAN = NamedColor(14)
BRIGHT_WHITE = NamedColor(15)


##


# Standard xterm rgb values for the 16 named colors, used for nearest-match downgrading.
NAMED_COLOR_RGBS: ta.Sequence[tuple[int, int, int]] = (
    (0, 0, 0),
    (205, 0, 0),
    (0, 205, 0),
    (205, 205, 0),
    (0, 0, 238),
    (205, 0, 205),
    (0, 205, 205),
    (229, 229, 229),
    (127, 127, 127),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (92, 92, 255),
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 255),
)

_GREY_NAMED_INDICES: ta.AbstractSet[int] = frozenset([0, 7, 8, 15])

_CUBE_VALUES: ta.Sequence[int] = (0, 95, 135, 175, 215, 255)


@functools.cache
def _indexed_color_rgbs() -> ta.Sequence[tuple[int, int, int]]:
    rgbs: list[tuple[int, int, int]] = list(NAMED_COLOR_RGBS)
    for r in _CUBE_VALUES:
        for g in _CUBE_VALUES:
            for b in _CUBE_VALUES:
                rgbs.append((r, g, b))
    for i in range(24):
        v = 8 + 10 * i
        rgbs.append((v, v, v))
    return rgbs


def indexed_color_rgb(index: int) -> tuple[int, int, int]:
    return _indexed_color_rgbs()[index]


##


def _cube_component(c: int) -> int:
    # The cube's values are 0, 95, then steps of 40 - a naive c * 6 // 256 mismaps the low end.
    if c < 95:
        return round(c / 95)
    return 1 + round((c - 95) / 40)


@functools.cache
def rgb_to_indexed(color: st.RgbColor) -> IndexedColor:
    r, g, b = color.r, color.g, color.b
    _, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)  # noqa: E741

    if s < .15:
        # Low saturation: use the 24-step grey ramp (with pure black/white from the cube corners).
        grey = round(l * 25)
        if grey == 0:
            return IndexedColor(16)
        if grey == 25:
            return IndexedColor(231)
        return IndexedColor(231 + grey)

    return IndexedColor(
        16 +
        36 * _cube_component(r) +
        6 * _cube_component(g) +
        _cube_component(b),
    )


def _nearest_named(r: int, g: int, b: int) -> NamedColor:
    saturation = abs(r - g) + abs(g - b) + abs(b - r)
    best_index = 0
    best_distance: int | None = None
    for i, (cr, cg, cb) in enumerate(NAMED_COLOR_RGBS):
        # Skip the greys for saturated colors - grey is otherwise too often the nearest match.
        if saturation > 30 and i in _GREY_NAMED_INDICES:
            continue
        distance = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_index = i
    return NamedColor(best_index)


@functools.cache
def _rgb_to_named(color: st.RgbColor) -> NamedColor:
    return _nearest_named(color.r, color.g, color.b)


@functools.cache
def _indexed_to_named(color: IndexedColor) -> NamedColor:
    if color.index < 16:
        return NamedColor(color.index)
    return _nearest_named(*indexed_color_rgb(color.index))


def downgrade_color(color: st.Color, depth: ColorDepth) -> st.Color | None:
    """Return `color` representable at `depth`, or None if colors are unavailable at that depth."""

    if depth is ColorDepth.MONO:
        return None

    if depth is ColorDepth.TRUE:
        return color

    if depth is ColorDepth.ANSI_256:
        if isinstance(color, st.RgbColor):
            return rgb_to_indexed(color)
        return color

    if isinstance(color, st.RgbColor):
        return _rgb_to_named(color)
    if isinstance(color, IndexedColor):
        return _indexed_to_named(color)
    return color
