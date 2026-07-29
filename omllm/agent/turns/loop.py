from omcore import check
from omcore import dataclasses as dc

from ... import llm
from ..types.contexts import Context
from ..types.events import AgentEndEvent
from ..types.events import AgentStartEvent
from ..types.events import Event
from ..types.events import EventSink
from ..types.events import LlmAiStreamEvent
from ..types.events import TurnEndEvent
from ..types.events import TurnStartEvent
from ..types.messages import Message
from ..types.tools import ToolContext
from ..types.tools import ToolEnvironment
from ..types.turns import TurnConfig
from ..types.turns import TurnResult


##


class TurnLoop:
    def __init__(
            self,
            *,
            config: TurnConfig | None = None,
            context: Context | None = None,
            sink: EventSink | None = None,
            llm_backend: llm.ImmediateBackend,
            tool_env: ToolEnvironment | None = None,
    ) -> None:
        super().__init__()

        if config is None:
            config = TurnConfig()
        self._initial_config = config
        if context is None:
            context = Context()
        self._initial_context = context
        self._sink = sink
        self._llm_backend = llm_backend
        self._tool_env = tool_env

        #

        self._config = config
        self._context = context

        self._new_messages: list[Message] = []

    #

    def _add_new_message(self, *messages: Message) -> None:
        self._context = dc.replace(
            self._context,

            messages=[*(self._context.messages or []), *messages],
        )

        self._new_messages.extend(messages)

    #

    async def _emit(self, event: Event) -> None:
        if (sink := self._sink) is not None:
            await sink(event)

    #

    async def _llm_complete(self) -> llm.AiMessage:
        llm_context = llm.Context(
            system_prompt=self._context.system_prompt,

            messages=[  # noqa
                m
                for m in self._context.messages
            ] if self._context.messages is not None else None,

            tools=[
                t.llm_tool
                for t in self._context.tools
            ] if self._context.tools else None,
        )

        if isinstance(llm_backend := self._llm_backend, llm.StreamBackend):
            async with (await llm_backend.stream(
                    llm_context,
                    self._config.llm_options,
            )) as it:
                async for e in it:
                    await self._emit(LlmAiStreamEvent(e))
                return it.result.must()

        else:
            return await self._llm_backend.immediate(
                llm_context,
                self._config.llm_options,
            )

    #

    @dc.dataclass(frozen=True, kw_only=True)
    class _TurnResult:
        should_continue: bool

    async def _turn(self) -> _TurnResult:
        await self._emit(TurnStartEvent())

        message = await self._llm_complete()  # noqa

        self._add_new_message(message)

        if message.stop_reason is not None and message.stop_reason != 'tool_use':
            await self._emit(TurnEndEvent(
                message=message,
            ))

            return self._TurnResult(
                should_continue=False,
            )

        tool_calls = [c for c in message.content if isinstance(c, llm.ToolCall)]
        if tool_calls:
            for tool_call in tool_calls:
                tool = check.not_none(self._context.tools)[tool_call.name]

                tool_result = await tool.executor(ToolContext(  # noqa
                    args=tool_call.args,

                    llm_tool_call=tool_call,

                    env=self._tool_env,
                ))

                tool_result_message = llm.ToolResultMessage(
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,

                    content=(tool_result.content,),
                )

                self._add_new_message(tool_result_message)

        await self._emit(TurnEndEvent(
            message=message,
        ))

        return self._TurnResult(
            should_continue=bool(tool_calls),
        )

    #

    async def run(self) -> TurnResult:
        await self._emit(AgentStartEvent())

        while True:
            turn_result = await self._turn()

            if not turn_result.should_continue:
                break

        await self._emit(AgentEndEvent(
            context=self._context,

            new_messages=self._new_messages,
        ))

        return TurnResult(
            config=self._config,
            context=self._context,

            new_messages=self._new_messages,
        )
