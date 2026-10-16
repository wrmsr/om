"""What is the same for every way of standing a subagent up: it is prompted once, and what it said is shaped."""
import typing as ta

from ... import llm
from ..agent import Agent
from ..types.messages import Message
from ..types.turns import TurnResult
from .types import SubagentRunId
from .types import SubagentRunResult


##


def subagent_process_scope_name(run_id: SubagentRunId) -> str:
    return f'subagent-{run_id.v}'


##


def final_subagent_text(messages: ta.Sequence[Message]) -> str:
    """The text of the last AI message, or empty where there was none."""

    for m in reversed(messages):
        if isinstance(m, llm.AiMessage):
            return '\n'.join(c.text for c in m.content if isinstance(c, llm.TextContent))

    return ''


def build_subagent_run_result(run_id: SubagentRunId, result: TurnResult) -> SubagentRunResult:
    return SubagentRunResult(
        run_id=run_id,
        text=final_subagent_text(result.new_messages),
        reason=result.reason,
        error=result.error,
        usage=result.context.usage,
        num_turns=sum(1 for m in result.new_messages if isinstance(m, llm.AiMessage)),
        messages=result.new_messages,
    )


async def drive_subagent(
        agent: Agent,
        *,
        run_id: SubagentRunId,
        prompt: str,
) -> SubagentRunResult:
    """
    Runs the one prompt a subagent gets, on an agent set up for it with its subscribers in place. Raises only on the
    caller's own cancellation, like the prompt itself.
    """

    return build_subagent_run_result(run_id, await agent.prompt(prompt))
