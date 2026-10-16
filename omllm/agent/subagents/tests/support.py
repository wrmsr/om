"""
Test support for the subagent layer, offline: a parent agent and a hand-built child runner, each on a scripted model of
its own, so what the parent says and what the child says are scripted independently.
"""
import asyncio
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...agent import Agent
from ...backends import DictBackendManager
from ...permissions.deciders import StaticPermissionDecider
from ...permissions.types import PermissionDecider
from ...permissions.types import PermissionState
from ...tests.scripted import scripted_backend
from ...tests.tools import bare_tool
from ...turns.runner import TurnLoopRunner
from ...types.contexts import Context
from ...types.events import Event
from ...types.events import StateUpdateEvent
from ...types.events import ToolExecutionUpdateEvent
from ...types.messages import Message
from ...types.tools import Tool
from ...types.tools import ToolEnvironment
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ..profiles import GENERAL_SUBAGENT_PROFILE
from ..profiles import SubagentProfiles
from ..progress import SubagentEventToolProgressUpdate
from ..runners import AgentSubagentRunner
from ..tools.subagent import SubagentTool


##


def turn_loop_runner(*turns: ta.Any) -> TurnLoopRunner:
    return TurnLoopRunner(
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        backends=DictBackendManager.of(scripted_backend(*turns)),
    )


def child_runner(
        *turns: ta.Any,
        tools: ta.Sequence[Tool] = (),
        **kwargs: ta.Any,
) -> AgentSubagentRunner:
    return AgentSubagentRunner(
        turn_runner=turn_loop_runner(*turns),
        tools=ToolSet(list(tools)),
        **kwargs,
    )


def subagent_tool(
        runner: AgentSubagentRunner,
        *,
        profiles: SubagentProfiles | None = None,
        permissions: PermissionDecider | None = None,
) -> SubagentTool:
    return SubagentTool(
        permissions=permissions if permissions is not None else StaticPermissionDecider(PermissionState.ALLOW),
        runner=runner,
        profiles=profiles if profiles is not None else SubagentProfiles([GENERAL_SUBAGENT_PROFILE]),
    )


async def parent_agent(
        *turns: ta.Any,
        tools: ta.Sequence[Tool],
        env: ToolEnvironment | None = None,
) -> Agent:
    agent = Agent(turn_runner=turn_loop_runner(*turns))

    await agent.update_state(lambda s: dc.replace(
        s,
        context=Context(tools=ToolSet(list(tools))),
        tool_env=env,
    ))

    return agent


##


def subagent_call(
        id: str,  # noqa
        prompt: str,
        *,
        profile: str | None = None,
        description: str | None = None,
) -> llm.ToolCall:
    args: dict[str, ta.Any] = {'prompt': prompt}
    if profile is not None:
        args['profile'] = profile
    if description is not None:
        args['description'] = description
    return llm.ToolCall(id, SubagentTool.name, args)


def tool_results(messages: ta.Sequence[Message]) -> list[llm.ToolResultMessage]:
    return [m for m in messages if isinstance(m, llm.ToolResultMessage)]


def ai_text(message: Message) -> str:
    return '\n'.join(c.text for c in check.isinstance(message, llm.AiMessage).content if isinstance(c, llm.TextContent))


def relayed_updates(events: ta.Sequence[Event]) -> list[SubagentEventToolProgressUpdate]:
    return [
        e.update
        for e in events
        if isinstance(e, ToolExecutionUpdateEvent) and isinstance(e.update, SubagentEventToolProgressUpdate)
    ]


def relayed_events(events: ta.Sequence[Event]) -> list[Event]:
    """The child's run events, as relayed: its state updates (its setup, its run's application) are left out."""

    return [u.event for u in relayed_updates(events) if not isinstance(u.event, StateUpdateEvent)]


##


class GatedTool:
    """An executor which waits to be released, recording what it sees on the way out."""

    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.seen: list = []

    async def __call__(self, ctx):
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.seen.append(('cancelled', check.not_none(asyncio.current_task()).cancelling() > 0))
            raise
        self.seen.append('done')
        return ToolResult(content=llm.TextContent(f'ran {self.name}'))

    def tool(self) -> Tool:
        return bare_tool(self.name, self)


class EnvRecordingTool:
    """An executor which records the environment each call ran in."""

    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name
        self.envs: list[ToolEnvironment | None] = []

    async def __call__(self, ctx):
        self.envs.append(ctx.env)
        return ToolResult(content=llm.TextContent(f'ran {self.name}'))

    def tool(self) -> Tool:
        return bare_tool(self.name, self)
