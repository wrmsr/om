import asyncio
import sys
import contextlib


##


_PY39 = sys.version_info >= (3, 9)
_PY311 = sys.version_info >= (3, 11)


def _spawn(coro, name, context):
    if context is not None:
        if not _PY311:
            raise RuntimeError("context= requires Python 3.11+")
        return asyncio.create_task(coro, name=name, context=context)
    return asyncio.create_task(coro, name=name)  # name= exists since 3.8


def _request_cancel(task, msg):
    if _PY39:
        task.cancel(msg=msg)  # msg= is 3.9+; it rides along in the CancelledError
    else:
        task.cancel()


@contextlib.asynccontextmanager
async def daemon_task(
        coro,
        *,
        name="daemon_task",
        context=None,
        cancel_msg="daemon_task teardown",
):
    task = _spawn(coro, name, context)
    try:
        yield task
    finally:
        _request_cancel(task, cancel_msg)

        # Reap via asyncio.wait(): unlike `await task`, it never raises the *child's* exception, so any CancelledError
        # caught here is unambiguously our own. Identical semantics on 3.8 through 3.12+.
        our_cancel = None
        while not task.done():
            try:
                await asyncio.wait({task})
            except asyncio.CancelledError as exc:
                our_cancel = exc  # note it, keep reaping

        child_exc = None if task.cancelled() else task.exception()

        if our_cancel is not None:
            if child_exc is not None:
                our_cancel.__context__ = child_exc  # keep it visible in tracebacks
            raise our_cancel
        if child_exc is not None:
            raise child_exc

