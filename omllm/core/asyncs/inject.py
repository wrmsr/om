"""
Injector wiring. The `AsyncJobRunner` is bound as an async-managed singleton, one per injector like the process
manager: `aclose()`d when the injector's `AsyncExitStack` unwinds, so no job thread outlives what created it unnoticed.
"""
from omcore import inject as inj
from omcore.asyncs.asynclite import all as asl

from .asyncio import AsyncioGroupRunner
from .asyncio import AsyncioJobRunner
from .base import AsyncGroupRunner
from .base import AsyncJobRunner


##


def bind_asyncio_runtime() -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        inj.bind(asl.asyncio.All, singleton=True),
        inj.bind(asl.Cancellation, to_key=asl.asyncio.All),
        inj.bind(asl.Locks, to_key=asl.asyncio.All),
        inj.bind(asl.Sleeps, to_key=asl.asyncio.All),

        inj.bind(AsyncioGroupRunner, singleton=True),
        inj.bind(AsyncGroupRunner, to_key=AsyncioGroupRunner),
    ])

    #

    return inj.as_elements(*lst)


##


def bind_asyncio_job_runner(
        *,
        max_workers: int | None = None,
) -> inj.Elements:
    return inj.as_elements(
        inj.bind(
            AsyncioJobRunner,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(lambda: AsyncioJobRunner(max_workers=max_workers)),
        ),
        inj.bind(AsyncJobRunner, to_key=AsyncioJobRunner),
    )
