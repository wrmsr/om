import pytest

from omcore import check
from omcore import lang

from ....types.backends import StreamBackend
from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.messages import AiMessage
from ....types.messages import UserMessage
from ....types.models import Model
from ....types.models import ModelKey
from ....types.options import Options
from ....types.streams import StreamEndAiStreamEvent
from ....types.streams import StreamStartAiStreamEvent
from ....types.streams import TextDeltaAiStreamEvent
from ....types.streams import ThinkingDeltaAiStreamEvent
from ....types.streams import ToolCallDeltaAiStreamEvent
from ..backend import ScriptedImmediateBackend
from ..backend import ScriptedStreamBackend
from ..scripts import BackendScript
from ..scripts import BackendScriptCursor
from ..scripts import BackendScriptExhaustedError
from ..scripts import BackendScriptTurn


def _model():
    return Model(
        key=ModelKey('scripted', 'scripted'),
        backend='scripted',
    )


def _message(text):
    return AiMessage([TextContent(text)], stop_reason='stop')


def test_immediate_backend_is_distinct_and_consumes_turns():
    script = BackendScript([
        BackendScriptTurn(_message('first')),
        BackendScriptTurn(_message('second')),
    ])
    backend = ScriptedImmediateBackend(_model(), script)

    assert not isinstance(backend, StreamBackend)
    assert check.isinstance(
        check.single((lang.sync_await(backend.immediate(Context()))).content),
        TextContent,
    ).text == 'first'
    assert check.isinstance(
        check.single((lang.sync_await(backend.immediate(Context()))).content),
        TextContent,
    ).text == 'second'

    with pytest.raises(BackendScriptExhaustedError):
        lang.sync_await(backend.immediate(Context()))


def test_expectation_and_error():
    seen = []

    def expect(invocation):
        seen.append(invocation)
        assert check.single(invocation.context.messages).content == 'expected'
        assert invocation.options.max_tokens == 123

    backend = ScriptedImmediateBackend(_model(), BackendScript([
        BackendScriptTurn(
            expect=expect,
            error=RuntimeError('scripted failure'),
        ),
    ]))

    with pytest.raises(RuntimeError, match='scripted failure'):
        lang.sync_await(backend.immediate(
            Context(messages=[UserMessage('expected')]),
            Options(max_tokens=123),
        ))

    assert len(seen) == 1
    assert seen[0].invocation_index == 0


def test_exhaustion_policies_and_shared_cursor():
    repeating = ScriptedImmediateBackend(_model(), BackendScript(
        [BackendScriptTurn(_message('same'))],
        on_exhausted='repeat_last',
    ))
    assert [
        check.isinstance(
            check.single((lang.sync_await(repeating.immediate(Context()))).content),
            TextContent,
        ).text
        for _ in range(3)
    ] == ['same', 'same', 'same']

    script = BackendScript([
        BackendScriptTurn(_message('a')),
        BackendScriptTurn(_message('b')),
    ])
    cursor = BackendScriptCursor(script)
    first = ScriptedImmediateBackend(_model(), cursor=cursor)
    second = ScriptedImmediateBackend(_model(), cursor=cursor)

    assert check.isinstance(
        check.single((lang.sync_await(first.immediate(Context()))).content),
        TextContent,
    ).text == 'a'
    assert check.isinstance(
        check.single((lang.sync_await(second.immediate(Context()))).content),
        TextContent,
    ).text == 'b'


def test_stream_backend_events_result_and_gate():
    points = []

    async def gate(point):
        points.append((point.invocation_index, point.emission_index))

    message = AiMessage(
        [
            ThinkingContent('pondering'),
            TextContent('answer'),
            ToolCall('call_1', 'lookup', {'key': 'value'}),
        ],
        stop_reason='tool_use',
    )
    backend = ScriptedStreamBackend(_model(), BackendScript(
        [BackendScriptTurn(message, chunk_size=3)],
        gate=gate,
    ))

    assert isinstance(backend, StreamBackend)

    with lang.sync_async_with(lang.sync_await(backend.stream(
            Context(),
    ))) as stream:
        events: list = []
        for e in lang.sync_aiter(stream):
            events.append(e)  # noqa
        result = stream.result.must()

    assert result is message
    assert isinstance(events[0], StreamStartAiStreamEvent)
    assert isinstance(events[-1], StreamEndAiStreamEvent)
    assert ''.join(event.text for event in events if isinstance(event, ThinkingDeltaAiStreamEvent)) == 'pondering'
    assert ''.join(event.text for event in events if isinstance(event, TextDeltaAiStreamEvent)) == 'answer'
    assert ''.join(event.text for event in events if isinstance(event, ToolCallDeltaAiStreamEvent)) == '{"key":"value"}'
    assert points == [(0, i) for i in range(len(events) + 1)]

    with pytest.raises(BackendScriptExhaustedError):
        lang.sync_await(backend.immediate(Context()))


def test_stream_gate_can_fail_midstream():
    async def gate(point):
        if point.emission_index == 2:
            raise RuntimeError('midstream failure')

    backend = ScriptedStreamBackend(_model(), BackendScript(
        [BackendScriptTurn(_message('abcdefgh'), chunk_size=2)],
        gate=gate,
    ))

    def run():
        with lang.sync_async_with(lang.sync_await(backend.stream(
            Context(),
        ))) as stream:
            for _ in lang.sync_aiter(stream):
                pass

    with pytest.raises(RuntimeError, match='midstream failure'):
        run()
