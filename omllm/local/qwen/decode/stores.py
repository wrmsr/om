import abc
import typing as ta

from omcore import lang

from .state import Snapshot


##


class StateStore(lang.Abstract):
    """
    Where resumable states live between requests: the prefix cache is one (prefix/store.py). `offer` takes a thunk so a
    store that would not keep the state never pays for exporting it.
    """

    @abc.abstractmethod
    def lookup(self, ids: ta.Sequence[int]) -> Snapshot | None:
        """A state whose tokens are a prefix of `ids` (the longest one), as a private copy, or None."""

        raise NotImplementedError

    @abc.abstractmethod
    def offer(self, make: ta.Callable[[], Snapshot]) -> None:
        raise NotImplementedError


class NullStateStore(StateStore):
    def lookup(self, ids: ta.Sequence[int]) -> Snapshot | None:
        return None

    def offer(self, make: ta.Callable[[], Snapshot]) -> None:
        pass
