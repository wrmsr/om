"""
The card: an updatable, expandable, lifecycle-bearing panel - the warm-window shape of a tool use.

A card lives in the live region while its subject is in flight: state advances (confirming -> running -> complete /
denied / failed), the summary and detail mutate freely, the detail expands and collapses (keyboard or click). When its
subject finalizes, the app commits the card's rendered rows to scrollback and drops it from the stack - the full
warm-window lifecycle. Confirmation is a callback the app resolves (bound keys, clicks); the card itself just displays
and remembers.
"""
import enum
import typing as ta

from ..events.types import Event
from ..events.types import MouseEvent
from ..events.types import MouseEventKind
from ..text.parts import TextParts
from ..text.segments import Segment
from ..text.wrap import wrap_segments
from .base import Control


##


class CardState(enum.Enum):
    PENDING = enum.auto()
    CONFIRMING = enum.auto()
    RUNNING = enum.auto()
    COMPLETE = enum.auto()
    DENIED = enum.auto()
    FAILED = enum.auto()


_STATE_GLYPHS: ta.Mapping[CardState, str] = {
    CardState.PENDING: '·',
    CardState.CONFIRMING: '?',
    CardState.RUNNING: '*',
    CardState.COMPLETE: '✓',
    CardState.DENIED: '✗',
    CardState.FAILED: '✗',
}

TERMINAL_CARD_STATES: ta.AbstractSet[CardState] = frozenset([
    CardState.COMPLETE,
    CardState.DENIED,
    CardState.FAILED,
])


class Card(Control):
    def __init__(
            self,
            summary: TextParts = (),
            *,
            state: CardState = CardState.PENDING,
            detail: ta.Sequence[ta.Sequence[Segment]] = (),
            expanded: bool = False,
            on_confirm: ta.Callable[[bool], None] | None = None,
    ) -> None:
        super().__init__()

        self._summary = tuple(summary)
        self._state = state
        self._detail = tuple(tuple(row) for row in detail)
        self._expanded = expanded
        self._on_confirm = on_confirm

    @property
    def state(self) -> CardState:
        return self._state

    @property
    def is_terminal(self) -> bool:
        return self._state in TERMINAL_CARD_STATES

    @property
    def expanded(self) -> bool:
        return self._expanded

    def set_state(self, state: CardState) -> None:
        self._state = state

    def set_summary(self, summary: TextParts) -> None:
        self._summary = tuple(summary)

    def set_detail(self, detail: ta.Sequence[ta.Sequence[Segment]]) -> None:
        self._detail = tuple(tuple(row) for row in detail)

    def toggle_expanded(self) -> None:
        if self._detail:
            self._expanded = not self._expanded

    def respond(self, allowed: bool) -> None:
        """Resolve a CONFIRMING card. The app decides the next state via its callback."""

        if self._state is CardState.CONFIRMING and self._on_confirm is not None:
            self._on_confirm(allowed)

    ##
    # Rendering

    def _glyph_tag(self) -> str:
        return f'card.glyph.{self._state.name.lower()}'

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        expander = ('[-] ' if self._expanded else '[+] ') if self._detail else '    '
        header: list[Segment] = [
            Segment(expander, 'card.expander'),
            Segment(_STATE_GLYPHS[self._state] + ' ', self._glyph_tag()),
            *(Segment(text, style) for text, style in self._summary if text),
        ]

        rows: list[ta.Sequence[Segment]] = list(wrap_segments(header, width))

        if self._state is CardState.CONFIRMING:
            rows.append([
                Segment('    '),
                Segment(' allow (f10) ', 'card.allow'),
                Segment('  '),
                Segment(' deny (f2) ', 'card.deny'),
            ])

        if self._expanded:
            for detail_row in self._detail:
                for wrapped in wrap_segments([Segment('  '), *detail_row], width):
                    rows.append(wrapped)  # noqa: PERF402

        return rows

    ##
    # Events (clicks routed by the app via StackLayout.hit; local y arrives in the event)

    def handle_event(self, event: Event) -> bool:
        if isinstance(event, MouseEvent) and event.kind is MouseEventKind.DOWN:
            if event.y == 0:
                self.toggle_expanded()
                return True
        return False
