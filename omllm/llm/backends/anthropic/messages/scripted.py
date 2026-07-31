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


def _render_stop_reason(response: ScriptedHttpResponse) -> str:
    return {
        'stop': 'end_turn',
        'length': 'max_tokens',
        'tool_use': 'tool_use',
        'error': 'refusal',
    }[response.resolved_stop_reason()]


def _render_usage(usage: ScriptedUsage) -> dict[str, int]:
    return {
        'input_tokens': usage.uncached_input_tokens,
        'output_tokens': usage.output_tokens,
        'cache_read_input_tokens': usage.cache_read_tokens,
        'cache_creation_input_tokens': usage.cache_write_tokens,
    }


def _thinking_signature(content: ThinkingContent, response_index: int, content_index: int) -> str:
    return content.backend_signature or f'sig_scripted_{response_index}_{content_index}'


##


def _normalize_content_blocks(value: ta.Any) -> ta.Any:
    if isinstance(value, str):
        return [{'type': 'text', 'text': value}]
    return value


def _has_cache_control(value: ta.Any) -> bool:
    if isinstance(value, dict):
        return 'cache_control' in value or any(_has_cache_control(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_cache_control(item) for item in value)
    return False


def _serialize_prompt(payload: ta.Mapping[str, ta.Any]) -> str:
    messages = []
    for message in strip_cache_controls(payload.get('messages')) or []:
        messages.append({
            **message,
            'content': _normalize_content_blocks(message.get('content')),
        })

    return json.dumps_compact({
        'tools': strip_cache_controls(payload.get('tools')),
        'system': _normalize_content_blocks(strip_cache_controls(payload.get('system'))),
        'messages': messages,
    })


##


class AnthropicMessagesScriptedHttpClient(BaseScriptedHttpClient):
    def _validate_request(
            self,
            request: http.HttpClientRequest,
            headers: http.HttpHeaders,
            payload: ta.Mapping[str, ta.Any],
    ) -> ScriptedHttpValidationError | None:
        if not request.url.rstrip('/').endswith('/messages'):
            return ScriptedHttpValidationError(
                status=404,
                error_type='not_found_error',
                message=f'unknown path: {request.url}',
            )

        if self._require_auth and not (
                headers.single.get('x-api-key') or
                headers.single.get('authorization', '').startswith('Bearer ')
        ):
            return ScriptedHttpValidationError(
                status=401,
                error_type='authentication_error',
                message='missing x-api-key or bearer authorization',
            )

        if not headers.single.get('anthropic-version'):
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing anthropic-version header',
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
        if not isinstance(payload.get('max_tokens'), int) or payload['max_tokens'] <= 0:
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing max_tokens',
            )
        if 'stream' in payload and not isinstance(payload['stream'], bool):
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='invalid stream mode',
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
                'type': 'error',
                'error': {
                    'type': error_type,
                    'message': message,
                },
            }),
        )

    def _cache_key_and_prompt(self, request: RecordedHttpRequest) -> tuple[str | None, str]:
        payload = request.payload
        return (
            f'anthropic:{payload["model"]}' if _has_cache_control(payload) else None,
            _serialize_prompt(payload),
        )

    def _render_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        if request.payload.get('stream'):
            return self._render_stream_response(request, response, usage, response_index)
        return self._render_immediate_response(request, response, usage, response_index)

    def _response_identity(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            response_index: int,
    ) -> tuple[str, str]:
        return (
            response.response_id or f'msg_scripted_{response_index}',
            response.model or check.non_empty_str(request.payload['model']),
        )

    def _render_content(
            self,
            response: ScriptedHttpResponse,
            response_index: int,
    ) -> list[dict[str, ta.Any]]:
        raw_content: list[dict[str, ta.Any]] = []

        for content_index, content in enumerate(response.content):
            if isinstance(content, TextContent):
                raw_content.append({
                    'type': 'text',
                    'text': content.text,
                })

            elif isinstance(content, ThinkingContent):
                if content.redacted:
                    raw_content.append({
                        'type': 'redacted_thinking',
                        'data': _thinking_signature(content, response_index, content_index),
                    })
                else:
                    raw_content.append({
                        'type': 'thinking',
                        'thinking': content.text,
                        'signature': _thinking_signature(content, response_index, content_index),
                    })

            elif isinstance(content, ToolCall):
                raw_content.append({
                    'type': 'tool_use',
                    'id': content.id,
                    'name': content.name,
                    'input': content.args,
                })

            else:
                raise TypeError(content)

        return raw_content

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
                'id': response_id,
                'type': 'message',
                'role': 'assistant',
                'model': model,
                'content': self._render_content(response, response_index),
                'stop_reason': _render_stop_reason(response),
                'stop_sequence': None,
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

        def event(name: str, body: ta.Mapping[str, ta.Any]) -> str:
            return f'event: {name}\ndata: {json.dumps(body)}\n\n'

        raw_message: dict[str, ta.Any] = {
            'id': response_id,
            'type': 'message',
            'role': 'assistant',
            'model': model,
            'content': [],
            'stop_reason': None,
        }
        if usage is not None:
            raw_message['usage'] = {
                **_render_usage(usage),
                'output_tokens': min(1, usage.output_tokens),
            }

        out = [event('message_start', {
            'type': 'message_start',
            'message': raw_message,
        })]

        for content_index, content in enumerate(response.content):
            if isinstance(content, TextContent):
                out.append(event('content_block_start', {
                    'type': 'content_block_start',
                    'index': content_index,
                    'content_block': {'type': 'text', 'text': ''},
                }))
                out.extend(
                    event('content_block_delta', {
                        'type': 'content_block_delta',
                        'index': content_index,
                        'delta': {'type': 'text_delta', 'text': piece},
                    })
                    for piece in split_script_text(content.text, response.chunk_chars)
                )
                out.append(event('content_block_stop', {
                    'type': 'content_block_stop',
                    'index': content_index,
                }))

            elif isinstance(content, ThinkingContent):
                signature = _thinking_signature(content, response_index, content_index)

                if content.redacted:
                    raw_block = {
                        'type': 'redacted_thinking',
                        'data': signature,
                    }
                else:
                    raw_block = {
                        'type': 'thinking',
                        'thinking': '',
                    }

                out.append(event('content_block_start', {
                    'type': 'content_block_start',
                    'index': content_index,
                    'content_block': raw_block,
                }))

                if not content.redacted:
                    out.extend(
                        event('content_block_delta', {
                            'type': 'content_block_delta',
                            'index': content_index,
                            'delta': {'type': 'thinking_delta', 'thinking': piece},
                        })
                        for piece in split_script_text(content.text, response.chunk_chars)
                    )
                    out.append(event('content_block_delta', {
                        'type': 'content_block_delta',
                        'index': content_index,
                        'delta': {'type': 'signature_delta', 'signature': signature},
                    }))

                out.append(event('content_block_stop', {
                    'type': 'content_block_stop',
                    'index': content_index,
                }))

            elif isinstance(content, ToolCall):
                out.append(event('content_block_start', {
                    'type': 'content_block_start',
                    'index': content_index,
                    'content_block': {
                        'type': 'tool_use',
                        'id': content.id,
                        'name': content.name,
                        'input': {},
                    },
                }))
                raw_args = json.dumps(content.args)
                out.extend(
                    event('content_block_delta', {
                        'type': 'content_block_delta',
                        'index': content_index,
                        'delta': {'type': 'input_json_delta', 'partial_json': piece},
                    })
                    for piece in split_script_text(raw_args, response.chunk_chars)
                )
                out.append(event('content_block_stop', {
                    'type': 'content_block_stop',
                    'index': content_index,
                }))

            else:
                raise TypeError(content)

        message_delta: dict[str, ta.Any] = {
            'type': 'message_delta',
            'delta': {'stop_reason': _render_stop_reason(response)},
        }
        if usage is not None:
            message_delta['usage'] = {'output_tokens': usage.output_tokens}
        out.append(event('message_delta', message_delta))
        out.append(event('message_stop', {'type': 'message_stop'}))

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'text/event-stream'},
            body=''.join(out),
        )
