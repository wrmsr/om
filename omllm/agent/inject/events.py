import typing as ta

from omcore import inject as inj
from omcore import lang

from ... import agent as agn


##


@lang.cached_function
def event_subscribers_binder() -> inj.ItemsBinderHelper[agn.EventSubscriber]:
    return inj.items_binder_helper[agn.EventSubscriber](agn.EventSubscribers)


#


class HasOnAgentEvent(ta.Protocol):
    def on_agent_event(self, ev: agn.Event) -> ta.Awaitable[None]: ...


def bind_on_agent_event_subscriber(cls: type[HasOnAgentEvent]) -> inj.Elements:
    return event_subscribers_binder().bind_item(to_fn=inj.target(o=cls)(lambda o: o.on_agent_event))


##


def bind_events() -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        event_subscribers_binder().bind_items_provider(singleton=True),
    ])

    #

    return inj.as_elements(*lst)
