import typing as ta

from omcore import check
from omcore.formats.json import all as json
from omcore.http import all as http

from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ...scripted.caching import strip_cache_controls
from ...scripted.clients import BaseScriptedHttpClient
from ...scripted.http import RecordedHttpRequest
from ...scripted.http import ScriptedHttpResponse
from ...scripted.http import ScriptedHttpValidationError
from ...scripted.http import ScriptedRenderedHttpResponse
from ...scripted.http import ScriptedUsage
from ...scripted.scripts import split_script_text


##


def _request_model(url: str) -> str:
    marker = '/models/'
    try:
        tail = url.split(marker, 1)[1]
    except IndexError:
        raise ValueError(url) from None
    return check.non_empty_str(tail.split(':', 1)[0])


def _render_stop_reason(response: ScriptedHttpResponse) -> str:
    return {
        'stop': 'STOP',
        'length': 'MAX_TOKENS',
        'tool_use': 'STOP',
        'error': 'OTHER',
    }[response.resolved_stop_reason()]


def _render_usage(usage: ScriptedUsage) -> dict[str, int]:
    prompt_tokens = (
        usage.uncached_input_tokens +
        usage.cache_read_tokens +
        usage.cache_write_tokens
    )
    reasoning_tokens = usage.reasoning_tokens or 0
    check.arg(reasoning_tokens <= usage.output_tokens)
    candidate_tokens = usage.output_tokens - reasoning_tokens

    return {
        'promptTokenCount': prompt_tokens,
        'candidatesTokenCount': candidate_tokens,
        **(
            {'thoughtsTokenCount': usage.reasoning_tokens}
            if usage.reasoning_tokens is not None
            else {}
        ),
        'cachedContentTokenCount': usage.cache_read_tokens,
        'totalTokenCount': (
            usage.total_tokens
            if usage.total_tokens is not None
            else prompt_tokens + usage.output_tokens
        ),
    }


##


