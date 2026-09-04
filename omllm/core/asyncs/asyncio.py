"""The asyncio group runner: a TaskGroup, with the group's contract mapped onto its behavior."""
import asyncio
import typing as ta

from omcore import lang

from .base import AsyncGroupCancelledError
from .base import AsyncGroupMemberCancelledError
from .base import AsyncGroupRunner


T = ta.TypeVar('T')


##


class AsyncioGroupCancelledError(AsyncGroupCancelledError, asyncio.CancelledError):
    """An asyncio.CancelledError too, so the task it unwinds through ends cancelled."""


class AsyncioGroupRunner(AsyncGroupRunner):
    async def run(self, fns: ta.Sequence[ta.Callable[[], ta.Awaitable[T]]]) -> list[T]:
        outcomes: list[lang.Maybe[T]] = [lang.nothing() for _ in fns]

        async def member(i: int, fn: ta.Callable[[], ta.Awaitable[T]]) -> None:
            outcomes[i] = lang.just(await fn())

        tasks: list[asyncio.Task] = []

        try:
            async with asyncio.TaskGroup() as tg:
                for i, fn in enumerate(fns):
                    tasks.append(tg.create_task(member(i, fn)))

        except asyncio.CancelledError as e:
            # The group re-raises the calling task's cancellation only once every member is done - and only when none
            # of them raised: a member's error takes precedence and comes out as a group, with the task re-cancelled to
            # keep its count.
            raise AsyncioGroupCancelledError(outcomes) from e

        # A member which ended cancelled is passed over by the group, so is found here. The group only cancels members
        # while aborting, after which it raises - so on this path any cancelled member was cancelled from under it.
        if strays := [i for i, t in enumerate(tasks) if t.cancelled()]:
            raise ExceptionGroup(
                'Cancelled members of an async group',
                [AsyncGroupMemberCancelledError(i) for i in strays],
            )

        return [o.must() for o in outcomes]
