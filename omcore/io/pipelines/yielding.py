# ruff: noqa: UP045
# @om-lite
"""
TODO:
 - timeslice policy, per TODO.md - wants a clock, likely off IoPipelineScheduling
"""
import abc
import typing as ta

from ...lite.abstract import Abstract


##


class IoPipelineYieldPolicy(Abstract):
    """
    Decides when a handler doing bounded work on behalf of the driver should stop and defer the rest.

    Deferring is a fairness yield, not a latency one: it lets the driver interleave reads, writes and timers before the
    handler resumes. It cannot interrupt work already in progress, so a policy only bounds how much is attempted
    between yields.
    """

    @abc.abstractmethod
    def new_turn(self) -> ta.Callable[[], bool]:
        """
        Returns a predicate for a single turn of work - true means stop and defer.

        The predicate holds the turn's state, so one policy instance may be shared by any number of handlers, and is
        consulted before each unit of work rather than after.
        """

        raise NotImplementedError


##


class CountingIoPipelineYieldPolicy(IoPipelineYieldPolicy):
    """Yields after a fixed number of units of work."""

    def __init__(self, max_units: int) -> None:
        super().__init__()

        # A zero budget would yield before ever doing a unit of work - an infinite defer loop.
        if max_units < 1:
            raise ValueError(f'max_units must be positive: {max_units!r}')
        self._max_units = max_units

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._max_units!r})'

    @property
    def max_units(self) -> int:
        return self._max_units

    def new_turn(self) -> ta.Callable[[], bool]:
        state = [0]
        max_units = self._max_units

        def should_yield() -> bool:
            if state[0] >= max_units:
                return True
            state[0] += 1
            return False

        return should_yield


##


class NeverIoPipelineYieldPolicy(IoPipelineYieldPolicy):
    """Never yields - the work runs to completion in one turn."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    def new_turn(self) -> ta.Callable[[], bool]:
        return lambda: False
