import abc
import typing as ta

from omcore import lang

from ... import llm
from ..types.contexts import Context
from ..types.messages import AgentMessage


##


class AgentMessageProjector(lang.Abstract):
    """Projects an agent message into what, if anything, the model sees of it. Nothing back means invisible."""

    @abc.abstractmethod
    def project(self, message: AgentMessage) -> ta.Sequence[llm.Message]:
        raise NotImplementedError


class LlmContextBuilder(lang.Abstract):
    """
    Builds the model's view of the transcript for one call. Pure: it changes nothing about the transcript itself, so
    it may trim, restate, or omit freely - the full record stays where it is.
    """

    @abc.abstractmethod
    def build(self, context: Context) -> llm.Context:
        raise NotImplementedError
