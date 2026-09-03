import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite.sleeps import AsyncliteSleeps

from ... import llm
from ...core.errors import is_cancelled_error
from ...core.eventbus import EventSubscriber
from ..types.contexts import Context
from ..types.errors import ErrorStopReasonError
from ..types.errors import UnknownToolError
from ..types.events import AgentEndEvent
from ..types.events import AgentStartEvent
from ..types.events import Event
from ..types.events import LlmAiStreamEvent
from ..types.events import LlmRetryEvent
from ..types.events import ToolExecutionEndEvent
from ..types.events import ToolExecutionStartEvent
from ..types.events import TurnEndEvent
from ..types.events import TurnStartEvent
from ..types.messages import InfoAgentMessage
from ..types.messages import Message
from ..types.tools import ToolContext
from ..types.tools import ToolEnvironment
from ..types.tools import ToolResult
from ..types.turns import AgentEndReason
from ..types.turns import TurnConfig
from ..types.turns import TurnResult


##


class TurnLoop:
    """
    Runs one prompt: LLM calls and the tool calls they make, around again until the model ends its turn or a limit is
    reached.

    Sans-io: nothing here depends on asyncio being loaded, and the one concurrency primitive used - the sleeper for
    retry backoff - is handed in. Every outcome the loop decides for itself, a failure included, is returned as a
    TurnResult and published as an AgentEndEvent; only the run's own cancellation (or a non-Exception BaseException)
    propagates, and it does so after that same terminal publish.

    Whatever the outcome, the transcript left behind is one the next request can be built on: every tool call in the
    last AI message has a result, synthesized as an error wherever the call was never executed, and an interrupted run
    is noted with an InfoAgentMessage.
    """

    def __init__(
            self,
            *,
            new_messages: ta.Sequence[Message],
            config: TurnConfig | None = None,
            context: Context | None = None,
            subscriber: EventSubscriber[Event] | None = None,
            llm_backend: llm.ImmediateBackend,
            tool_env: ToolEnvironment | None = None,
            sleeps: AsyncliteSleeps | None = None,
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
        if config.llm_retry is not None:
            check.state(sleeps is not None, 'Retries need a sleeper for their backoff')
        self._sleeps = sleeps

        #

        self._config = config
        self._context = context

        self._new_messages: list[Message] = []

        self._num_turns = 0
        self._num_llm_content_events = 0

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

    def _unexecuted_tool_calls(self) -> list[llm.ToolCall]:
        """
        The tool calls of the latest AI message which have no result following them, if that message is this run's.
        """

        result_ids: set[str] = set()

        for m in reversed(self._context.messages or []):
            if isinstance(m, llm.ToolResultMessage):
                result_ids.add(m.tool_call_id)

            elif isinstance(m, llm.AiMessage):
                return [c for c in m.content if isinstance(c, llm.ToolCall) and c.id not in result_ids]

            elif isinstance(m, llm.UserMessage):
                # Back at this run's prompt without an AI message: nothing of this run's to repair, and an earlier
                # run's messages are not to be touched.
                return []

            # Agent messages are transparent.

        return []

    def _add_unexecuted_tool_call_results(self, why: str) -> None:
        """
        Gives every unexecuted tool call of the latest AI message an error result saying it was not executed and why.
        A call without a result is a transcript providers reject on the next request, so the loop never leaves one
        behind, however the run ended.
        """

        for tc in self._unexecuted_tool_calls():
            self._add_new_message(llm.ToolResultMessage(
                tool_call_id=tc.id,
                tool_name=tc.name,
                content=(llm.TextContent(f'Tool call was not executed: {why}.'),),
                is_error=True,
            ))

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

    async def _llm_complete_once(self) -> llm.AiMessage:
        llm_context = self._build_llm_context()

        if isinstance(llm_backend := self._llm_backend, llm.StreamBackend):
            async with (await llm_backend.stream(
                    llm_context,
                    self._config.llm_options,
            )) as it:
                async for e in it:
                    if isinstance(e, llm.ContentAiStreamEvent):
                        self._num_llm_content_events += 1
                    await self._publish(LlmAiStreamEvent(e))
                return it.result.must()

        else:
            return await self._llm_backend.immediate(
                llm_context,
                self._config.llm_options,
            )

    async def _llm_complete(self) -> llm.AiMessage:
        retry = self._config.llm_retry
        attempts = 0

        while True:
            attempts += 1
            self._num_llm_content_events = 0

            try:
                return await self._llm_complete_once()

            except llm.TransientBackendError as e:
                if retry is None or attempts > retry.max_retries:
                    raise

                if self._num_llm_content_events:
                    # Content from the failed attempt has already reached subscribers. A retry would produce a second,
                    # different response on top of it, so the failure stands.
                    raise

                delay_s = retry.delay_s(attempts, retry_after_s=e.retry_after_s)

                await self._publish(LlmRetryEvent(
                    attempts=attempts,
                    delay_s=delay_s,
                    error=e,
                ))

                await check.not_none(self._sleeps).sleep(delay_s)

    #

    async def _execute_tool_call(self, tool_call: llm.ToolCall) -> None:
        tool = self._context.tools.by_name.get(tool_call.name) if self._context.tools is not None else None

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

        tool_result: ToolResult

        if tool is None:
            tool_result = ToolResult(
                content=llm.TextContent(f'Unknown tool: {tool_call.name!r}'),
                error=UnknownToolError(tool_call.name),
            )

        else:
            # Any Exception out of an executor is an error result for the model to see and recover from. Tool classes
            # do this for themselves; this is the backstop for bare executors. Cancellation is a BaseException, and
            # propagates.
            try:
                tool_result = await tool.executor(tool_context)
            except Exception as e:  # noqa: BLE001
                tool_result = ToolResult.of_error(e)

        await self._publish(ToolExecutionEndEvent(
            tool=tool,
            context=tool_context,
            result=tool_result,
        ))

        self._add_new_message(llm.ToolResultMessage(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,

            content=(tool_result.content,),

            is_error=tool_result.error is not None,
        ))

    #

    async def _turn(self) -> AgentEndReason | None:
        """One LLM call and the tool calls it makes. None means the loop goes around again."""

        self._num_turns += 1

        await self._publish(TurnStartEvent())

        message = await self._llm_complete()

        self._add_new_message(message)

        tool_calls = [c for c in message.content if isinstance(c, llm.ToolCall)]

        end_reason: AgentEndReason | None

        if message.stop_reason == 'error':
            # A refusal or a content filter. The message is kept, as it may carry an explanation, but the run fails:
            # the model did not produce what was asked for, and going around again would only ask again.
            await self._publish(TurnEndEvent(
                message=message,
            ))

            raise ErrorStopReasonError(message)

        elif message.stop_reason == 'length':
            # A truncated message's tool calls are not to be trusted: their arguments may have been cut off mid-way.
            self._add_unexecuted_tool_call_results('the output was cut off by the token limit')

            end_reason = AgentEndReason.LENGTH

        elif not tool_calls:
            # Tool calls are executed on their presence, not on the stop reason: a provider reporting a plain stop
            # alongside calls still expects their results on the next request.
            end_reason = AgentEndReason.COMPLETED

        elif (max_turns := self._config.max_turns) is not None and self._num_turns >= max_turns:
            self._add_unexecuted_tool_call_results('the turn limit was reached')

            end_reason = AgentEndReason.MAX_TURNS

        else:
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

            end_reason = None

        await self._publish(TurnEndEvent(
            message=message,
        ))

        return end_reason

    #

    def _note_interruption(self, reason: AgentEndReason, error: BaseException) -> None:
        """
        Deliberately synchronous: this runs on the cancellation path, where an await would widen the window in which a
        second cancellation could land.
        """

        if reason is AgentEndReason.CANCELLED:
            self._add_unexecuted_tool_call_results('the turn was cancelled')
            self._add_new_message(InfoAgentMessage('Turn cancelled.'))

        else:
            self._add_unexecuted_tool_call_results('the turn failed')
            self._add_new_message(InfoAgentMessage(f'Turn failed: {error!r}'))

    async def run(self) -> TurnResult:
        end_reason: AgentEndReason | None = None
        end_error: BaseException | None = None

        try:
            await self._publish(AgentStartEvent())

            while True:
                if (end_reason := await self._turn()) is not None:
                    break

        except Exception as e:  # noqa: BLE001
            # The loop's own failures are outcomes, not exceptions: recorded on the result and the terminal event, with
            # the transcript up to them kept.
            end_reason = AgentEndReason.FAILED
            end_error = e

        except BaseException as e:
            # FIXME: cancellation classification is coarse. `is_cancelled_error` answers "is this a cancellation
            # error", not "was this task cancelled": a CancelledError raised because *something else* cancelled a
            # future this task was awaiting (a frontend withdrawing a permission ask, a tool cancelling its own
            # awaitable) is indistinguishable here from the user cancelling the turn. It is reported CANCELLED, and
            # re-raised as such into a task which was never cancelled. The precise test is asyncio-specific -
            # `asyncio.current_task().cancelling() > 0` - and this layer must stay usable without asyncio loaded at
            # all, so it is not done here. The consequence is pushed to the edges: askers must never inject a bare
            # cancellation into a live turn (see the PermissionAsker contract; minitui's CardPermissionAsker converts a
            # withdrawn ask into PermissionAskAbortedError when its own task was not cancelled).
            if not is_cancelled_error(e):
                # Not the loop's to report: a KeyboardInterrupt or SystemExit passes straight through, terminal event
                # and all.
                raise

            # Cancellation is reported like any other outcome, but must still unwind through the caller's task.
            end_reason = AgentEndReason.CANCELLED
            end_error = e
            raise

        finally:
            if end_reason is not None:
                if end_error is not None:
                    self._note_interruption(end_reason, end_error)

                # FIXME: this terminal publish is not atomic under cancellation. If a cancellation lands while a
                # subscriber is suspended inside it, the CancelledError is thrown into that subscriber and every
                # subscriber after it never sees the AgentEndEvent: a frontend can be left mid-turn forever, and a
                # completed run can be half-recorded (Session has stored it, then the task unwinds before Agent.prompt
                # applies it to state). The fix is to shield the publish so a cancellation arriving during it is
                # deferred until every subscriber has run and then re-raised - `omcore.asyncs.asyncio.shielded_finally`
                # does exactly this - but it is asyncio-specific and this layer must not depend on asyncio. Until a
                # sans-io equivalent exists:
                #  - A subscriber that may suspend (storage, network) widens the window for every subscriber behind it.
                #    The harness Session subscribes at construction, ahead of UI subscribers, and its JSONL storage
                #    does synchronous file IO, so today the window is nil - keep it that way, or reorder.
                #  - Frontends must backstop a lost terminal event. minitui's PromptPump closes the surface's turn from
                #    the prompt task's done callback if the renderer never saw the end event.
                #  - Agent.prompt captures this event ahead of forwarding it, so its state is applied even when the
                #    cancellation lands in a later subscriber.
                await self._publish(AgentEndEvent(
                    context=self._context,

                    new_messages=tuple(self._new_messages),

                    reason=end_reason,
                    error=end_error,
                ))

        return TurnResult(
            config=self._config,
            context=self._context,

            new_messages=tuple(self._new_messages),

            reason=check.not_none(end_reason),
            error=end_error,
        )
