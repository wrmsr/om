"""
When a generation stops, and how many of a round's accepted tokens it keeps. A terminator answers `cut` before the
round is committed, because the recurrent state cannot be rewound afterwards: the state that is stored covers exactly
the emitted tokens. Terminators compose by taking the earliest stop, so they are an unordered set.
"""
import abc
import typing as ta

from omcore import lang

from ..tokenizer import Tokenizer
from .generation import Generation


##


class Terminator(lang.Abstract):
    @abc.abstractmethod
    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        """How many of a round's accepted `tokens` to keep and then stop, or None to keep all and go on."""

        raise NotImplementedError

    @abc.abstractmethod
    def poll(self, gen: Generation) -> bool:
        """True to cancel the generation (polled between prefill chunks and rounds)."""

        raise NotImplementedError


class CompositeTerminator(Terminator):
    def __init__(self, terminators: ta.Iterable[Terminator] = ()) -> None:
        super().__init__()

        self._terminators = list(terminators)

    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        cuts = [c for t in self._terminators if (c := t.cut(gen, tokens)) is not None]
        return min(cuts) if cuts else None

    def poll(self, gen: Generation) -> bool:
        return any(t.poll(gen) for t in self._terminators)


class EosTerminator(Terminator):
    """Stops at the first end-of-sequence id, keeping it: the end of turn is part of the conversation's ids."""

    def __init__(self, eos_ids: ta.Iterable[int]) -> None:
        super().__init__()

        self._eos_ids = frozenset(eos_ids)

    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        for i, t in enumerate(tokens):
            if t in self._eos_ids:
                return i + 1
        return None

    def poll(self, gen: Generation) -> bool:
        return False


class BudgetTerminator(Terminator):
    def __init__(self, max_new_tokens: int) -> None:
        super().__init__()

        self._max_new_tokens = max_new_tokens

    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        left = self._max_new_tokens - len(gen.tokens)
        return max(0, left) if len(tokens) >= left else None

    def poll(self, gen: Generation) -> bool:
        return False


class CallbackTerminator(Terminator):
    """Cancellation from outside: `should_stop()` is polled between prefill chunks and rounds."""

    def __init__(self, should_stop: ta.Callable[[], bool]) -> None:
        super().__init__()

        self._should_stop = should_stop

    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        return None

    def poll(self, gen: Generation) -> bool:
        return self._should_stop()


class StopStringTerminator(Terminator):
    """
    Stops when the decoded text contains one of `stops`, keeping the token that completes it; `stopped_at` is then the
    text position where the stop string starts (the caller trims there -- stop strings are not part of the answer).
    The cut comes before the commit, so each round is decoded tentatively from a copy of the committed text's decoder.

    `end_ids` (the end of turn) end the text: nothing at or after one is scanned (whatever ends the generation there is
    another terminator's business). A speculative round can carry tokens past the end of turn -- the chat template's
    newline after it, say -- and a stop string must not match across it.
    """

    def __init__(
            self,
            tok: Tokenizer,
            stops: ta.Iterable[str],
            *,
            end_ids: ta.Iterable[int] = (),
    ) -> None:
        super().__init__()

        self._tok = tok
        self._stops = [s for s in stops if s]
        self._end_ids = frozenset(end_ids)
        self._longest = max((len(s) for s in self._stops), default=0)

        self._text = ''  # the committed tokens' text
        self._buf = b''  # their trailing incomplete UTF-8 bytes
        self.stopped_at: int | None = None

    def _decode(self, buf: bytes, i: int) -> tuple[str, bytes]:
        streamer = Tokenizer.Streamer(self._tok)
        streamer.buf = buf
        piece = streamer.push(i)
        return piece, streamer.buf

    def cut(self, gen: Generation, tokens: ta.Sequence[int]) -> int | None:
        if not self._stops:
            return None

        text = self._text
        buf = self._buf
        for n, t in enumerate(tokens):
            if t in self._end_ids:
                break
            piece, buf = self._decode(buf, t)
            if not piece:
                continue
            start = max(0, len(text) - self._longest + 1)
            text += piece
            hits = [at for s in self._stops if (at := text.find(s, start)) >= 0]
            if hits:
                self.stopped_at = min(hits)
                return n + 1

        # nothing stops this round: whatever another terminator decides, this text is now the committed text
        self._text = text
        self._buf = buf
        return None

    def poll(self, gen: Generation) -> bool:
        return False