class GoogleGenerativeScriptedHttpClient(BaseScriptedHttpClient):
    def _validate_request(
            self,
            request: http.HttpClientRequest,
            headers: http.HttpHeaders,
            payload: ta.Mapping[str, ta.Any],
    ) -> ScriptedHttpValidationError | None:
        if not (
                request.url.endswith(':generateContent') or
                ':streamGenerateContent' in request.url
        ):
            return ScriptedHttpValidationError(
                status=404,
                error_type='NOT_FOUND',
                message=f'unknown path: {request.url}',
            )

        try:
            _request_model(request.url)
        except ValueError:
            return ScriptedHttpValidationError(
                status=400,
                error_type='INVALID_ARGUMENT',
                message='missing model in URL',
            )

        if self._require_auth and not headers.single.get('x-goog-api-key'):
            return ScriptedHttpValidationError(
                status=401,
                error_type='UNAUTHENTICATED',
                message='missing x-goog-api-key',
            )

        if not isinstance(payload.get('contents'), list) or not payload['contents']:
            return ScriptedHttpValidationError(
                status=400,
                error_type='INVALID_ARGUMENT',
                message='missing contents',
            )

        return None

    def _render_error(
            self,
            *,
            status: int,
            error_type: str,
            message: str,
    ) -> ScriptedRenderedHttpResponse:
        return ScriptedRenderedHttpResponse(
            status=status,
            headers={'content-type': 'application/json'},
            body=json.dumps({
                'error': {
                    'code': status,
                    'status': error_type,
                    'message': message,
                },
            }),
        )

    def _cache_key_and_prompt(self, request: RecordedHttpRequest) -> tuple[str | None, str]:
        payload = request.payload
        cached_content = check.isinstance(payload.get('cachedContent'), (str, None))
        return (
            (
                f'google:{_request_model(request.url)}:{cached_content}'
                if cached_content
                else None
            ),
            json.dumps_compact({
                'tools': strip_cache_controls(payload.get('tools')),
                'systemInstruction': strip_cache_controls(payload.get('systemInstruction')),
                'contents': strip_cache_controls(payload.get('contents')),
            }),
        )

    def _render_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        if ':streamGenerateContent' in request.url:
            return self._render_stream_response(request, response, usage, response_index)
        return self._render_immediate_response(request, response, usage, response_index)

    def _response_identity(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            response_index: int,
    ) -> tuple[str, str]:
        return (
            response.response_id or f'response-scripted-{response_index}',
            response.model or _request_model(request.url),
        )

    def _render_part(self, content: ta.Any) -> dict[str, ta.Any]:
        if isinstance(content, ThinkingContent):
            return {
                'thought': True,
                'text': content.text,
                **({'thoughtSignature': content.backend_signature} if content.backend_signature else {}),
            }

        if isinstance(content, TextContent):
            return {
                'text': content.text,
                **({'thoughtSignature': content.backend_signature} if content.backend_signature else {}),
            }

        if isinstance(content, ToolCall):
            return {
                'functionCall': {
                    'id': content.id,
                    'name': content.name,
                    'args': content.args,
                },
                **({'thoughtSignature': content.backend_signature} if content.backend_signature else {}),
            }

        raise TypeError(content)

    def _render_immediate_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        response_id, model = self._response_identity(request, response, response_index)

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'application/json'},
            body=json.dumps({
                'responseId': response_id,
                'modelVersion': model,
                'candidates': [{
                    'index': 0,
                    'content': {
                        'role': 'model',
                        'parts': [self._render_part(content) for content in response.content],
                    },
                    'finishReason': _render_stop_reason(response),
                }],
                **({'usageMetadata': _render_usage(usage)} if usage is not None else {}),
            }),
        )

    def _render_stream_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        response_id, model = self._response_identity(request, response, response_index)

        def chunk(
                *,
                part: ta.Mapping[str, ta.Any] | None = None,
                finish_reason: str | None = None,
                raw_usage: ta.Mapping[str, ta.Any] | None = None,
        ) -> str:
            candidate: dict[str, ta.Any] = {'index': 0}
            if part is not None:
                candidate['content'] = {
                    'role': 'model',
                    'parts': [part],
                }
            if finish_reason is not None:
                candidate['finishReason'] = finish_reason

            return f'data: {json.dumps({
                "responseId": response_id,
                "modelVersion": model,
                "candidates": [candidate],
                **({"usageMetadata": raw_usage} if raw_usage is not None else {}),
            })}\n\n'

        out: list[str] = []

        for content in response.content:
            if isinstance(content, ThinkingContent):
                pieces = split_script_text(content.text, response.chunk_chars)
                for piece_index, piece in enumerate(pieces):
                    out.append(chunk(part={
                        'thought': True,
                        'text': piece,
                        **(
                            {'thoughtSignature': content.backend_signature}
                            if content.backend_signature and piece_index == len(pieces) - 1
                            else {}
                        ),
                    }))
                if not pieces and content.backend_signature:
                    out.append(chunk(part={
                        'thought': True,
                        'text': '',
                        'thoughtSignature': content.backend_signature,
                    }))

            elif isinstance(content, TextContent):
                pieces = split_script_text(content.text, response.chunk_chars)
                for piece_index, piece in enumerate(pieces):
                    out.append(chunk(part={
                        'text': piece,
                        **(
                            {'thoughtSignature': content.backend_signature}
                            if content.backend_signature and piece_index == len(pieces) - 1
                            else {}
                        ),
                    }))
                if not pieces and content.backend_signature:
                    out.append(chunk(part={
                        'text': '',
                        'thoughtSignature': content.backend_signature,
                    }))

            elif isinstance(content, ToolCall):
                out.append(chunk(part=self._render_part(content)))

            else:
                raise TypeError(content)

        out.append(chunk(
            finish_reason=_render_stop_reason(response),
            raw_usage=_render_usage(usage) if usage is not None else None,
        ))

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'text/event-stream'},
            body=''.join(out),
        )
