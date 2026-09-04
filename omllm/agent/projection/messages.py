import typing as ta

from ... import llm
from ..types.messages import AgentMessage
from .types import AgentMessageProjector


##


class TypeMapAgentMessageProjector(AgentMessageProjector):
    """
    Dispatches on the message's type, nearest class first, and leaves anything unmapped invisible. The mapping is the
    one place to teach the model about a new kind of agent message.
    """

    def __init__(
            self,
            projectors: ta.Mapping[type[AgentMessage], AgentMessageProjector] | None = None,
    ) -> None:
        super().__init__()

        self._projectors = dict(projectors) if projectors is not None else {}

    def project(self, message: AgentMessage) -> ta.Sequence[llm.Message]:
        for cls in type(message).__mro__:
            if (p := self._projectors.get(cls)) is not None:
                return p.project(message)

        return ()
