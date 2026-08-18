"""
A tiny generator-as-parser engine.

The parse logic is written as a generator that *asks* for characters by yielding `Read1(timeout_s)` and emits events via
`emit()`; the engine pumps characters in from `feed()`. Timeouts are cooperative and clock-free: the engine never looks
at a clock - it exposes the currently-pending read's timeout (`pending_timeout_s`), and whoever owns the real event loop
calls `flush_timeout()` when that much time passes without input. Tests just call `flush_timeout()` directly, making
every timeout path exactly reproducible.

(The shape is a reimplementation of the idea in textual's `_parser.py`, on structured events and without the
buffering/peek machinery.)
"""
import collections
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .types import Event


ParseGenerator: ta.TypeAlias = ta.Generator['Read1', str]


##


class ParseTimeoutError(Exception):
    """Thrown into the parse generator at a timed `Read1` when the timeout elapses. Purely control flow."""


@dc.dataclass(frozen=True)
class Read1(lang.Final):
    """A request for one character; `timeout_s` of None waits indefinitely."""

    timeout_s: float | None = None


class EventParser(lang.Abstract):
    """
    Drives a subclass's `_run` parse generator, buffering emitted events.

    Not reentrant: feed/flush_timeout must not be called from within the generator.
    """

    def __init__(self) -> None:
        super().__init__()

        self._events: collections.deque[Event] = collections.deque()
        self._gen: ParseGenerator = self._run()
        self._pending: Read1 = check.isinstance(next(self._gen), Read1)

    def _run(self) -> ParseGenerator:
        raise NotImplementedError

    def emit(self, event: Event) -> None:
        self._events.append(event)

    @property
    def pending_read(self) -> Read1:
        """
        The read the generator is currently waiting on.

        Identity changes on every consumed character, so loop code can tell "same wait, deadline already set" from "a
        new wait began".
        """

        return self._pending

    @property
    def pending_timeout_s(self) -> float | None:
        """The timeout of the read the generator is currently waiting on, if any."""

        return self._pending.timeout_s

    def _drain(self) -> list[Event]:
        events = list(self._events)
        self._events.clear()
        return events

    def feed(self, data: str) -> list[Event]:
        for c in data:
            self._pending = check.isinstance(self._gen.send(c), Read1)
        return self._drain()

    def flush_timeout(self) -> list[Event]:
        """
        Signal that the pending read's timeout elapsed.

        Calling this when the pending read has no timeout is a no-op (a benign race with arriving input).
        """

        if self._pending.timeout_s is None:
            return []
        self._pending = check.isinstance(self._gen.throw(ParseTimeoutError()), Read1)
        return self._drain()
