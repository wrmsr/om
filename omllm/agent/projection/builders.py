import typing as ta

from ... import llm
from ..types.contexts import Context
from ..types.messages import AgentMessage
from ..types.messages import Message
from .messages import TypeMapAgentMessageProjector
from .types import AgentMessageProjector
from .types import LlmContextBuilder


##


def _user_text(m: llm.UserMessage) -> str:
    return m.content if isinstance(m.content, str) else m.content.text


class StandardLlmContextBuilder(LlmContextBuilder):
    def __init__(
            self,
            *,
            projector: AgentMessageProjector | None = None,
    ) -> None:
        super().__init__()

        if projector is None:
            projector = TypeMapAgentMessageProjector()
        self._projector = projector

    def _project_messages(self, messages: ta.Sequence[Message]) -> list[llm.Message]:
        out: list[llm.Message] = []

        for m in messages:
            if isinstance(m, llm.Message):
                out.append(m)
            elif isinstance(m, AgentMessage):
                out.extend(self._projector.project(m))
            else:
                raise TypeError(m)

        return out

    def _merge_adjacent_user_messages(self, messages: ta.Sequence[llm.Message]) -> list[llm.Message]:
        # A projected note often lands right next to a real prompt, and providers differ in how they take two user
        # turns in a row. One merged turn reads the same everywhere.
        out: list[llm.Message] = []

        for m in messages:
            if isinstance(m, llm.UserMessage) and out and isinstance(prev := out[-1], llm.UserMessage):
                out[-1] = llm.UserMessage('\n\n'.join([_user_text(prev), _user_text(m)]))
            else:
                out.append(m)

        return out

    def build(self, context: Context) -> llm.Context:
        messages: list[llm.Message] | None = None
        if context.messages is not None:
            messages = self._merge_adjacent_user_messages(self._project_messages(context.messages))

        return llm.Context(
            system_prompt=context.system_prompt,

            messages=messages,

            tools=[
                t.llm_tool
                for t in context.tools
            ] if context.tools else None,
        )
