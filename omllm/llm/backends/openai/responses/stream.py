import typing as ta

from omcore import check
from omcore import resources as rs
from omcore.formats.json import all as json
from omcore.http import all as http

from .....core.http.sse import SseEvent
from ....models.pricing import fill_estimated_token_cost
from ....types.backends import StreamBackend
from ....types.content import ContentBuilder
from ....types.content import TextContentBuilder
from ....types.content import ThinkingContentBuilder
from ....types.content import ToolCallBuilder
from ....types.context import Context
from ....types.models import TokenPricing
from ....types.options import Options
from ....types.streams import AiStream
from ....types.streams import TextDeltaAiStreamEvent
from ....types.streams import ThinkingDeltaAiStreamEvent
from ....types.streams import ToolCallDeltaAiStreamEvent
from ...base.sse import BaseBackendSseEventProcessor
from .base import BaseOpenaiResponsesBackend
from .requests import RequestPreparer
from .responses import stringify_error
from .responses import translate_stop_reason
from .responses import translate_token_usage
from .signatures import build_text_signature
from .signatures import build_thinking_signature
from .signatures import build_tool_call_signature


ContentBuilderT = ta.TypeVar('ContentBuilderT', bound=ContentBuilder)


##


class SseEventProcessor(BaseBackendSseEventProcessor):
    def __init__(
            self,
            *,
            pricing: TokenPricing | None = None,
    ) -> None:
        super().__init__()

        self._pricing = pricing

        # Deltas are routed by output_index. Item boundaries come only from output_item events - each opens a fresh
        # content block even when adjacent items share a type, keeping per-item replay identity distinct.
        self._builders_by_index_: dict[int, ContentBuilder] = {}

    def _index_builder(self, raw_event: ta.Mapping[str, ta.Any], cls: type[ContentBuilderT]) -> ContentBuilderT:
        raw_index = check.isinstance(raw_event['output_index'], int)
        return check.isinstance(self._builders_by_index_[raw_index], cls)

    #

    def _feed_output_item_added(self, raw_event: ta.Mapping[str, ta.Any]) -> None:
        raw_index = check.isinstance(raw_event['output_index'], int)
        raw_item = check.isinstance(raw_event['item'], ta.Mapping)

        check.not_in(raw_index, self._builders_by_index_)

        raw_item_type = check.isinstance(raw_item['type'], str)

        builder: ContentBuilder

        if raw_item_type == 'reasoning':
            self._close_thinking()
            builder = self._thinking()

        elif raw_item_type == 'message':
            check.equal(raw_item['role'], 'assistant')
            self._close_text()
            builder = self._text()

        elif raw_item_type == 'function_call':
            tool_call = self._tool_call(id=check.non_empty_str(raw_item['call_id']))
            tool_call.name = check.non_empty_str(raw_item['name'])

            if raw_args := raw_item.get('arguments'):
                tool_call.partial_args.write(check.isinstance(raw_args, str))
                tool_call.parse_args()

            builder = tool_call

        else:
            raise ValueError(raw_item_type)

        self._builders_by_index_[raw_index] = builder

    def _feed_output_item_done(self, raw_event: ta.Mapping[str, ta.Any]) -> None:
        raw_item = check.isinstance(raw_event['item'], ta.Mapping)

        raw_item_type = check.isinstance(raw_item['type'], str)

        if raw_item_type == 'reasoning':
            thinking = self._index_builder(raw_event, ThinkingContentBuilder)
            # The added-time item is not the replayable form - encrypted content in particular is only final here.
            thinking.backend_signature = build_thinking_signature(raw_item)
            self._close_thinking()

        elif raw_item_type == 'message':
            text = self._index_builder(raw_event, TextContentBuilder)
            text.backend_signature = build_text_signature(raw_item)
            self._close_text()

        elif raw_item_type == 'function_call':
            tool_call = self._index_builder(raw_event, ToolCallBuilder)

            # The done-time item carries the complete argument text, authoritative over accumulated deltas.
            if raw_args := raw_item.get('arguments'):
                tool_call.args = check.isinstance(json.loads(check.isinstance(raw_args, str)), ta.Mapping)

            tool_call.backend_signature = build_tool_call_signature(raw_item)

        else:
            raise ValueError(raw_item_type)

    def _feed_terminal_response(self, raw_response: ta.Mapping[str, ta.Any]) -> None:
        if (raw_usage := raw_response.get('usage')) is not None:
            self._message.token_usage = fill_estimated_token_cost(
                translate_token_usage(check.isinstance(raw_usage, ta.Mapping)),
                self._pricing,
            )

        incomplete_reason: str | None = None
        if (raw_details := check.isinstance(raw_response.get('incomplete_details'), (ta.Mapping, None))) is not None:
            incomplete_reason = check.isinstance(raw_details.get('reason'), (str, None))

        self._message.stop_reason = translate_stop_reason(
            check.non_empty_str(raw_response['status']),
            incomplete_reason=incomplete_reason,
            has_tool_calls=any(isinstance(c, ToolCallBuilder) for c in self._message.content),
        )

    #

    def _feed(self, sse: SseEvent) -> None:
        try:
            raw_event = json.loads(sse.data)
        except (json.DecodeError, ValueError):
            return
        raw_event = check.isinstance(raw_event, ta.Mapping)

        raw_event_type = raw_event.get('type')

        if raw_event_type == 'error':
            raise RuntimeError(stringify_error(raw_event))

        elif raw_event_type == 'response.output_item.added':
            self._feed_output_item_added(raw_event)

        elif raw_event_type == 'response.output_item.done':
            self._feed_output_item_done(raw_event)

        elif raw_event_type == 'response.reasoning_summary_part.added':
            # Summary parts join with a blank line - emitting the separator when a later part opens keeps the streamed
            # text identical to the parts joined whole.
            thinking = self._index_builder(raw_event, ThinkingContentBuilder)
            if thinking.text.tell():
                self._emit(ThinkingDeltaAiStreamEvent(
                    '\n\n',
                    content_index=self._content_index(thinking),
                ))
                thinking.text.write('\n\n')

        elif raw_event_type == 'response.reasoning_summary_text.delta':
            if raw_delta := check.isinstance(raw_event['delta'], str):
                thinking = self._index_builder(raw_event, ThinkingContentBuilder)
                self._emit(ThinkingDeltaAiStreamEvent(
                    raw_delta,
                    content_index=self._content_index(thinking),
                ))
                thinking.text.write(raw_delta)

        elif raw_event_type in ('response.output_text.delta', 'response.refusal.delta'):
            # Refusals read as ordinary text - the terminal status governs the stop reason.
            if raw_delta := check.isinstance(raw_event['delta'], str):
                text = self._index_builder(raw_event, TextContentBuilder)
                self._emit(TextDeltaAiStreamEvent(
                    raw_delta,
                    content_index=self._content_index(text),
                ))
                text.text.write(raw_delta)

        elif raw_event_type == 'response.function_call_arguments.delta':
            tool_call = self._index_builder(raw_event, ToolCallBuilder)

            raw_delta = check.isinstance(raw_event['delta'], str)
            if raw_delta:
                tool_call.partial_args.write(raw_delta)
                tool_call.parse_args()

            self._emit(ToolCallDeltaAiStreamEvent(
                raw_delta,
                content_index=self._content_index(tool_call),
            ))

        elif raw_event_type in ('response.completed', 'response.incomplete'):
            self._feed_terminal_response(check.isinstance(raw_event['response'], ta.Mapping))

        elif raw_event_type == 'response.failed':
            raw_response = check.isinstance(raw_event['response'], ta.Mapping)
            raise RuntimeError(stringify_error(raw_response.get('error')))

        else:
            # The remaining known event types - lifecycle progress, part boundaries, and whole-value .done restatements
            # of accumulated deltas - carry nothing not already tracked, and unrecognized event types must be skipped
            # for forward compatibility.
            pass


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='openai-responses',
#     type='$.llm.types.backends.StreamBackend',
# )
class OpenaiResponsesStreamBackend(BaseOpenaiResponsesBackend, StreamBackend):
    async def stream(self, context: Context, options: Options | None = None) -> AiStream:
        preparer = RequestPreparer(
            self._model,
            context,
            options,
        )

        raw_request = preparer.raw_request()

        raw_request['stream'] = True

        #

        http_headers = {
            **({'authorization': f'Bearer {self._api_key.reveal()}'} if self._api_key is not None else {}),
            'content-type': 'application/json',
            'accept': 'application/json',
            **(self._model_http.extra_headers or {}),
        }

        http_request = http.HttpClientRequest(
            self._url,
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
