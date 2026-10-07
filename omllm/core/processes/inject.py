"""
Injector wiring. The `ProcessManager` is bound as an async-managed singleton: it is `start()`ed on first provision and
`aclose()`d when the injector's `AsyncExitStack` unwinds - so nothing keeps a module-global handle to it, and a new
manager can be created and torn down cleanly per injector.
"""
from omcore import inject as inj

from .asyncio.manager import AsyncioProcessManager
from .managers.types import ManagerConfig
from .managers.types import ProcessManager
from .managers.types import RootProcessScope


##


def bind_root_process_scope() -> inj.Elements:
    """Binds the root scope of whichever `ProcessManager` is bound, local or remote, for the ui to hand to tools."""

    return inj.as_elements(
        inj.bind(RootProcessScope, to_fn=inj.KwargsTarget.of(lambda pm: pm.root, pm=ProcessManager)),
    )


def bind_process_manager(
        config: ManagerConfig | None = None,
) -> inj.Elements:
    lst: list[inj.Elemental] = []

    lst.append(inj.bind(config if config is not None else ManagerConfig()))

    lst.append(bind_root_process_scope())

    lst.extend([
        inj.bind(
            AsyncioProcessManager,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(AsyncioProcessManager),
        ),
        inj.bind(ProcessManager, to_key=AsyncioProcessManager),
    ])

    return inj.as_elements(*lst)
