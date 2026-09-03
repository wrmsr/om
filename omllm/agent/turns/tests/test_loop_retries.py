"""Retry of transiently failing LLM calls, with the backoff asserted on rather than waited out."""
import pytest

from .... import llm
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.sleeps import RecordingSleeps
from ...types.events import LlmAiStreamEvent
from ...types.events import LlmRetryEvent
from ...types.turns import AgentEndReason
from ...types.turns import LlmRetryConfig
from ...types.turns import TurnConfig
from ..loop import TurnLoop


##


def _retry_config(**kwargs):
    return LlmRetryConfig(**{
        'max_retries': 3,
        'initial_delay_s': 1.,
        'max_delay_s': 30.,
        'multiplier': 2.,
        **kwargs,
    })


async def _run(backend, *, retry=None, sleeps=None, events=None):
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        config=TurnConfig(llm_retry=retry),
        subscriber=events.append if events is not None else None,
        llm_backend=backend,
        sleeps=sleeps,
    )
    return await loop.run()


def _retry_events(events):
    return [e for e in events if isinstance(e, LlmRetryEvent)]


@pytest.mark.asyncs('asyncio')
async def test_transient_failures_are_retried_with_backoff():
    backend = scripted_backend(
        llm.TransientBackendError('overloaded'),
        llm.TransientBackendError('still overloaded'),
        text_message('ok'),
    )
    sleeps = RecordingSleeps()
    events: list = []

    result = await _run(backend, retry=_retry_config(), sleeps=sleeps, events=events)

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 3
    assert sleeps.delays == [1., 2.]

    retries = _retry_events(events)
    assert [r.attempts for r in retries] == [1, 2]
    assert [r.delay_s for r in retries] == [1., 2.]
    assert all(isinstance(r.error, llm.TransientBackendError) for r in retries)


@pytest.mark.asyncs('asyncio')
async def test_backoff_is_capped_and_a_providers_delay_wins():
    backend = scripted_backend(
        llm.TransientBackendError('a'),
        llm.TransientBackendError('b', retry_after_s=7.5),
        llm.TransientBackendError('c'),
        text_message('ok'),
    )
    sleeps = RecordingSleeps()

    result = await _run(backend, retry=_retry_config(multiplier=10., max_delay_s=3.), sleeps=sleeps)

    assert result.reason is AgentEndReason.COMPLETED
    assert sleeps.delays == [1., 7.5, 3.]


@pytest.mark.asyncs('asyncio')
async def test_retries_exhaust_into_failure():
    last = llm.TransientBackendError('last')
    backend = scripted_backend(
        llm.TransientBackendError('first'),
        last,
        text_message('never'),
    )
    sleeps = RecordingSleeps()

    result = await _run(backend, retry=_retry_config(max_retries=1), sleeps=sleeps)

    assert result.reason is AgentEndReason.FAILED
    assert result.error is last
    assert backend.invocations == 2
    assert sleeps.delays == [1.]


@pytest.mark.asyncs('asyncio')
async def test_non_transient_failures_are_not_retried():
    error = llm.BackendError('bad request')
    backend = scripted_backend(error, text_message('never'))
    sleeps = RecordingSleeps()

    result = await _run(backend, retry=_retry_config(), sleeps=sleeps)

    assert result.reason is AgentEndReason.FAILED
    assert result.error is error
    assert backend.invocations == 1
    assert sleeps.delays == []


@pytest.mark.asyncs('asyncio')
async def test_no_retry_config_means_no_retries():
    error = llm.TransientBackendError('overloaded')
    backend = scripted_backend(error, text_message('never'))
    sleeps = RecordingSleeps()

    result = await _run(backend, sleeps=sleeps)

    assert result.reason is AgentEndReason.FAILED
    assert result.error is error
    assert backend.invocations == 1
    assert sleeps.delays == []


def test_retry_config_needs_a_sleeper():
    with pytest.raises(RuntimeError, match='sleeper'):
        TurnLoop(
            new_messages=[llm.UserMessage('hi')],
            config=TurnConfig(llm_retry=_retry_config()),
            llm_backend=scripted_backend(text_message('ok')),
        )


##


@pytest.mark.asyncs('asyncio')
async def test_stream_failing_before_content_is_retried():
    backend = scripted_backend(
        llm.TransientBackendError('overloaded'),
        text_message('ok'),
        stream=True,
    )
    sleeps = RecordingSleeps()
    events: list = []

    result = await _run(backend, retry=_retry_config(), sleeps=sleeps, events=events)

    assert result.reason is AgentEndReason.COMPLETED
    assert sleeps.delays == [1.]

    # Only the successful attempt's stream reached subscribers.
    text = ''.join(
        e.event.text
        for e in events
        if isinstance(e, LlmAiStreamEvent) and isinstance(e.event, llm.TextDeltaAiStreamEvent)
    )
    assert text == 'ok'


@pytest.mark.parametrize(('fail_at', 'retried'), [
    # Before the first emission at all, and after only the stream-start marker: nothing content-bearing was seen.
    (0, True),
    (1, True),
    # After the first content event: the failure stands.
    (2, False),
])
@pytest.mark.asyncs('asyncio')
async def test_stream_failing_mid_way_is_retried_only_before_content(fail_at, retried):
    async def gate(point):
        if point.invocation_index == 0 and point.emission_index == fail_at:
            raise llm.TransientBackendError('dropped')

    backend = scripted_backend(
        text_message('first'),
        text_message('second'),
        stream=True,
        gate=gate,
    )
    sleeps = RecordingSleeps()
    events: list = []

    result = await _run(backend, retry=_retry_config(), sleeps=sleeps, events=events)

    if retried:
        assert result.reason is AgentEndReason.COMPLETED
        assert sleeps.delays == [1.]
        assert backend.invocations == 2
        assert [type(m) for m in result.new_messages][-1] is llm.AiMessage
        assert result.new_messages[-1].content[0].text == 'second'
    else:
        assert result.reason is AgentEndReason.FAILED
        assert isinstance(result.error, llm.TransientBackendError)
        assert sleeps.delays == []
        assert backend.invocations == 1
        assert any(isinstance(e, LlmAiStreamEvent) and isinstance(e.event, llm.TextStartAiStreamEvent) for e in events)
