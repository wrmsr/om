import concurrent.interpreters
import importlib
import sys
import threading
import time
import typing as ta

from ..... import dataclasses as dc
from ...interpreters import SubinterpreterCaller
from ...interpreters import SubinterpreterService


##


CODE_IDENTITY = 'omcore-daemons-subinterpreter-integration-v1'


@dc.dataclass(frozen=True, kw_only=True)
class TestServiceConfig:
    extension_module: str


class TestSubinterpreterService(SubinterpreterService):
    def __init__(self, config: TestServiceConfig) -> None:
        super().__init__()

        self._extension = importlib.import_module(config.extension_module)

    def dispatch(
            self,
            method: str,
            args: tuple[ta.Any, ...],
            kwargs: ta.Mapping[str, ta.Any],
    ) -> ta.Any:
        if method == 'info':
            if args or kwargs:
                raise TypeError('info takes no arguments')
            return {
                'interpreter_id': concurrent.interpreters.get_current().id,
                'gil_enabled': sys._is_gil_enabled(),  # noqa
                'thread_ident': threading.get_ident(),
            }

        if method == 'increment':
            if len(args) != 1 or kwargs:
                raise TypeError('increment takes one positional argument')
            return self._extension.increment(args[0])

        if method == 'fail':
            if args or kwargs:
                raise TypeError('fail takes no arguments')
            raise ValueError('intentional service failure')

        if method == 'unpicklable':
            if args or kwargs:
                raise TypeError('unpicklable takes no arguments')
            return lambda: None

        if method == 'sleep':
            if len(args) != 1 or kwargs:
                raise TypeError('sleep takes one positional argument')
            time.sleep(args[0])
            return None

        raise ValueError(f'Unknown test method: {method!r}')


def make_test_service(config: TestServiceConfig) -> SubinterpreterService:
    return TestSubinterpreterService(config)


class TestClient:
    def __init__(self, caller: SubinterpreterCaller) -> None:
        super().__init__()

        self._caller = caller

    @property
    def caller(self) -> SubinterpreterCaller:
        return self._caller

    def info(self) -> ta.Mapping[str, ta.Any]:
        return self._caller.invoke('info')

    def increment(self, delta: int) -> tuple[int, int]:
        return self._caller.invoke('increment', (delta,))

    def fail(self) -> None:
        self._caller.invoke('fail')

    def unpicklable(self) -> None:
        self._caller.invoke('unpicklable')

    def sleep(self, delay_s: float, *, timeout_s: float) -> None:
        self._caller.invoke('sleep', (delay_s,), timeout=timeout_s)
