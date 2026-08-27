import typing as ta
import uuid

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
from .base import BaseGoogleGenerativeBackend
from .requests import RequestPreparer
from .responses import translate_stop_reason
from .responses import translate_token_usage


##


# @om-manifest $.core.registry.manifests.RegistryManifest(
#     name='google-generative',
#     type='ImmediateBackend',
# )
class GoogleGenerativeImmediateBackend(BaseGoogleGenerativeBackend, ImmediateBackend):
    async def immediate(self, context: Context, options: Options | None = None) -> AiMessage:
        raw_request = RequestPreparer(
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
            f'{self._base_url}/models/{self._model.key.id}:generateContent',
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

        raw_candidate = check.isinstance(check.single(raw_response['candidates']), ta.Mapping)

        content: list[Content] = []

        # A candidate may lack content entirely, such as when truncated by MAX_TOKENS before emitting anything.
        if (raw_content := raw_candidate.get('content')) is not None:
            raw_content = check.isinstance(raw_content, ta.Mapping)

            # Truncated candidates may carry a bare content object with no role.
            if (raw_role := raw_content.get('role')) is not None:
                check.equal(raw_role, 'model')

            for raw_part in raw_content.get('parts') or []:
                raw_part = check.isinstance(raw_part, ta.Mapping)

                if raw_part.get('thought'):
                    content.append(ThinkingContent(
                        check.isinstance(raw_part.get('text') or '', str),
                        backend_signature=check.isinstance(raw_part.get('thoughtSignature'), (str, None)),
                    ))
                    continue

                if 'text' in raw_part:
                    if raw_text := raw_part['text']:
                        content.append(TextContent(
                            check.isinstance(raw_text, str),
                            backend_signature=check.isinstance(raw_part.get('thoughtSignature'), (str, None)),
                        ))

                elif 'functionCall' in raw_part:
                    raw_fc = check.isinstance(raw_part['functionCall'], ta.Mapping)

                    content.append(ToolCall(
                        # Google does not reliably issue tool call ids - fabricate as needed.
                        id=check.non_empty_str(raw_fc.get('id') or str(uuid.uuid7())),
                        name=check.non_empty_str(raw_fc['name']),
                        args=check.isinstance(raw_fc.get('args') or {}, ta.Mapping),
                        backend_signature=check.isinstance(raw_part.get('thoughtSignature'), (str, None)),
                    ))

                else:
                    raise ValueError(raw_part)

        stop_reason: StopReason | None = None
        if raw_fr := raw_candidate.get('finishReason'):
            stop_reason = translate_stop_reason(check.isinstance(raw_fr, str))

            # Google reports STOP even on tool-calling turns.
            if stop_reason == 'stop' and any(isinstance(c, ToolCall) for c in content):
                stop_reason = 'tool_use'

        token_usage: TokenUsage | None = None
        if (raw_usage := raw_response.get('usageMetadata')) is not None:
            token_usage = translate_token_usage(check.isinstance(raw_usage, ta.Mapping))
        token_usage = fill_estimated_token_cost(token_usage, self._pricing)

        return AiMessage(
            ta.cast(ta.Any, content),
            stop_reason=stop_reason,
            token_usage=token_usage,
        )
