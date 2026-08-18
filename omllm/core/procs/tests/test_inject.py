import pytest

from omcore import inject as inj

from ..asyncio.manager import AsyncioProcessManager
from ..inject import bind_process_manager
from ..manager import ManagerConfig
from ..manager import ProcessManager
from ..types.specs import ProcessSpec


@pytest.mark.asyncs('asyncio')
async def test_bind_process_manager():
    seen = {}
    async with inj.create_async_managed_injector(
        bind_process_manager(ManagerConfig()),
        factory=inj.create_asyncio_injector,
    ) as injector:
        pm = await injector[ProcessManager]
        assert isinstance(pm, AsyncioProcessManager)
        assert pm.started
        assert await injector[ProcessManager] is pm  # singleton
        run = await pm.root.run(ProcessSpec(['sh', '-c', 'echo injected']))
        assert run.stdout == b'injected\n'
        seen['pm'] = pm

    # Closed on injector teardown.
    assert seen['pm'].closed
