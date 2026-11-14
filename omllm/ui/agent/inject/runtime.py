from omcore import inject as inj
from omcore.asyncs.asynclite import all as asl

from ....core.asyncs.asyncio import AsyncioGroupRunner
from ....core.asyncs.base import AsyncGroupRunner
from ..config import AgentConfig


##


def bind_runtime(config: AgentConfig) -> inj.Elements:
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
