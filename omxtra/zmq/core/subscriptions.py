from .errors import PeerViolationError


##


class SubscriptionCounts:
    """Reference-counted byte prefixes, matched linearly against a message's first frame."""

    def __init__(self, *, max_prefixes: int | None = None) -> None:
        super().__init__()

        self._max_prefixes = max_prefixes
        self._counts: dict[bytes, int] = {}

    def __len__(self) -> int:
        return len(self._counts)

    def __contains__(self, prefix: bytes) -> bool:
        return prefix in self._counts

    def prefixes(self) -> list[bytes]:
        return list(self._counts)

    def add(self, prefix: bytes) -> bool:
        """Add a reference, returning whether the prefix became effective."""

        if (n := self._counts.get(prefix)) is not None:
            self._counts[prefix] = n + 1
            return False

        if self._max_prefixes is not None and len(self._counts) >= self._max_prefixes:
            raise PeerViolationError(f'more than {self._max_prefixes} subscription prefixes')
        self._counts[prefix] = 1
        return True

    def remove(self, prefix: bytes) -> bool:
        """Remove a reference if present, returning whether the prefix stopped being effective."""

        if (n := self._counts.get(prefix)) is None:
            return False
        if n > 1:
            self._counts[prefix] = n - 1
            return False
        del self._counts[prefix]
        return True

    def matches(self, topic: bytes) -> bool:
        return any(topic.startswith(p) for p in self._counts)
