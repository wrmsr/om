import typing as ta

from ... import agent as agn
from ...core.eventbus import EventSubscriber


##


AgentEventSubscribers = ta.NewType('AgentEventSubscribers', ta.Sequence[EventSubscriber[agn.Event]])
