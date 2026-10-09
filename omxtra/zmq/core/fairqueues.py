import collections
import typing as ta


T = ta.TypeVar('T')


##


class FairQueue(ta.Generic[T]):
    """A rotation of members, each present at most once - such as the peers with messages to receive."""

    def __init__(self) -> None:
        super().__init__()

        self._q: collections.deque[T] = collections.deque()
        self._members: set[T] = set()

    def __len__(self) -> int:
        return len(self._q)

    def __contains__(self, m: T) -> bool:
        return m in self._members

    def add(self, m: T) -> None:
        if m not in self._members:
            self._members.add(m)
            self._q.append(m)

    def remove(self, m: T) -> None:
        if m in self._members:
            self._members.remove(m)
            self._q.remove(m)

    def pop(self) -> T | None:
        """Remove and return the member at the front, which the caller may add again to place it at the back."""

        if not self._q:
            return None
        m = self._q.popleft()
        self._members.remove(m)
        return m

    def find(self, pred: ta.Callable[[T], bool]) -> T | None:
        """Return the first member satisfying pred, rotating it and every member before it to the back."""

        for _ in range(len(self._q)):
            m = self._q[0]
            self._q.rotate(-1)
            if pred(m):
                return m
        return None
