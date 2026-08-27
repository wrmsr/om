import typing as ta

from omcore import check
from omcore.formats.json import all as json
from omcore.http import all as http

from ....models.pricing import fill_estimated_token_cost
from ....types.backends import ImmediateBackend
from ....types.content import Content
from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.messages import AiMessage
from ....types.messages import StopReason
from ....types.messages import TokenUsage
from ....types.options import Options
from .base import BaseAnthropicMessagesBackend
from .requests import RequestPreparer
from .responses import translate_stop_reason
from .responses import translate_token_usage


##


class AnthropicMessagesImmediateBackend(BaseAnthropicMessagesBackend, ImmediateBackend):
    async def immediate(self, context: Context, options: Options | None = None) -> AiMessage:
        raw_request = RequestPreparer(
            self._model,
            context,
            options,
        ).raw_request()

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

        http_response = await http.async_request(
            http_request,
            client=self._http_client,
        )

        if http_response.status != 200:
            raise http.StatusHttpClientError(http_response)

        raw_response = json.loads(check.not_none(http_response.data).decode('utf-8'))

        #

        check.equal(raw_response['type'], 'message')
        check.equal(raw_response['role'], 'assistant')

        response_content: list[Content] = []

        for raw_c in raw_response['content']:
            if raw_c['type'] == 'text':
                response_content.append(TextContent(raw_c['text']))

            elif raw_c['type'] == 'tool_use':
                response_content.append(ToolCall(
                    id=check.non_empty_str(raw_c['id']),
                    name=check.non_empty_str(raw_c['name']),
                    args=check.isinstance(raw_c.get('input') or {}, ta.Mapping),
                ))

            elif raw_c['type'] == 'thinking':
                # Note thinking blocks may appear even when not requested, and their text may be empty - some models
                # return only a signature, which must still be preserved for replay.
                response_content.append(ThinkingContent(
                    check.isinstance(raw_c.get('thinking') or '', str),
                    backend_signature=check.isinstance(raw_c.get('signature'), (str, None)),
                ))

            elif raw_c['type'] == 'redacted_thinking':
                # Opaque and unreadable, but still preserved for replay - the data blob rides backend_signature.
                response_content.append(ThinkingContent(
                    '<redacted>',
                    backend_signature=check.isinstance(raw_c.get('data'), (str, None)),
                    redacted=True,
                ))

            else:
                raise ValueError(raw_c['type'])

        stop_reason: StopReason | None = None
        if raw_sr := raw_response.get('stop_reason'):
            stop_reason = translate_stop_reason(check.isinstance(raw_sr, str))

        token_usage: TokenUsage | None = None
        if (raw_usage := raw_response.get('usage')) is not None:
            token_usage = translate_token_usage(check.isinstance(raw_usage, ta.Mapping))
        token_usage = fill_estimated_token_cost(token_usage, self._pricing)

        return AiMessage(
            ta.cast(ta.Any, response_content),
            stop_reason=stop_reason,
            token_usage=token_usage,
        )
