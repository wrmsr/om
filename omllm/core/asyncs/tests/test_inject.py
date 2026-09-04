import pytest

from omcore import inject as inj

from ..asyncio import AsyncioJobRunner
from ..base import AsyncJob
from ..base import AsyncJobRunner
from ..inject import bind_job_runner


class _One(AsyncJob[int]):
    def run(self) -> int:
        return 1


@pytest.mark.asyncs('asyncio')
async def test_bind_job_runner():
    seen = {}
    async with inj.create_async_managed_injector(
        bind_job_runner(),
        factory=inj.create_asyncio_injector,
    ) as injector:
        runner = await injector[AsyncJobRunner]
        assert isinstance(runner, AsyncioJobRunner)
        assert await injector[AsyncJobRunner] is runner  # singleton
        assert await runner.run(_One()) == 1
        seen['runner'] = runner

    # Closed on injector teardown.
    assert seen['runner'].closed
