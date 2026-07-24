import typing as ta
import uuid

from omcore import check
from omcore.formats.json import all as json
from omcore.http import all as http

from ....types.backends import ImmediateBackend
from ....types.content import Content
from ....types.content import TextContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.messages import AiMessage
from ....types.options import Options
from ...base.http import BaseHttpBackend
from .requests import RequestPreparer


##


class GoogleGenerativeImmediateBackend(BaseHttpBackend, ImmediateBackend):
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
            check.equal(raw_content['role'], 'model')

            for raw_part in raw_content.get('parts') or []:
                raw_part = check.isinstance(raw_part, ta.Mapping)

                if raw_part.get('thought'):
                    continue

                if 'text' in raw_part:
                    if raw_text := raw_part['text']:
                        content.append(TextContent(check.isinstance(raw_text, str)))

                elif 'functionCall' in raw_part:
                    raw_fc = check.isinstance(raw_part['functionCall'], ta.Mapping)

                    content.append(ToolCall(
                        # Google does not reliably issue tool call ids - fabricate as needed.
                        id=check.non_empty_str(raw_fc.get('id') or str(uuid.uuid4())),
                        name=check.non_empty_str(raw_fc['name']),
                        args=check.isinstance(raw_fc.get('args') or {}, ta.Mapping),
                        backend_signature=check.isinstance(raw_part.get('thoughtSignature'), (str, None)),
                    ))

                else:
                    raise ValueError(raw_part)

        return AiMessage(
            ta.cast(ta.Any, content),
        )
