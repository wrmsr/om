import contextvars
import typing as ta

from omcore import inject as inj
from omcore import lang
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ....core.asyncs.base import AsyncGroupRunner
from ....core.asyncs.inject import bind_job_runner
from ....core.eventbus import EventSubscriber
from ..config import Config


##


AgentEventSubscribers = ta.NewType('AgentEventSubscribers', ta.Sequence[EventSubscriber[agn.Event]])


@lang.cached_function
def agent_event_subscribers() -> inj.ItemsBinderHelper[EventSubscriber[agn.Event]]:
    return inj.items_binder_helper[EventSubscriber[agn.Event]](AgentEventSubscribers)


#


class HasOnEventAgent(ta.Protocol):
    def on_agent_event(self, ev: agn.Event) -> ta.Awaitable[None]: ...


def bind_on_agent_event_subscriber(cls: type[HasOnEventAgent]) -> inj.Elements:
    return agent_event_subscribers().bind_item(to_fn=inj.target(o=cls)(lambda o: o.on_agent_event))


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


class TURN_SCOPED(lang.Marker):  # noqa
    pass


_TURN_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._TURN_SCOPE_CONTEXT')

TURN_SCOPE: ta.Final = inj.DelimitedScope(TURN_SCOPED, context=inj.ContextVarScopeContext(_TURN_SCOPE_CONTEXT))


#


class ScopedTurnRunner(agn.TurnRunner):
    def __init__(
            self,
            *,
            injector: inj.AsyncInjector,
    ) -> None:
        super().__init__()

        self._injector = injector

    async def run_turn(self, params: agn.TurnParams) -> agn.TurnResult:
        async with inj.async_enter_scope(
                self._injector,
                TURN_SCOPE,
                {
                    inj.as_key(agn.TurnParams): params,
                },
        ):
            runner = await self._injector[agn.TurnLoopRunner]

            return await runner.run_turn(params)


##


def bind_agent(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        agent_event_subscribers().bind_items_provider(singleton=True),
    ])

    #

    lst.extend([
        inj.bind_scope(TURN_SCOPE),
        inj.bind_scope_seed(agn.TurnParams, TURN_SCOPE),

        inj.bind(ScopedTurnRunner, singleton=True),
        inj.bind(agn.TurnRunner, to_key=ScopedTurnRunner),

        # What the loop needs of its runtime: the ui is asyncio, so the loop gets asyncio's cancellation, task groups,
        # and sleeps.
        inj.bind(asl.asyncio.Cancellation, singleton=True),
        inj.bind(asl.Cancellation, to_key=asl.asyncio.Cancellation),
        inj.bind(AsyncioGroupRunner, singleton=True),
        inj.bind(AsyncGroupRunner, to_key=AsyncioGroupRunner),
        inj.bind(asl.asyncio.Sleeps, singleton=True),
        inj.bind(asl.Sleeps, to_key=asl.asyncio.Sleeps),

        # Blocking work (the quickjs tool's evals) runs off the loop through this, one per injector, closed with it.
        bind_job_runner(),

        # The model's view of the transcript. The map binder is bound even with no entries so the mapping resolves.
        inj.map_binder[type[agn.AgentMessage], agn.AgentMessageProjector](),
        inj.bind(agn.TypeMapAgentMessageProjector, singleton=True),
        inj.bind(agn.AgentMessageProjector, to_key=agn.TypeMapAgentMessageProjector),
        inj.bind(agn.StandardLlmContextBuilder, singleton=True),
        inj.bind(agn.LlmContextBuilder, to_key=agn.StandardLlmContextBuilder),

        inj.bind(agn.TurnLoop, in_=TURN_SCOPE),
        inj.bind(agn.TurnLoopRunner, in_=TURN_SCOPE),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),
    ])

    return inj.as_elements(*lst)
