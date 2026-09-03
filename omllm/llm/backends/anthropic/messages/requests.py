import typing as ta

from omcore import check
from omcore import lang

from ....tools.jsonschema import build_tool_params_json_schema
from ....types.compat import OpenaiCompletionsCompat
from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.messages import AiMessage
from ....types.messages import ToolResultMessage
from ....types.messages import UserMessage
from ....types.models import Model
from ....types.options import CacheRetention
from ....types.options import Options


##


_CACHE_RETENTIONS: ta.Final[ta.Mapping[CacheRetention, str]] = {
    CacheRetention.FIVE_MINUTES: '5m',
    CacheRetention.ONE_HOUR: '1h',
}


##


class RequestPreparer:
    def __init__(
            self,
            model: Model,
            context: Context,
            options: Options | None = None,
    ) -> None:
        super().__init__()

        self._model = model
        self._context = context
        self._given_options = options

        self._options = Options().merge(
            model.default_options,
            options,
        )

        if model.compat is not None:
            self._compat = check.isinstance(model.compat, OpenaiCompletionsCompat)
        else:
            self._compat = OpenaiCompletionsCompat()

    def _add_cache_options(self, raw_request: dict[str, ta.Any]) -> None:
        if self._options.cache_key is not None:
            raise ValueError(f'Model does not support caller-supplied prompt cache keys: {self._model.key!r}')

        cache_retention = self._options.cache_retention
        if cache_retention is None:
            # Unlike OpenAI and Gemini, Anthropic caching is disabled unless cache_control is present.
            return

        cache = self._model.cache
        if (
                cache is None or
                cache.control_style != 'anthropic' or
                cache_retention not in (cache.retentions or ())
        ):
            raise ValueError(
                f'Model does not support cache retention {cache_retention.name}: {self._model.key!r}',
            )

        # Top-level cache_control enables Anthropic's automatic moving breakpoint. Explicit per-block breakpoints are
        # intentionally left for a future content model which can represent them without provider-specific options.
        raw_request['cache_control'] = {
            'type': 'ephemeral',
            'ttl': _CACHE_RETENTIONS[cache_retention],
        }

    @lang.cached_function
    def raw_request(self) -> dict[str, ta.Any]:
        raw_request: dict = {
            'model': self._model.key_.id,
        }

        if self._options.max_tokens is not None:
            raw_request['max_tokens'] = self._options.max_tokens

        if self._options.thinking:
            raw_request['thinking'] = {'type': 'adaptive'}

        self._add_cache_options(raw_request)

        #

        raw_messages: list[dict] = []

        if self._context.system_prompt:
            raw_request['system'] = [{
                'type': 'text',
                'text': self._context.system_prompt,
            }]

        for msg in self._context.messages or []:
            if isinstance(msg, UserMessage):
                if isinstance(msg.content, str):
                    raw_messages.append({
                        'role': 'user',
                        'content': msg.content,
                    })

                elif isinstance(msg.content, TextContent):
                    raw_messages.append({
                        'role': 'user',
                        'content': msg.content.text,
                    })

                else:
                    raise TypeError(msg)

            elif isinstance(msg, AiMessage):
                raw_content: list[dict] = []

                for c in msg.content:
                    if isinstance(c, TextContent):
                        # Empty text blocks are rejected.
                        if c.text:
                            raw_content.append({
                                'type': 'text',
                                'text': c.text,
                            })

                    elif isinstance(c, ThinkingContent):
                        # Signed thinking blocks must be replayed verbatim for validity in subsequent tool use. Unsigned
                        # ones (such as from a different backend) cannot be replayed, and are dropped. For redacted
                        # blocks the opaque data blob rides backend_signature, and the placeholder text is not sent.
                        if c.redacted:
                            if c.backend_signature:
                                raw_content.append({
                                    'type': 'redacted_thinking',
                                    'data': c.backend_signature,
                                })

                        elif c.backend_signature:
                            raw_content.append({
                                'type': 'thinking',
                                'thinking': c.text,
                                'signature': c.backend_signature,
                            })

                    elif isinstance(c, ToolCall):
                        raw_content.append({
                            'type': 'tool_use',
                            'id': c.id,
                            'name': c.name,
                            'input': c.args,
                        })

                    else:
                        raise TypeError(c)

                raw_messages.append({
                    'role': 'assistant',
                    'content': raw_content,
                })

            elif isinstance(msg, ToolResultMessage):
                raw_messages.append({
                    'role': 'user',
                    'content': [{
                        'type': 'tool_result',
                        'tool_use_id': msg.tool_call_id,
                        'content': '\n'.join([c.text for c in msg.content]),
                        **({'is_error': True} if msg.is_error else {}),
                    }],
                })

            else:
                raise TypeError(msg)

        raw_request['messages'] = raw_messages

        #

        if self._context.tools:
            raw_tools: list[dict] = []

            for tool in self._context.tools:
                raw_tools.append({
                    'name': tool.name,
                    **({'description': tool.description} if tool.description else {}),
                    'input_schema': build_tool_params_json_schema(tool),
                })

            raw_request['tools'] = raw_tools

        #

        return raw_request
