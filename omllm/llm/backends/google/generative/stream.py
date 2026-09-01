import typing as ta
import uuid

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
from .base import BaseGoogleGenerativeBackend
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

        self._next_tool_call_index_ = 0

    def _feed(self, sse: SseEvent) -> None:
        try:
            raw_chunk = json.loads(sse.data)
        except (json.DecodeError, ValueError):
            return
        raw_chunk = check.isinstance(raw_chunk, ta.Mapping)

        if 'error' in raw_chunk and raw_chunk.get('error'):
            raise BackendError(_stringify_error(raw_chunk['error']))

        # Chunks carry cumulative usage - each overwrites the last, leaving the final chunk's totals.
        if (raw_usage := raw_chunk.get('usageMetadata')) is not None:
            self._message.token_usage = fill_estimated_token_cost(
                translate_token_usage(check.isinstance(raw_usage, ta.Mapping)),
                self._pricing,
            )

        if not (raw_candidates := raw_chunk.get('candidates')):
            return
        raw_candidate = check.isinstance(check.single(raw_candidates), ta.Mapping)

        if (raw_content := raw_candidate.get('content')) is not None:
            raw_content = check.isinstance(raw_content, ta.Mapping)

            for raw_part in raw_content.get('parts') or []:
                raw_part = check.isinstance(raw_part, ta.Mapping)

                if raw_part.get('thought'):
                    thinking = self._thinking()

                    if raw_text := check.isinstance(raw_part.get('text') or '', str):
                        self._emit(ThinkingDeltaAiStreamEvent(
                            raw_text,
                            content_index=self._content_index(thinking),
                        ))
                        thinking.text.write(raw_text)

                    if raw_sig := raw_part.get('thoughtSignature'):
                        thinking.backend_signature = check.isinstance(raw_sig, str)

                    continue

                if 'text' in raw_part:
                    raw_text = check.isinstance(raw_part['text'], str)

                    # A signature may ride a text part - even an empty one - and must be captured for echoing.
                    if raw_text or raw_part.get('thoughtSignature'):
                        text = self._text()

                        if raw_text:
                            self._emit(TextDeltaAiStreamEvent(
                                raw_text,
                                content_index=self._content_index(text),
                            ))
                            text.text.write(raw_text)

                        if raw_sig := raw_part.get('thoughtSignature'):
                            text.backend_signature = check.isinstance(raw_sig, str)

                elif 'functionCall' in raw_part:
                    raw_fc = check.isinstance(raw_part['functionCall'], ta.Mapping)

                    # Function calls arrive whole - args are a complete mapping, never streamed as partial json - so
                    # each such part is a fully-formed new tool call, indexed only by arrival order. Google does not
                    # reliably issue ids for them, so they are fabricated as needed.
                    tool_call = self._tool_call(
                        id=check.non_empty_str(raw_fc.get('id') or str(uuid.uuid7())),
                        index=self._next_tool_call_index_,
                    )
                    self._next_tool_call_index_ += 1

                    tool_call.name = check.non_empty_str(raw_fc['name'])
                    tool_call.backend_signature = check.isinstance(raw_part.get('thoughtSignature'), (str, None))

                    args_delta = json.dumps(check.isinstance(raw_fc.get('args') or {}, ta.Mapping))
                    tool_call.partial_args.write(args_delta)
                    tool_call.parse_args()

                    self._emit(ToolCallDeltaAiStreamEvent(
                        args_delta,
                        content_index=self._content_index(tool_call),
                    ))

                else:
                    raise ValueError(raw_part)

        if raw_fr := raw_candidate.get('finishReason'):
            stop_reason = translate_stop_reason(check.isinstance(raw_fr, str))

            # Google reports STOP even on tool-calling turns.
            if stop_reason == 'stop' and self._next_tool_call_index_ > 0:
                stop_reason = 'tool_use'

            self._message.stop_reason = stop_reason


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='google-generative',
#     type='$.llm.types.backends.StreamBackend',
# )
class GoogleGenerativeStreamBackend(BaseGoogleGenerativeBackend, StreamBackend):
    async def stream(self, context: Context, options: Options | None = None) -> AiStream:
        raw_request = RequestPreparer(  # noqa
            self._model,
            context,
            options,
        ).raw_request()

        #

        http_headers = {
            **({'x-goog-api-key': self._api_key.reveal()} if self._api_key is not None else {}),
            'content-type': 'application/json',
            'accept': 'application/json',
            **(self._model_http.extra_headers or {}),
        }

        http_request = http.HttpClientRequest(
            f'{self._base_url}/models/{self._model.key_.id}:streamGenerateContent?alt=sse',
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
