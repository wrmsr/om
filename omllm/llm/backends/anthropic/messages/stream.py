import typing as ta

from omcore import check
from omcore import resources as rs
from omcore.formats.json import all as json
from omcore.http import all as http

from .....core.http.sse import SseEvent
from ....models.pricing import fill_estimated_token_cost
from ....types.backends import StreamBackend
from ....types.context import Context
from ....types.errors import BackendError
from ....types.models import TokenPricing
from ....types.options import Options
from ....types.streams import AiStream
from ....types.streams import TextDeltaAiStreamEvent
from ....types.streams import ThinkingDeltaAiStreamEvent
from ....types.streams import ToolCallDeltaAiStreamEvent
from ...base.sse import BaseBackendSseEventProcessor
from .base import BaseAnthropicMessagesBackend
from .requests import RequestPreparer
from .responses import translate_stop_reason
from .responses import translate_token_usage


##


def _stringify_error(error: ta.Any) -> str:
    if isinstance(error, str):
        return error
    try:
        return json.dumps(error)
    except (TypeError, ValueError):
        return str(error)


class SseEventProcessor(BaseBackendSseEventProcessor):
    def __init__(
            self,
            *,
            pricing: TokenPricing | None = None,
    ) -> None:
        super().__init__()

        self._pricing = pricing

        # Usage arrives split across events - input tokens on message_start, final output tokens on message_delta - so
        # the raw fields are accumulated and retranslated as they appear.
        self._raw_usage_: dict[str, ta.Any] = {}

    def _feed_usage(self, raw_usage: ta.Mapping[str, ta.Any]) -> None:
        self._raw_usage_.update(raw_usage)
        self._message.token_usage = fill_estimated_token_cost(
            translate_token_usage(self._raw_usage_),
            self._pricing,
        )

    def _feed_content_block_start(self, raw_event: ta.Mapping[str, ta.Any]) -> None:
        raw_index = check.isinstance(raw_event['index'], int)
        raw_block = check.isinstance(raw_event['content_block'], ta.Mapping)

        raw_block_type = raw_block['type']

        if raw_block_type == 'text':
            text = self._text()

            if raw_text := raw_block.get('text'):
                raw_text = check.isinstance(raw_text, str)
                self._emit(TextDeltaAiStreamEvent(
                    raw_text,
                    content_index=self._content_index(text),
                ))
                text.text.write(raw_text)

        elif raw_block_type == 'tool_use':
            tool_call = self._tool_call(
                id=check.non_empty_str(raw_block['id']),
                index=raw_index,
            )

            tool_call.name = check.non_empty_str(raw_block['name'])

            # A tool call with empty input may receive no input_json_delta events at all - the initial input given here,
            # usually an empty mapping, must be taken as potentially final.
            if (raw_input := raw_block.get('input')) is not None:
                tool_call.args = check.isinstance(raw_input, ta.Mapping)

        elif raw_block_type == 'thinking':
            # Note thinking blocks may appear even when not requested, and may carry no text at all - some models stream
            # only a signature_delta, which must still be preserved for replay.
            thinking = self._thinking()

            if raw_thinking := raw_block.get('thinking'):
                raw_thinking = check.isinstance(raw_thinking, str)
                self._emit(ThinkingDeltaAiStreamEvent(
                    raw_thinking,
                    content_index=self._content_index(thinking),
                ))
                thinking.text.write(raw_thinking)

            if raw_sig := raw_block.get('signature'):
                thinking.backend_signature = check.isinstance(raw_sig, str)

        elif raw_block_type == 'redacted_thinking':
            # Opaque and unreadable, but still preserved for replay - the data blob rides backend_signature. Arrives
            # whole, with no subsequent deltas.
            thinking = self._thinking()

            self._emit(ThinkingDeltaAiStreamEvent(
                '<redacted>',
                content_index=self._content_index(thinking),
            ))
            thinking.text.write('<redacted>')
            thinking.redacted = True

            if raw_data := raw_block.get('data'):
                thinking.backend_signature = check.isinstance(raw_data, str)

        else:
            raise ValueError(raw_block_type)

    def _feed_content_block_delta(self, raw_event: ta.Mapping[str, ta.Any]) -> None:
        raw_index = check.isinstance(raw_event['index'], int)
        raw_delta = check.isinstance(raw_event['delta'], ta.Mapping)

        raw_delta_type = raw_delta['type']

        if raw_delta_type == 'text_delta':
            if raw_text := check.isinstance(raw_delta['text'], str):
                text = self._text()
                self._emit(TextDeltaAiStreamEvent(
                    raw_text,
                    content_index=self._content_index(text),
                ))
                text.text.write(raw_text)

        elif raw_delta_type == 'input_json_delta':
            tool_call = self._tool_call(index=raw_index)

            args_delta = check.isinstance(raw_delta['partial_json'], str)
            if args_delta:
                tool_call.partial_args.write(args_delta)
                tool_call.parse_args()

            self._emit(ToolCallDeltaAiStreamEvent(
                args_delta,
                content_index=self._content_index(tool_call),
            ))

        elif raw_delta_type == 'thinking_delta':
            if raw_thinking := check.isinstance(raw_delta['thinking'], str):
                thinking = self._thinking()
                self._emit(ThinkingDeltaAiStreamEvent(
                    raw_thinking,
                    content_index=self._content_index(thinking),
                ))
                thinking.text.write(raw_thinking)

        elif raw_delta_type == 'signature_delta':
            if raw_sig := check.isinstance(raw_delta['signature'], str):
                thinking = self._thinking()
                thinking.backend_signature = (thinking.backend_signature or '') + raw_sig

        else:
            raise ValueError(raw_delta_type)

    def _feed(self, sse: SseEvent) -> None:
        try:
            raw_event = json.loads(sse.data)
        except (json.DecodeError, ValueError):
            return
        raw_event = check.isinstance(raw_event, ta.Mapping)

        raw_event_type = raw_event.get('type')

        if raw_event_type == 'error':
            raise BackendError(_stringify_error(raw_event.get('error')))

        elif raw_event_type == 'message_start':
            raw_message = check.isinstance(raw_event['message'], ta.Mapping)
            check.equal(raw_message['type'], 'message')
            check.equal(raw_message['role'], 'assistant')

            if (raw_usage := raw_message.get('usage')) is not None:
                self._feed_usage(check.isinstance(raw_usage, ta.Mapping))

        elif raw_event_type == 'content_block_start':
            self._feed_content_block_start(raw_event)

        elif raw_event_type == 'content_block_delta':
            self._feed_content_block_delta(raw_event)

        elif raw_event_type == 'content_block_stop':
            # Block boundaries are explicit - closing here keeps adjacent blocks of the same type (and their individual
            # signatures) distinct rather than merged.
            self._close_text()
            self._close_thinking()

        elif raw_event_type == 'message_delta':
            raw_delta = check.isinstance(raw_event['delta'], ta.Mapping)

            if raw_sr := raw_delta.get('stop_reason'):
                self._message.stop_reason = translate_stop_reason(check.isinstance(raw_sr, str))

            if (raw_usage := raw_event.get('usage')) is not None:
                self._feed_usage(check.isinstance(raw_usage, ta.Mapping))

        else:
            # The remaining known event types - ping and message_stop - carry nothing currently tracked, and
            # unrecognized event types must be skipped for forward compatibility.
            pass


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='anthropic-messages',
#     type='$.llm.types.backends.StreamBackend',
# )
class AnthropicMessagesStreamBackend(BaseAnthropicMessagesBackend, StreamBackend):
    async def stream(self, context: Context, options: Options | None = None) -> AiStream:
        raw_request = RequestPreparer(  # noqa
            self._model,
            context,
            options,
        ).raw_request()

        raw_request['stream'] = True

        #

        http_headers = {
            **({'x-api-key': self._api_key.reveal()} if self._api_key is not None else {}),
            'content-type': 'application/json',
            'accept': 'application/json',
            **(self._model_http.extra_headers or {}),
        }

        http_request = http.HttpClientRequest(
            self._base_url + '/messages',
            headers=http_headers,
            data=json.dumps(raw_request).encode('utf-8'),
        )

        #

        async with await rs.async_contextual_or_new(bind=True) as rm:  # noqa
            http_client = await rm.enter_async_context(http.manage_async_client(self._http_client))
            http_response = await rm.enter_async_context(await http_client.stream_request(http_request))

            if http_response.status != 200:
                err_http_response = await http.async_read_http_client_response(http_response)
                raise http.StatusHttpClientError(err_http_response)

            processor = SseEventProcessor(
                pricing=self._pricing,
            )

            return await processor.stream_http_response(http_response)
