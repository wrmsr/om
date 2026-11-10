import abc
import typing as ta

from omcore import lang

from .generation import Generation
from .rounds import Round


##


class Observer(lang.Abstract):
    """
    Sees a generation happen: streaming delivery, statistics, logging. Observers do not affect it, so they compose
    as an unordered set.
    """

    @abc.abstractmethod
    def on_prefill(self, gen: Generation) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def on_round(self, gen: Generation, rnd: Round, kept: ta.Sequence[int]) -> None:
        raise NotImplementedError


class CompositeObserver(Observer):
    def __init__(self, observers: ta.Iterable[Observer] = ()) -> None:
        super().__init__()

        self._observers = list(observers)

    def on_prefill(self, gen: Generation) -> None:
        for o in self._observers:
            o.on_prefill(gen)

    def on_round(self, gen: Generation, rnd: Round, kept: ta.Sequence[int]) -> None:
        for o in self._observers:
            o.on_round(gen, rnd, kept)


class TokenCallbackObserver(Observer):
    """Calls `on_token(id)` for every emitted token, in order. It may raise `Cancelled` to abandon the generation."""

    def __init__(self, on_token: ta.Callable[[int], None]) -> None:
        super().__init__()

        self._on_token = on_token

    def on_prefill(self, gen: Generation) -> None:
        pass

    def on_round(self, gen: Generation, rnd: Round, kept: ta.Sequence[int]) -> None:
        for t in kept:
            self._on_token(t)
