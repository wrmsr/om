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
from ....types.errors import BackendError
from ....types.messages import AiMessage
from ....types.messages import TokenUsage
from ....types.options import Options
from .base import BaseOpenaiResponsesBackend
from .requests import RequestPreparer
from .responses import stringify_error
from .responses import translate_stop_reason
from .responses import translate_token_usage
from .signatures import build_text_signature
from .signatures import build_thinking_signature
from .signatures import build_tool_call_signature


##


def _translate_summary_text(raw_item: ta.Mapping[str, ta.Any]) -> str:
    raw_texts: list[str] = []
    for raw_part in raw_item.get('summary') or []:
        raw_part_type = raw_part['type']

        if raw_part_type == 'summary_text':
            raw_texts.append(check.isinstance(raw_part['text'], str))

        else:
            raise ValueError(raw_part_type)

    return '\n\n'.join(raw_texts)


def _translate_message_text(raw_item: ta.Mapping[str, ta.Any]) -> str:
    raw_texts: list[str] = []
    for raw_part in raw_item.get('content') or []:
        raw_part_type = raw_part['type']

        if raw_part_type == 'output_text':
            raw_texts.append(check.isinstance(raw_part['text'], str))

        elif raw_part_type == 'refusal':
            # Refusals read as ordinary text - the response status governs the stop reason.
            raw_texts.append(check.isinstance(raw_part['refusal'], str))

        else:
            raise ValueError(raw_part_type)

    return ''.join(raw_texts)


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='openai-responses',
#     type='$.llm.types.backends.ImmediateBackend',
# )
class OpenaiResponsesImmediateBackend(BaseOpenaiResponsesBackend, ImmediateBackend):
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

        raw_status = check.non_empty_str(raw_response['status'])
        if raw_status == 'failed':
            raise BackendError(stringify_error(raw_response.get('error')))

        content: list[Content] = []

        for raw_item in raw_response['output'] or []:
            raw_item_type = check.isinstance(raw_item['type'], str)

            if raw_item_type == 'reasoning':
                content.append(ThinkingContent(
                    _translate_summary_text(raw_item),
                    backend_signature=build_thinking_signature(raw_item),
                ))

            elif raw_item_type == 'message':
                check.equal(raw_item['role'], 'assistant')
                content.append(TextContent(
                    _translate_message_text(raw_item),
                    backend_signature=build_text_signature(raw_item),
                ))

            elif raw_item_type == 'function_call':
                args = json.loads(raw_item['arguments'])
                content.append(ToolCall(
                    id=check.non_empty_str(raw_item['call_id']),
                    name=check.non_empty_str(raw_item['name']),
                    args=check.isinstance(args, ta.Mapping),
                    backend_signature=build_tool_call_signature(raw_item),
                ))

            else:
                raise ValueError(raw_item_type)

        incomplete_reason: str | None = None
        if (raw_details := check.isinstance(raw_response.get('incomplete_details'), (ta.Mapping, None))) is not None:
            incomplete_reason = check.isinstance(raw_details.get('reason'), (str, None))

        stop_reason = translate_stop_reason(
            raw_status,
            incomplete_reason=incomplete_reason,
            has_tool_calls=any(isinstance(c, ToolCall) for c in content),
        )

        token_usage: TokenUsage | None = None
        if (raw_usage := raw_response.get('usage')) is not None:
            token_usage = translate_token_usage(check.isinstance(raw_usage, ta.Mapping))
        token_usage = fill_estimated_token_cost(token_usage, self._pricing)

        return AiMessage(
            ta.cast(ta.Any, content),
            stop_reason=stop_reason,
            token_usage=token_usage,
        )
