"""
Injector wiring. The `AsyncJobRunner` is bound as an async-managed singleton, one per injector like the process
manager: `aclose()`d when the injector's `AsyncExitStack` unwinds, so no job thread outlives what created it unnoticed.
"""
from omcore import inject as inj

from .asyncio import AsyncioJobRunner
from .base import AsyncJobRunner


##


def bind_job_runner(
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
