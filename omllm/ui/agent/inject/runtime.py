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
        inj.bind(asl.asyncio.Cancellation, singleton=True),
        inj.bind(asl.Cancellation, to_key=asl.asyncio.Cancellation),

        inj.bind(asl.asyncio.Sleeps, singleton=True),
        inj.bind(asl.Sleeps, to_key=asl.asyncio.Sleeps),

        inj.bind(AsyncioGroupRunner, singleton=True),
        inj.bind(AsyncGroupRunner, to_key=AsyncioGroupRunner),
    ])

    #

    return inj.as_elements(*lst)
