# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import typing as ta

from ...lite.timeouts import Timeout
from ...lite.timeouts import TimeoutLike


AwaitableT = ta.TypeVar('AwaitableT', bound=ta.Awaitable)


##


def asyncio_maybe_timeout(
        fut: AwaitableT,
        timeout: TimeoutLike = None,
) -> AwaitableT:
    if timeout is not None:
        try:
            seconds = Timeout.of(timeout)()
        except BaseException:
            asyncio.ensure_future(fut).cancel()
            raise
        fut = asyncio.wait_for(fut, seconds)  # type: ignore
    return fut
