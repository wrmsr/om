# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
import abc
import collections
import typing as ta

from ....lite.abstract import Abstract
from ....lite.check import check
from .types import IoPipelineMultiplexStreamKey


##


class IoPipelineMultiplexOutputScheduler(Abstract):
    """
    Chooses which stream sends next when several have sendable output and the connection is writable.

    The multiplexer reports which streams are ready - have output which could be sent right now - asks for the next
    stream before each unit of output, and accounts the cost of what it sent. Implementations must not starve a stream
    which stays ready.
    """

    @abc.abstractmethod
    def add(self, key: IoPipelineMultiplexStreamKey, *, weight: int = 1) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def remove(self, key: IoPipelineMultiplexStreamKey) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def set_weight(self, key: IoPipelineMultiplexStreamKey, weight: int) -> None:
        """Changes a stream's weight; a turn already under way keeps its allowance."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_ready(self, key: IoPipelineMultiplexStreamKey, ready: bool) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def is_ready(self, key: IoPipelineMultiplexStreamKey) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def next(self) -> ta.Optional[IoPipelineMultiplexStreamKey]:
        """The ready stream which should send its next unit, or None if no stream is ready."""

        raise NotImplementedError

    @abc.abstractmethod
    def account(self, key: IoPipelineMultiplexStreamKey, cost: int) -> None:
        """Records that `cost` was sent on the stream returned by the last `next()`."""

        raise NotImplementedError


##


@ta.final
class RoundRobinIoPipelineMultiplexOutputScheduler(IoPipelineMultiplexOutputScheduler):
    """
    Deficit round robin: each ready stream in turn may send up to `quantum * weight` cost (always at least one unit)
    before the next ready stream gets its turn. Units are never split by the scheduler; a unit larger than the quantum
    simply ends that stream's turn.
    """

    def __init__(self, quantum: int = 16 * 1024) -> None:
        super().__init__()

        check.arg(quantum > 0)
        self._quantum = quantum

        self._weights: ta.Dict[IoPipelineMultiplexStreamKey, int] = {}
        self._ready: ta.Set[IoPipelineMultiplexStreamKey] = set()
        self._rotation: ta.Deque[IoPipelineMultiplexStreamKey] = collections.deque()  # ready streams awaiting their turn  # noqa
        self._current: ta.Optional[IoPipelineMultiplexStreamKey] = None
        self._remaining = 0

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}({self._quantum!r})'

    @property
    def quantum(self) -> int:
        return self._quantum

    def add(self, key: IoPipelineMultiplexStreamKey, *, weight: int = 1) -> None:
        check.not_in(key, self._weights)
        check.arg(weight > 0)
        self._weights[key] = weight

    def remove(self, key: IoPipelineMultiplexStreamKey) -> None:
        if self._weights.pop(key, None) is None:
            return
        self._set_unready(key)

    def set_weight(self, key: IoPipelineMultiplexStreamKey, weight: int) -> None:
        check.in_(key, self._weights)
        check.arg(weight > 0)
        self._weights[key] = weight

    def _set_unready(self, key: IoPipelineMultiplexStreamKey) -> None:
        if key not in self._ready:
            return
        self._ready.discard(key)
        if self._current == key:
            self._current = None
            self._remaining = 0
        else:
            self._rotation.remove(key)

    def set_ready(self, key: IoPipelineMultiplexStreamKey, ready: bool) -> None:
        check.in_(key, self._weights)
        if ready:
            if key in self._ready:
                return
            self._ready.add(key)
            self._rotation.append(key)
        else:
            self._set_unready(key)

    def is_ready(self, key: IoPipelineMultiplexStreamKey) -> bool:
        return key in self._ready

    def next(self) -> ta.Optional[IoPipelineMultiplexStreamKey]:
        if self._current is not None:
            if self._remaining > 0:
                return self._current
            # Turn over: back of the line.
            self._rotation.append(self._current)
            self._current = None

        if not self._rotation:
            return None

        key = self._rotation.popleft()
        self._current = key
        self._remaining = self._quantum * self._weights[key]
        return key

    def account(self, key: IoPipelineMultiplexStreamKey, cost: int) -> None:
        check.arg(cost >= 0)
        if key == self._current:
            self._remaining -= max(cost, 1)
