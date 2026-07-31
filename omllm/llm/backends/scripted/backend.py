from omcore import check
from omcore import lang
from omcore.formats.json import all as json

from ....core.streams import StreamSink
from ....core.streams import new_stream
from ...types.backends import Backend
from ...types.backends import ImmediateBackend
from ...types.backends import StreamBackend
from ...types.content import TextContent
from ...types.content import ThinkingContent
from ...types.content import ToolCall
from ...types.context import Context
from ...types.messages import AiMessage
from ...types.models import Model
from ...types.options import Options
from ...types.streams import AiStream
from ...types.streams import AiStreamEvent
from ...types.streams import StreamEndAiStreamEvent
from ...types.streams import StreamStartAiStreamEvent
from ...types.streams import TextDeltaAiStreamEvent
from ...types.streams import TextEndAiStreamEvent
from ...types.streams import TextStartAiStreamEvent
from ...types.streams import ThinkingDeltaAiStreamEvent
from ...types.streams import ThinkingEndAiStreamEvent
from ...types.streams import ThinkingStartAiStreamEvent
from ...types.streams import ToolCallDeltaAiStreamEvent
from ...types.streams import ToolCallEndAiStreamEvent
from ...types.streams import ToolCallStartAiStreamEvent
from .scripts import BackendScript
from .scripts import BackendScriptCursor
from .scripts import BackendScriptGatePoint
from .scripts import BackendScriptInvocation
from .scripts import BackendScriptTurn
from .scripts import split_script_text


##


@lang.cached_function
def default_backend_script() -> BackendScript:
    return BackendScript(
        [
            BackendScriptTurn(AiMessage(
                [TextContent("Hello from the scripted backend's built-in offline response.")],
                stop_reason='stop',
            )),
        ],
        on_exhausted='restart',
    )


##


class _ScriptedBackendBase(Backend, lang.Abstract):
    def __init__(
            self,
            model: Model,
            script: BackendScript | None = None,
            *,
            cursor: BackendScriptCursor | None = None,
    ) -> None:
        super().__init__()

        check.arg(script is None or cursor is None)

        self._model = model

        if cursor is not None:
            self._cursor = cursor
            self._script = cursor.script
        else:
            self._script = script if script is not None else default_backend_script()
            self._cursor = BackendScriptCursor(self._script)

        self._invocations = 0

    @property
    def model(self) -> Model:
        return self._model

    @property
    def script(self) -> BackendScript:
        return self._script

    @property
    def invocations(self) -> int:
        return self._invocations

    def _next_turn(self, context: Context, options: Options | None) -> tuple[int, BackendScriptTurn]:
        turn = self._cursor.next_turn()

        invocation_index = self._invocations
        self._invocations += 1

        if (expect := turn.expect) is not None:
            expect(BackendScriptInvocation(
                invocation_index=invocation_index,
                context=context,
                options=options,
            ))

        return invocation_index, turn


##


class ScriptedImmediateBackend(_ScriptedBackendBase, ImmediateBackend):
    async def immediate(self, context: Context, options: Options | None = None) -> AiMessage:
        _, turn = self._next_turn(context, options)

        if (error := turn.error) is not None:
            raise error

        return check.not_none(turn.message)


##


def _build_stream_events(turn: BackendScriptTurn) -> list[AiStreamEvent]:
    message = check.not_none(turn.message)

    events: list[AiStreamEvent] = [StreamStartAiStreamEvent()]

    for content_index, content in enumerate(message.content):
        if isinstance(content, TextContent):
            events.append(TextStartAiStreamEvent(content_index=content_index))
            events.extend(
                TextDeltaAiStreamEvent(chunk, content_index=content_index)
                for chunk in split_script_text(content.text, turn.chunk_size)
            )
            events.append(TextEndAiStreamEvent(content.text, content_index=content_index))

        elif isinstance(content, ThinkingContent):
            events.append(ThinkingStartAiStreamEvent(content_index=content_index))
            events.extend(
                ThinkingDeltaAiStreamEvent(chunk, content_index=content_index)
                for chunk in split_script_text(content.text, turn.chunk_size)
            )
            events.append(ThinkingEndAiStreamEvent(content.text, content_index=content_index))

        elif isinstance(content, ToolCall):
            events.append(ToolCallStartAiStreamEvent(content_index=content_index))
            raw_args = json.dumps(content.args)
            events.extend(
                ToolCallDeltaAiStreamEvent(chunk, content_index=content_index)
                for chunk in split_script_text(raw_args, turn.chunk_size)
            )
            events.append(ToolCallEndAiStreamEvent(content, content_index=content_index))

        else:
            raise TypeError(content)

    events.append(StreamEndAiStreamEvent())
    return events


class ScriptedStreamBackend(_ScriptedBackendBase, StreamBackend):
    async def stream(self, context: Context, options: Options | None = None) -> AiStream:
        invocation_index, turn = self._next_turn(context, options)

        async def inner(sink: StreamSink[AiStreamEvent]) -> AiMessage:
            if (error := turn.error) is not None:
                raise error

            events = _build_stream_events(turn)
            gate = self._script.gate

            for emission_index, event in enumerate(events):
                if gate is not None:
                    await gate(BackendScriptGatePoint(
                        invocation_index=invocation_index,
                        emission_index=emission_index,
                    ))
                await sink.emit(event)

            if gate is not None:
                await gate(BackendScriptGatePoint(
                    invocation_index=invocation_index,
                    emission_index=len(events),
                ))

            return check.not_none(turn.message)

        return await new_stream(inner)
