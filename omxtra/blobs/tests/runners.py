"""
Drivers for async test scenarios. Async code which never actually suspends (stores over sync backends, or over
SyncAsyncHttpClient) is driven synchronously with sync_await, with threads for concurrency. Async code over real event
loop clients is driven with asyncio.
"""
import abc
import asyncio
import threading
import typing as ta

from omcore import lang


T = ta.TypeVar('T')


##


class ScenarioRunner(lang.Abstract):
    @abc.abstractmethod
    def run(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> T:
        """Drives one scenario to completion."""

        raise NotImplementedError

    @abc.abstractmethod
    def gather(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> ta.Awaitable[list[T | BaseException]]:
        """Awaited inside a scenario to run operations concurrently. Results are in order, exceptions returned."""

        raise NotImplementedError


class SyncAwaitScenarioRunner(ScenarioRunner):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    def run(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> T:
        return lang.sync_await(fn())

    async def gather(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> list[T | BaseException]:
        # Blocking inside a coroutine is fine here: it is only ever driven by sync_await.
        results: list[ta.Any] = [None] * len(fns)

        def worker(i: int) -> None:
            try:
                results[i] = lang.sync_await(fns[i]())
            except BaseException as e:  # noqa
                results[i] = e

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(fns))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return results


class AsyncioScenarioRunner(ScenarioRunner):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    def run(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> T:
        async def inner() -> T:
            return await fn()

        return asyncio.run(inner())

    async def gather(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> list[T | BaseException]:
        return list(await asyncio.gather(*[fn() for fn in fns], return_exceptions=True))
