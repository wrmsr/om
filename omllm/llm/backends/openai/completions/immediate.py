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
from .base import BaseOpenaiCompletionsBackend
from .requests import RequestPreparer
from .responses import translate_stop_reason
from .responses import translate_token_usage


##


class OpenaiCompletionsImmediateBackend(BaseOpenaiCompletionsBackend, ImmediateBackend):
    async def immediate(self, context: Context, options: Options | None = None) -> AiMessage:
        preparer = RequestPreparer(
            self._model,
            context,
            options,
        )

        raw_request = preparer.raw_request()

        raw_request['stream'] = False

        #

        http_headers = {
            **({'authorization': f'Bearer {self._api_key.reveal()}'} if self._api_key is not None else {}),
            'content-type': 'application/json',
            'accept': 'application/json',
            **preparer.raw_headers(),
            **(self._model_http.extra_headers or {}),
        }

        http_request = http.HttpClientRequest(
            self._url,
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

        raw_choice = check.single(raw_response['choices'])

        raw_msg = raw_choice['message']
        check.equal(raw_msg['role'], 'assistant')

        content: list[Content] = []

        # Openai itself returns no reasoning content, but openai-compat backends commonly surface it via a message
        # field - conventionally reasoning_content, remapped per-model via compat. Only the predeclared field is
        # probed.
        if raw_reasoning := raw_msg.get(self._compat.reasoning_field or 'reasoning_content'):
            content.append(ThinkingContent(check.isinstance(raw_reasoning, str)))

        if raw_content := raw_msg.get('content'):
            content.append(TextContent(check.non_empty_str(raw_content)))

        if raw_tool_calls := raw_msg.get('tool_calls'):
            for raw_tool_call in raw_tool_calls:
                check.equal(raw_tool_call['type'], 'function')
                raw_fn = raw_tool_call['function']
                args = json.loads(raw_fn['arguments'])
                content.append(ToolCall(
                    id=check.non_empty_str(raw_tool_call['id']),
                    name=check.non_empty_str(raw_fn['name']),
                    args=check.isinstance(args, ta.Mapping),
                ))

        stop_reason: StopReason | None = None
        if raw_fr := raw_choice.get('finish_reason'):
            stop_reason = translate_stop_reason(check.isinstance(raw_fr, str))

        token_usage: TokenUsage | None = None
        if (raw_usage := raw_response.get('usage')) is not None:
            token_usage = translate_token_usage(
                check.isinstance(raw_usage, ta.Mapping),
                cost_mode=self._compat.cost_mode,
            )
        token_usage = fill_estimated_token_cost(token_usage, self._pricing)

        return AiMessage(
            ta.cast(ta.Any, content),
            stop_reason=stop_reason,
            token_usage=token_usage,
        )
