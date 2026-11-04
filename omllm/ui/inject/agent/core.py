import typing as ta

from omcore import inject as inj
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ....core.asyncs.base import AsyncGroupRunner
from ...config import UiConfig
from ...setup import AgentSetup


##


# How each kind of agent message is shown to the model. Unmapped kinds stay invisible, InfoAgentMessage included: the
# synthetic tool results already tell the model about an interruption.
AgentMessageProjectors: ta.TypeAlias = ta.Mapping[type[agn.AgentMessage], agn.AgentMessageProjector]


def bind_agent_message_projector(
        message_cls: type[agn.AgentMessage],
        projector: agn.AgentMessageProjector,
) -> inj.Elements:
    return inj.bind_map_entry_const(AgentMessageProjectors, message_cls, projector)


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

        # The model's view of the transcript. The map binder is bound even with no entries so the mapping resolves.
        inj.map_binder[type[agn.AgentMessage], agn.AgentMessageProjector](),
        inj.bind(agn.TypeMapAgentMessageProjector, singleton=True),
        inj.bind(agn.AgentMessageProjector, to_key=agn.TypeMapAgentMessageProjector),
        inj.bind(agn.StandardLlmContextBuilder, singleton=True),
        inj.bind(agn.LlmContextBuilder, to_key=agn.StandardLlmContextBuilder),

        # What a run reaches for when its view is too big for the model and pruning has not been enough, and what
        # /compact asks for outright: a summary of the older part of the transcript, asked of the model itself.
        inj.bind(agn.SummarizingContextCompactor, singleton=True),
        inj.bind(agn.ContextCompactor, to_key=agn.SummarizingContextCompactor),

        inj.bind(agn.StandardContextLifecycleManager, singleton=True),
        inj.bind(agn.ContextLifecycleManager, to_key=agn.StandardContextLifecycleManager),

        inj.bind(agn.ContextCompactionRunner, singleton=True),
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
