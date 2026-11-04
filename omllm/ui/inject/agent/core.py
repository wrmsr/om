from omcore import inject as inj
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ....core.asyncs.base import AsyncGroupRunner
from ...config import UiConfig
from ...setup import AgentSetup


##


def bind_core(config: UiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        # What the loop needs of its runtime: the ui is asyncio, so the loop gets asyncio's cancellation, task groups,
        # and sleeps.
        inj.bind(asl.asyncio.Cancellation, singleton=True),
        inj.bind(asl.Cancellation, to_key=asl.asyncio.Cancellation),
        inj.bind(AsyncioGroupRunner, singleton=True),
        inj.bind(AsyncGroupRunner, to_key=AsyncioGroupRunner),
        inj.bind(asl.asyncio.Sleeps, singleton=True),
        inj.bind(asl.Sleeps, to_key=asl.asyncio.Sleeps),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),
    ])

    #

    lst.extend([
        inj.bind(AgentSetup, singleton=True),
    ])

    #

    return inj.as_elements(*lst)
