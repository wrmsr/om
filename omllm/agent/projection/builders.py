import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ... import llm
from ..types.contexts import Context
from ..types.messages import AgentMessage
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

    @staticmethod
    def _project_tool_result(message: llm.ToolResultMessage, *, max_chars: int) -> llm.ToolResultMessage:
        text = '\n\n'.join(content.text for content in message.content)

        if max_chars == 0:
            projected = (
                f'[Earlier {message.tool_name} result pruned: {len(text)} characters. '
                'Run the tool again if exact output is needed.]'
            )

        elif len(text) <= max_chars:
            return message

        else:
            marker = f'\n\n[... result truncated from {len(text)} characters ...]\n\n'
            if len(marker) >= max_chars:
                projected = marker[:max_chars]
            else:
                remaining = max_chars - len(marker)
                head = (remaining * 2) // 3
                tail = remaining - head
                projected = text[:head] + marker + text[-tail:]

        return dc.replace(message, content=(llm.TextContent(projected),))

    def _project_messages(self, context: Context) -> list[llm.Message]:
        messages = context.messages or ()
        projection = context.projection
        check.arg(projection.first_kept_message_index <= len(messages))

        tool_results = projection.tool_results_by_message_index
        out: list[llm.Message] = []

        if projection.summary is not None:
            out.append(llm.UserMessage(f'Earlier conversation summary:\n\n{projection.summary}'))

        for index, m in enumerate(messages):
            if index < projection.first_kept_message_index:
                continue

            if isinstance(m, llm.Message):
                if isinstance(m, llm.ToolResultMessage) and (p := tool_results.get(index)) is not None:
                    m = self._project_tool_result(m, max_chars=p.max_chars)
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
            messages = self._merge_adjacent_user_messages(self._project_messages(context))

        return llm.Context(
            system_prompt=context.system_prompt,

            messages=messages,

            tools=[
                t.llm_tool
                for t in context.tools
            ] if context.tools else None,
        )
