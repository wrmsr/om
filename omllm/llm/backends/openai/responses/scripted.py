import typing as ta

from omcore import check
from omcore.formats.json import all as json
from omcore.http import all as http

from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ...scripted.clients import BaseScriptedHttpClient
from ...scripted.http import RecordedHttpRequest
from ...scripted.http import ScriptedHttpResponse
from ...scripted.http import ScriptedHttpValidationError
from ...scripted.http import ScriptedRenderedHttpResponse
from ...scripted.http import ScriptedUsage
from ...scripted.scripts import split_script_text


##


def _render_usage(usage: ScriptedUsage) -> dict[str, ta.Any]:
    input_tokens = (
        usage.uncached_input_tokens +
        usage.cache_read_tokens +
        usage.cache_write_tokens
    )

    return {
        'input_tokens': input_tokens,
        'input_tokens_details': {
            'cached_tokens': usage.cache_read_tokens,
            'cache_write_tokens': usage.cache_write_tokens,
        },
        'output_tokens': usage.output_tokens,
        **(
            {'output_tokens_details': {'reasoning_tokens': usage.reasoning_tokens}}
            if usage.reasoning_tokens is not None
            else {}
        ),
        'total_tokens': (
            usage.total_tokens
            if usage.total_tokens is not None
            else input_tokens + usage.output_tokens
        ),
    }


def _render_status(response: ScriptedHttpResponse) -> tuple[str, dict[str, ta.Any] | None]:
    stop_reason = response.resolved_stop_reason()

    if stop_reason in ('stop', 'tool_use'):
        return ('completed', None)
    elif stop_reason == 'length':
        return ('incomplete', {'reason': 'max_output_tokens'})
    elif stop_reason == 'error':
        return ('incomplete', {'reason': 'content_filter'})
    else:
        raise ValueError(stop_reason)


##


