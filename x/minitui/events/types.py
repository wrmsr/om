"""Typed input events - what the parser emits and apps consume."""
import enum

from omcore import dataclasses as dc
from omcore import lang

from .keys import Key


##


class Event(lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class KeyEvent(Event, lang.Final):
    key: Key

    _: dc.KW_ONLY

    # The insertable text, when the key is a plain printable.
    text: str | None = None


@dc.dataclass(frozen=True)
class PasteEvent(Event, lang.Final):
    text: str


class MouseEventKind(enum.Enum):
    DOWN = enum.auto()
    UP = enum.auto()
    MOVE = enum.auto()
    SCROLL_UP = enum.auto()
    SCROLL_DOWN = enum.auto()
    SCROLL_LEFT = enum.auto()
    SCROLL_RIGHT = enum.auto()


@dc.dataclass(frozen=True)
class MouseEvent(Event, lang.Final):
    kind: MouseEventKind
    x: int
    y: int

    _: dc.KW_ONLY

    button: int = 0
    ctrl: bool = False
    alt: bool = False
    shift: bool = False


@dc.dataclass(frozen=True)
class FocusEvent(Event, lang.Final):
    gained: bool


@dc.dataclass(frozen=True)
class ResizeEvent(Event, lang.Final):
    """Synthesized by the runtime from SIGWINCH, never parsed from the byte stream."""

    height: int
    width: int


##
# Terminal responses to queries we send. These flow through the input stream like everything else.


@dc.dataclass(frozen=True)
class CursorPositionEvent(Event, lang.Final):
    """A CPR (DSR 6) response. Coordinates are 0-based (the wire format's 1-based row;col is normalized)."""

    x: int
    y: int


@dc.dataclass(frozen=True)
class ModeReportEvent(Event, lang.Final):
    """A DECRQM report (CSI ? mode ; value $ y): value 1/2 = set/reset, 3/4 = permanently, 0 = unrecognized."""

    mode: int
    value: int


@dc.dataclass(frozen=True)
class KittyFlagsEvent(Event, lang.Final):
    """The response to a kitty keyboard protocol query (CSI ? flags u)."""

    flags: int


@dc.dataclass(frozen=True)
class UnknownSequenceEvent(Event, lang.Final):
    """An escape sequence we didn't recognize - kept as an event for debuggability rather than silently dropped."""

    text: str
