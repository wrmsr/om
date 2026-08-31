import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ... import llm
from ...core.eventbus import EventSubscriber
from ..types.contexts import Context
from ..types.events import AgentEndEvent
from ..types.events import AgentStartEvent
from ..types.events import Event
from ..types.events import LlmAiStreamEvent
from ..types.events import ToolExecutionEndEvent
from ..types.events import ToolExecutionStartEvent
from ..types.events import TurnEndEvent
from ..types.events import TurnStartEvent
from ..types.messages import Message
from ..types.states import State
from ..types.tools import ToolContext
from ..types.tools import ToolEnvironment
from ..types.turns import TurnConfig
from ..types.turns import TurnResult
from ..types.turns import TurnRunner


if ta.TYPE_CHECKING:
    from ..backends import BackendManager


##


class TurnLoop:
    def __init__(
            self,
            *,
            new_messages: ta.Sequence[Message],
            config: TurnConfig | None = None,
            context: Context | None = None,
            subscriber: EventSubscriber[Event] | None = None,
            llm_backend: llm.ImmediateBackend,
            tool_env: ToolEnvironment | None = None,
    ) -> None:
        super().__init__()

        self._initial_new_messages = list(new_messages)
        if config is None:
            config = TurnConfig()
        self._initial_config = config
        if context is None:
            context = Context()
        self._initial_context = context
        self._subscriber = subscriber
        self._llm_backend = llm_backend
        self._tool_env = tool_env

        #

        self._config = config
        self._context = context

        self._new_messages: list[Message] = []

        self._add_new_message(*new_messages)

    #

    def _add_new_message(self, *messages: Message) -> None:
        self._context = dc.replace(
            self._context,

            messages=[
                *(self._context.messages or []),
                *messages,
            ],
        )

        self._new_messages.extend(messages)

    #

    async def _publish(self, *events: Event) -> None:
        if (subs := self._subscriber) is not None:
            for e in events:
                if (aw := subs(e)) is not None:
                    await aw

    #

    def _build_llm_context(self) -> llm.Context:
        return llm.Context(
            system_prompt=self._context.system_prompt,

            messages=[  # noqa
                m
                for m in self._context.messages
                if isinstance(m, llm.Message)
            ] if self._context.messages is not None else None,

            tools=[
                t.llm_tool
                for t in self._context.tools
            ] if self._context.tools else None,
        )

    async def _llm_complete(self) -> llm.AiMessage:
        llm_context = self._build_llm_context()

        if isinstance(llm_backend := self._llm_backend, llm.StreamBackend):
            async with (await llm_backend.stream(
                    llm_context,
                    self._config.llm_options,
            )) as it:
                async for e in it:
                    await self._publish(LlmAiStreamEvent(e))
                return it.result.must()

        else:
            return await self._llm_backend.immediate(
                llm_context,
                self._config.llm_options,
            )

    #

    async def _execute_tool_call(self, tool_call: llm.ToolCall) -> None:
        tool = check.not_none(self._context.tools)[tool_call.name]

        tool_context = ToolContext(  # noqa
            tool=tool,

            args=tool_call.args,

            llm_tool_call=tool_call,

            env=self._tool_env,
        )

        await self._publish(ToolExecutionStartEvent(
            tool=tool,
            context=tool_context,
        ))

        tool_result = await tool.executor(tool_context)

        await self._publish(ToolExecutionEndEvent(
            tool=tool,
            context=tool_context,
            result=tool_result,
        ))

        tool_result_message = llm.ToolResultMessage(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,

            content=(tool_result.content,),
        )

        self._add_new_message(tool_result_message)

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _TurnResult:
        should_continue: bool

    async def _turn(self) -> _TurnResult:
        await self._publish(TurnStartEvent())

        message = await self._llm_complete()  # noqa

        self._add_new_message(message)

        if message.stop_reason is not None and message.stop_reason != 'tool_use':
            await self._publish(TurnEndEvent(
                message=message,
            ))

            return self._TurnResult(
                should_continue=False,
            )

        tool_calls = [c for c in message.content if isinstance(c, llm.ToolCall)]
        if tool_calls:
            for tool_call in tool_calls:
                await self._execute_tool_call(tool_call)

        await self._publish(TurnEndEvent(
            message=message,
        ))

        return self._TurnResult(
            should_continue=bool(tool_calls),
        )

    #

    async def run(self) -> TurnResult:
        await self._publish(AgentStartEvent())

        while True:
            turn_result = await self._turn()

            if not turn_result.should_continue:
                break

        await self._publish(AgentEndEvent(
            context=self._context,

            new_messages=self._new_messages,
        ))

        return TurnResult(
            config=self._config,
            context=self._context,

            new_messages=self._new_messages,
        )


##


class TurnLoopRunner(TurnRunner):
    def __init__(
            self,
            *,
            backends: BackendManager,
    ) -> None:
        super().__init__()

        self._backends = backends

    async def run_turn(
            self,
            state: State,
            new_messages: ta.Sequence[Message],
            *,
            subscriber: EventSubscriber[Event] | None = None,
    ) -> TurnResult:
        llm_backend = self._backends.get_backend(llm.ImmediateBackend, state.model)  # type: ignore[type-abstract]

        loop = TurnLoop(
            new_messages=new_messages,
            config=state.turn_config,
            context=state.context,
            subscriber=subscriber,
            llm_backend=llm_backend,
            tool_env=state.tool_env,
        )

        return await loop.run()
