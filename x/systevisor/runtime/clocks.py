import abc
import time

from omcore.lite.abstract import Abstract


class SystevisorClock(Abstract):
    @abc.abstractmethod
    def monotonic(self) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def wall_time(self) -> float:
        raise NotImplementedError


class SystevisorSystemClock(SystevisorClock):
    def monotonic(self) -> float:
        return time.monotonic()

    def wall_time(self) -> float:
        return time.time()
