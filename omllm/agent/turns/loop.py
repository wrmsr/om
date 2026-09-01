import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ... import llm
from ...core.errors import is_cancelled_error
from ...core.eventbus import EventSubscriber
from ..types.contexts import Context
from ..types.events import AgentEndEvent
from ..types.events import AgentEndReason
from ..types.events import AgentStartEvent
from ..types.events import Event
from ..types.events import LlmAiStreamEvent
from ..types.events import ToolExecutionEndEvent
from ..types.events import ToolExecutionStartEvent
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
            # FIXME: parallel tool calls. When these run concurrently, cancellation semantics must hold for the group,
            # not per call:
            #  - A failing sibling must cancel the others *before* control reaches `run`'s terminal publish, so their
            #    pending permission asks unwind inside their own tasks as genuine cancellations. Otherwise those asks
            #    are still parked when frontends receive the AgentEndEvent and the frontend has to withdraw them, which
            #    (per the PermissionAsker contract) surfaces to a still-live tool as PermissionAskAbortedError - and a
            #    detached tool then runs to completion, publishing ToolExecution*Events into a turn that has ended
            #    (minitui's renderer drops such stragglers; other frontends may not).
            #  - A cancellation of the loop itself must reach every child before the terminal publish, for the same
            #    reason.
            #  - Tool result messages must still be appended in tool-call order regardless of completion order;
            #    frontends already finalize cards in that order.
            # This layer is sans-io and must stay usable with asyncio absent from sys.modules: no TaskGroup / gather
            # here. The concurrency primitive is to be decided, and is explicitly *not* an injectable sync/async
            # abstraction for now.
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
        end_reason = AgentEndReason.COMPLETED
        end_error: BaseException | None = None

        try:
            await self._publish(AgentStartEvent())

            while True:
                turn_result = await self._turn()

                if not turn_result.should_continue:
                    break

        except BaseException as e:
            end_error = e
            raise

        finally:
            if end_error is not None:
                # FIXME: cancellation classification is coarse. `is_cancelled_error` answers "is this a cancellation
                # error", not "was this task cancelled": a CancelledError raised because *something else* cancelled a
                # future this task was awaiting (a frontend withdrawing a permission ask, a tool cancelling its own
                # awaitable) is indistinguishable here from the user cancelling the turn. It is reported CANCELLED, and
                # everything gating on that reason then drops the turn's messages (Session storage, Agent.prompt's state
                # update). The precise test is asyncio-specific - `asyncio.current_task().cancelling() > 0` - and this
                # layer must stay usable without asyncio loaded at all, so it is not done here. The consequence is
                # pushed to the edges: askers must never inject a bare cancellation into a live turn (see the
                # PermissionAsker contract; minitui's CardPermissionAsker converts a withdrawn ask into
                # PermissionAskAbortedError when its own task was not cancelled).
                if is_cancelled_error(end_error):
                    end_reason = AgentEndReason.CANCELLED
                elif isinstance(end_error, Exception):
                    end_reason = AgentEndReason.FAILED
                else:
                    raise  # noqa

            # FIXME: this terminal publish is not atomic under cancellation. If a cancellation lands while a subscriber
            # is suspended inside it, the CancelledError is thrown into that subscriber and every subscriber after it
            # never sees the AgentEndEvent: a frontend can be left mid-turn forever, and a COMPLETED turn can be
            # half-recorded (Session has stored it, then the task unwinds before Agent.prompt applies it to state). The
            # fix is to shield the publish so a cancellation arriving during it is deferred until every subscriber has
            # run and then re-raised - `omcore.asyncs.asyncio.shielded_finally` does exactly this - but it is
            # asyncio-specific and this layer must not depend on asyncio. Until a sans-io equivalent exists:
            #  - A subscriber that may suspend (storage, network) widens the window for every subscriber behind it. The
            #    harness Session subscribes at construction, ahead of UI subscribers, and its JSONL storage does
            #    synchronous file IO, so today the window is nil - keep it that way, or reorder.
            #  - Frontends must backstop a lost terminal event. minitui's PromptPump closes the surface's turn from the
            #    prompt task's done callback if the renderer never saw the end event.
            await self._publish(AgentEndEvent(
                context=self._context,

                new_messages=self._new_messages,

                reason=end_reason,
                error=end_error,
            ))

        return TurnResult(
            config=self._config,
            context=self._context,

            new_messages=self._new_messages,
        )