class OpenaiResponsesScriptedHttpClient(BaseScriptedHttpClient):
    def _validate_request(
            self,
            request: http.HttpClientRequest,
            headers: http.HttpHeaders,
            payload: ta.Mapping[str, ta.Any],
    ) -> ScriptedHttpValidationError | None:
        if not request.url.rstrip('/').endswith('/responses'):
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
        if not isinstance(payload.get('input'), list) or not payload['input']:
            return ScriptedHttpValidationError(
                status=400,
                error_type='invalid_request_error',
                message='missing input',
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
                'instructions': payload.get('instructions'),
                'tools': payload.get('tools'),
                'input': payload.get('input'),
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
            response.response_id or f'resp_scripted_{response_index}',
            response.model or check.non_empty_str(request.payload['model']),
        )

    def _render_output_items(
            self,
            response: ScriptedHttpResponse,
            response_index: int,
    ) -> list[dict[str, ta.Any]]:
        raw_items: list[dict[str, ta.Any]] = []

        for i, content in enumerate(response.content):
            if isinstance(content, ThinkingContent):
                raw_items.append({
                    'id': f'rs_scripted_{response_index}_{i}',
                    'type': 'reasoning',
                    'summary': (
                        [{'type': 'summary_text', 'text': content.text}]
                        if content.text
                        else []
                    ),
                    'content': [],
                    'encrypted_content': f'scripted-encrypted-{response_index}-{i}',
                })

            elif isinstance(content, TextContent):
                raw_items.append({
                    'id': f'msg_scripted_{response_index}_{i}',
                    'type': 'message',
                    'status': 'completed',
                    'role': 'assistant',
                    'phase': 'final_answer',
                    'content': [{
                        'type': 'output_text',
                        'annotations': [],
                        'text': content.text,
                    }],
                })

            elif isinstance(content, ToolCall):
                raw_items.append({
                    'id': f'fc_scripted_{response_index}_{i}',
                    'type': 'function_call',
                    'status': 'completed',
                    'call_id': content.id,
                    'name': content.name,
                    'arguments': json.dumps(content.args),
                })

            else:
                raise TypeError(content)

        return raw_items

    def _render_raw_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
            *,
            status: str,
            raw_incomplete_details: dict[str, ta.Any] | None,
            raw_items: list[dict[str, ta.Any]],
    ) -> dict[str, ta.Any]:
        response_id, model = self._response_identity(request, response, response_index)

        return {
            'id': response_id,
            'object': 'response',
            'model': model,
            'status': status,
            'error': None,
            'incomplete_details': raw_incomplete_details,
            'output': raw_items,
            **({'usage': _render_usage(usage)} if usage is not None else {}),
        }

    def _render_immediate_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        status, raw_incomplete_details = _render_status(response)

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'application/json'},
            body=json.dumps(self._render_raw_response(
                request,
                response,
                usage,
                response_index,
                status=status,
                raw_incomplete_details=raw_incomplete_details,
                raw_items=self._render_output_items(response, response_index),
            )),
        )

    def _render_stream_response(
            self,
            request: RecordedHttpRequest,
            response: ScriptedHttpResponse,
            usage: ScriptedUsage | None,
            response_index: int,
    ) -> ScriptedRenderedHttpResponse:
        response_id, model = self._response_identity(request, response, response_index)

        def sse(raw_event: ta.Mapping[str, ta.Any]) -> str:
            return f'event: {raw_event["type"]}\ndata: {json.dumps(raw_event)}\n\n'

        out = [
            sse({
                'type': raw_event_type,
                'response': {'id': response_id, 'model': model, 'status': 'in_progress'},
            })
            for raw_event_type in ('response.created', 'response.in_progress')
        ]

        raw_items = self._render_output_items(response, response_index)

        for output_index, (content, raw_item) in enumerate(zip(response.content, raw_items)):
            raw_item_id = raw_item['id']

            if isinstance(content, ThinkingContent):
                # The added-time item is deliberately not the final form - real streams only carry complete encrypted
                # content and summaries on the done-time item.
                out.append(sse({
                    'type': 'response.output_item.added',
                    'output_index': output_index,
                    'item': {**raw_item, 'summary': [], 'encrypted_content': None},
                }))

                if content.text:
                    out.append(sse({
                        'type': 'response.reasoning_summary_part.added',
                        'output_index': output_index,
                        'item_id': raw_item_id,
                        'summary_index': 0,
                        'part': {'type': 'summary_text', 'text': ''},
                    }))
                    out.extend(
                        sse({
                            'type': 'response.reasoning_summary_text.delta',
                            'output_index': output_index,
                            'item_id': raw_item_id,
                            'summary_index': 0,
                            'delta': piece,
                        })
                        for piece in split_script_text(content.text, response.chunk_chars)
                    )
                    out.append(sse({
                        'type': 'response.reasoning_summary_part.done',
                        'output_index': output_index,
                        'item_id': raw_item_id,
                        'summary_index': 0,
                        'part': {'type': 'summary_text', 'text': content.text},
                    }))

            elif isinstance(content, TextContent):
                out.append(sse({
                    'type': 'response.output_item.added',
                    'output_index': output_index,
                    'item': {**raw_item, 'status': 'in_progress', 'content': []},
                }))

                out.append(sse({
                    'type': 'response.content_part.added',
                    'output_index': output_index,
                    'item_id': raw_item_id,
                    'content_index': 0,
                    'part': {'type': 'output_text', 'annotations': [], 'text': ''},
                }))
                out.extend(
                    sse({
                        'type': 'response.output_text.delta',
                        'output_index': output_index,
                        'item_id': raw_item_id,
                        'content_index': 0,
                        'delta': piece,
                    })
                    for piece in split_script_text(content.text, response.chunk_chars)
                )
                out.append(sse({
                    'type': 'response.content_part.done',
                    'output_index': output_index,
                    'item_id': raw_item_id,
                    'content_index': 0,
                    'part': {'type': 'output_text', 'annotations': [], 'text': content.text},
                }))

            elif isinstance(content, ToolCall):
                out.append(sse({
                    'type': 'response.output_item.added',
                    'output_index': output_index,
                    'item': {**raw_item, 'status': 'in_progress', 'arguments': ''},
                }))

                raw_args = json.dumps(content.args)
                out.extend(
                    sse({
                        'type': 'response.function_call_arguments.delta',
                        'output_index': output_index,
                        'item_id': raw_item_id,
                        'delta': piece,
                    })
                    for piece in split_script_text(raw_args, response.chunk_chars)
                )
                out.append(sse({
                    'type': 'response.function_call_arguments.done',
                    'output_index': output_index,
                    'item_id': raw_item_id,
                    'arguments': raw_args,
                }))

            else:
                raise TypeError(content)

            out.append(sse({
                'type': 'response.output_item.done',
                'output_index': output_index,
                'item': raw_item,
            }))

        status, raw_incomplete_details = _render_status(response)

        out.append(sse({
            'type': 'response.completed' if status == 'completed' else 'response.incomplete',
            'response': self._render_raw_response(
                request,
                response,
                usage,
                response_index,
                status=status,
                raw_incomplete_details=raw_incomplete_details,
                raw_items=raw_items,
            ),
        }))

        return ScriptedRenderedHttpResponse(
            headers={'content-type': 'text/event-stream'},
            body=''.join(out),
        )
