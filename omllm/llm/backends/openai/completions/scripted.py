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


def _render_usage(usage: ScriptedUsage) -> dict[str, ta.Any]:
    prompt_tokens = (
        usage.uncached_input_tokens +
        usage.cache_read_tokens +
        usage.cache_write_tokens
    )

    return {
        'prompt_tokens': prompt_tokens,
        'completion_tokens': usage.output_tokens,
        'total_tokens': (
            usage.total_tokens
            if usage.total_tokens is not None
            else prompt_tokens + usage.output_tokens
        ),
        'prompt_tokens_details': {
            'cached_tokens': usage.cache_read_tokens,
            **(
                {'cache_write_tokens': usage.cache_write_tokens}
                if usage.cache_write_tokens
                else {}
            ),
        },
        **(
            {'completion_tokens_details': {'reasoning_tokens': usage.reasoning_tokens}}
            if usage.reasoning_tokens is not None
            else {}
        ),
    }


def _render_stop_reason(response: ScriptedHttpResponse) -> str:
    return {
        'stop': 'stop',
        'length': 'length',
        'tool_use': 'tool_calls',
        'error': 'content_filter',
    }[response.resolved_stop_reason()]


##


class OpenaiCompletionsScriptedHttpClient(BaseScriptedHttpClient):
    def _validate_request(
            self,
            request: http.HttpClientRequest,
            headers: http.HttpHeaders,
            payload: ta.Mapping[str, ta.Any],
    ) -> ScriptedHttpValidationError | None:
        if not request.url.rstrip('/').endswith('/chat/completions'):
            return ScriptedHttpValidationError(
                status=404,
                error_type='not_found_error',
                message=f'unknown path: {request.url}',
            )

        if self._require_auth and not headers.single.get('authorization', '').startswith('Bearer '):
            return ScriptedHttpValidationError(
                status=401,
                error_type='authentication_error',
                message='missing bearer authorization',
            )

        if not payload.get('model'):
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing model',
            )
        if not isinstance(payload.get('messages'), list) or not payload['messages']:
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing messages',
            )
        if not isinstance(payload.get('stream'), bool):
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing stream mode',
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
                    'type': error_type,
                    'message': message,
                },
            }),
        )

    def _cache_key_and_prompt(self, request: RecordedHttpRequest) -> tuple[str | None, str]:
        payload = request.payload
        return (
            check.isinstance(payload.get('prompt_cache_key'), (str, None)) or None,
            json.dumps_compact({
                'tools': strip_cache_controls(payload.get('tools')),
                'messages': strip_cache_controls(payload.get('messages')),
            }),
        )

    def _render_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        if request.payload['stream']:
            return self._render_stream_response(request, response, usage, response_index)
        return self._render_immediate_response(request, response, usage, response_index)

    def _response_identity(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            response_index: int,
    ) -> tuple[str, str]:
        return (
            response.response_id or f'chatcmpl-scripted-{response_index}',
            response.model or check.non_empty_str(request.payload['model']),
        )

    def _render_immediate_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        response_id, model = self._response_identity(request, response, response_index)

        text = ''.join(content.text for content in response.content if isinstance(content, TextContent))
        thinking = ''.join(content.text for content in response.content if isinstance(content, ThinkingContent))

        raw_tool_calls = []
        for content in response.content:
            if isinstance(content, ToolCall):
                raw_tool_calls.append({
                    'type': 'function',
                    'id': content.id,
                    'function': {
                        'name': content.name,
                        'arguments': json.dumps(content.args),
                    },
                })

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'application/json'},
            body=json.dumps({
                'id': response_id,
                'object': 'chat.completion',
                'model': model,
                'choices': [{
                    'index': 0,
                    'message': {
                        'role': 'assistant',
                        'content': text or None,
                        **({'reasoning_content': thinking} if thinking else {}),
                        **({'tool_calls': raw_tool_calls} if raw_tool_calls else {}),
                    },
                    'finish_reason': _render_stop_reason(response),
                }],
                **({'usage': _render_usage(usage)} if usage is not None else {}),
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
                delta: ta.Mapping[str, ta.Any] | None,
                *,
                finish_reason: str | None = None,
                raw_usage: ta.Mapping[str, ta.Any] | None = None,
        ) -> str:
            body: dict[str, ta.Any] = {
                'id': response_id,
                'object': 'chat.completion.chunk',
                'model': model,
                'choices': [],
            }
            if delta is not None or finish_reason is not None:
                body['choices'] = [{
                    'index': 0,
                    'delta': delta if delta is not None else {},
                    'finish_reason': finish_reason,
                }]
            if raw_usage is not None:
                body['usage'] = raw_usage
            return f'data: {json.dumps(body)}\n\n'

        out = [chunk({'role': 'assistant', 'content': ''})]

        tool_index = 0
        for content in response.content:
            if isinstance(content, ThinkingContent):
                out.extend(
                    chunk({'reasoning_content': piece})
                    for piece in split_script_text(content.text, response.chunk_chars)
                )

            elif isinstance(content, TextContent):
                out.extend(
                    chunk({'content': piece})
                    for piece in split_script_text(content.text, response.chunk_chars)
                )

            elif isinstance(content, ToolCall):
                out.append(chunk({
                    'tool_calls': [{
                        'index': tool_index,
                        'id': content.id,
                        'type': 'function',
                        'function': {
                            'name': content.name,
                            'arguments': '',
                        },
                    }],
                }))

                raw_args = json.dumps(content.args)
                out.extend(
                    chunk({
                        'tool_calls': [{
                            'index': tool_index,
                            'function': {'arguments': piece},
                        }],
                    })
                    for piece in split_script_text(raw_args, response.chunk_chars)
                )
                tool_index += 1

            else:
                raise TypeError(content)

        out.append(chunk(None, finish_reason=_render_stop_reason(response)))

        if usage is not None and bool((request.payload.get('stream_options') or {}).get('include_usage')):
            out.append(chunk(None, raw_usage=_render_usage(usage)))

        out.append('data: [DONE]\n\n')

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'text/event-stream'},
            body=''.join(out),
        )
