import typing as ta

from ..decode.state import Snapshot
from ..decode.stores import StateStore
from .cache import PrefixCache


##


class PrefixStateStore(StateStore):
    """The prefix cache as the generation loop's state store."""

    def __init__(self, cache: PrefixCache) -> None:
        super().__init__()

        self._cache = cache

    def lookup(self, ids: ta.Sequence[int]) -> Snapshot | None:
        return self._cache.lookup(ids)

    def offer(self, make: ta.Callable[[], Snapshot]) -> None:
        self._cache.put(make())
