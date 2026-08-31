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


_TURN_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._TURN_SCOPE_CONTEXT')

TURN_SCOPE: ta.Final = inj.DelimitedScope(context=inj.ContextVarScopeContext(_TURN_SCOPE_CONTEXT))


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
        inj.bind_scope_seed(float, TURN_SCOPE),
    ])

    #

    lst.extend([
        inj.bind(agn.TurnLoopRunner, singleton=True),
    ])

    #

    lst.extend([
        inj.bind(agn.Agent, singleton=True),
    ])

    return inj.as_elements(*lst)
