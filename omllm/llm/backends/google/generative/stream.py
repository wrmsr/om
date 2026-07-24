import typing as ta
import uuid

from omcore import check
from omcore import resources as rs
from omcore.formats.json import all as json
from omcore.http import all as http

from .....core.http.sse import SseEvent
from ....types.backends import StreamBackend
from ....types.context import Context
from ....types.options import Options
from ....types.streams import AiStream
from ....types.streams import TextDeltaAiStreamEvent
from ....types.streams import ToolCallDeltaAiStreamEvent
from ...base.http import BaseHttpBackend
from ...base.sse import BaseBackendSseEventProcessor
from .requests import RequestPreparer


##


def _stringify_error(error: ta.Any) -> str:
    if isinstance(error, str):
        return error
    try:
        return json.dumps(error)
    except (TypeError, ValueError):
        return str(error)


class SseEventProcessor(BaseBackendSseEventProcessor):
    def __init__(self) -> None:
        super().__init__()

        self._next_tool_call_index_ = 0

    def _feed(self, sse: SseEvent) -> None:
        try:
            raw_chunk = json.loads(sse.data)
        except (json.DecodeError, ValueError):
            return
        raw_chunk = check.isinstance(raw_chunk, ta.Mapping)

        if 'error' in raw_chunk and raw_chunk.get('error'):
            raise RuntimeError(_stringify_error(raw_chunk['error']))

        if not (raw_candidates := raw_chunk.get('candidates')):
            return
        raw_candidate = check.isinstance(check.single(raw_candidates), ta.Mapping)

        if (raw_content := raw_candidate.get('content')) is None:
            return
        raw_content = check.isinstance(raw_content, ta.Mapping)

        for raw_part in raw_content.get('parts') or []:
            raw_part = check.isinstance(raw_part, ta.Mapping)

            if raw_part.get('thought'):
                continue

            if 'text' in raw_part:
                if raw_text := check.isinstance(raw_part['text'], str):
                    text = self._text()
                    self._emit(TextDeltaAiStreamEvent(
                        raw_text,
                        content_index=self._content_index(text),
                    ))
                    text.text.write(raw_text)

            elif 'functionCall' in raw_part:
                raw_fc = check.isinstance(raw_part['functionCall'], ta.Mapping)

                # Function calls arrive whole - args are a complete mapping, never streamed as partial json - so each
                # such part is a fully-formed new tool call. Google does not reliably issue ids for them, so they are
                # fabricated as needed, and blocks are only indexed by arrival order.
                tool_call = self._tool_call(
                    id=check.non_empty_str(raw_fc.get('id') or str(uuid.uuid4())),
                    index=self._next_tool_call_index_,
                )
                self._next_tool_call_index_ += 1

                tool_call.name = check.non_empty_str(raw_fc['name'])

                args_delta = json.dumps(check.isinstance(raw_fc.get('args') or {}, ta.Mapping))
                tool_call.partial_args.write(args_delta)
                tool_call.parse_args()

                self._emit(ToolCallDeltaAiStreamEvent(
                    args_delta,
                    content_index=self._content_index(tool_call),
                ))

            else:
                raise ValueError(raw_part)


##


class GoogleGenerativeStreamBackend(BaseHttpBackend, StreamBackend):
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
            f'{self._base_url}/models/{self._model.key.id}:streamGenerateContent?alt=sse',
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

            processor = SseEventProcessor()

            return await processor.stream_http_response(http_response)
