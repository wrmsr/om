import contextvars
import typing as ta

from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from ...core.eventbus import EventSubscriber
from .config import Config


##


AgentEventSubscribers = ta.NewType('AgentEventSubscribers', ta.Sequence[EventSubscriber[agn.Event]])


@lang.cached_function
def agent_event_subscribers() -> inj.ItemsBinderHelper[EventSubscriber[agn.Event]]:
    return inj.items_binder_helper[EventSubscriber[agn.Event]](AgentEventSubscribers)


class HasOnEventAgent(ta.Protocol):
    def on_agent_event(self, ev: agn.Event) -> ta.Awaitable[None]: ...


def bind_on_agent_event_subscriber(cls: type[HasOnEventAgent]) -> inj.Elements:
    return agent_event_subscribers().bind_item(to_fn=inj.target(o=cls)(lambda o: o.on_agent_event))


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

        inj.bind(agn.TurnLoop, in_=TURN_SCOPE),
        inj.bind(agn.TurnLoopRunner, in_=TURN_SCOPE),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),
    ])

    return inj.as_elements(*lst)
