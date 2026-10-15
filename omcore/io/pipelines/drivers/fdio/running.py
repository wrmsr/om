# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import time
import typing as ta

from ....fdio.manager import FdioManager


##


def fdio_run_until(
        manager: FdioManager,
        cond: ta.Callable[[], bool],
        *,
        timeout_s: ta.Optional[float] = None,
        clock: ta.Callable[[], float] = time.monotonic,
) -> bool:
    """
    Polls the manager until `cond` holds or the timeout expires, returning whether it holds. This is how blocking code
    gets multi-transport behavior without asyncio: each poll blocks, tickless, until a descriptor is ready, a handler's
    deadline is due, or the timeout's remainder has passed. With no timeout and nothing to wake the manager, it blocks
    for good, so a condition which only something external can bring about needs a timeout.
    """

    if timeout_s is not None and timeout_s < 0.:
        raise ValueError(timeout_s)

    deadline = None if timeout_s is None else clock() + timeout_s
    while not cond():
        if deadline is None:
            manager.poll()
            continue

        remaining = deadline - clock()
        if remaining <= 0.:
            return cond()
        manager.poll(timeout=remaining)

    return True
