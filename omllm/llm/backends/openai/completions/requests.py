import typing as ta

from omcore import check
from omcore import lang
from omcore.formats.json import all as json

from ....tools.jsonschema import build_tool_json_schema
from ....types.compat import OpenaiCompat
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


_LEGACY_CACHE_RETENTIONS: ta.Final[ta.Mapping[CacheRetention, str]] = {
    CacheRetention.IN_MEMORY: 'in_memory',
    CacheRetention.ONE_DAY: '24h',
}

_TTL_CACHE_RETENTIONS: ta.Final[ta.Mapping[CacheRetention, str]] = {
    CacheRetention.THIRTY_MINUTES: '30m',
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
            self._compat = check.isinstance(model.compat, OpenaiCompat)
        else:
            self._compat = OpenaiCompat()

    def _add_cache_options(self, raw_request: dict[str, ta.Any]) -> None:
        cache_key = self._options.cache_key
        cache_retention = self._options.cache_retention
        if cache_key is None and cache_retention is None:
            return

        cache = self._model.cache
        if cache is None or cache.control_style not in ('openai_legacy', 'openai_ttl', 'openrouter'):
            raise ValueError(f'Model does not support OpenAI prompt cache controls: {self._model.key!r}')

        if cache_key is not None:
            if not cache.key:
                raise ValueError(f'Model does not support prompt cache keys: {self._model.key!r}')

            if cache.control_style == 'openrouter':
                # Translated to a session affinity header instead - see raw_headers.
                pass

            else:
                raw_request['prompt_cache_key'] = check.non_empty_str(cache_key)

        if cache_retention is not None:
            if cache_retention not in cache.retentions:
                raise ValueError(f'Model does not support cache retention {cache_retention.name}: {self._model.key!r}')

            if cache.control_style == 'openai_legacy':
                raw_request['prompt_cache_retention'] = _LEGACY_CACHE_RETENTIONS[cache_retention]

            elif cache.control_style == 'openai_ttl':
                # The implicit mode remains in use. Explicit breakpoints require block-level content metadata and are
                # intentionally left for a future content model which can represent them generically.
                raw_request['prompt_cache_options'] = {
                    'ttl': _TTL_CACHE_RETENTIONS[cache_retention],
                }

            else:
                raise RuntimeError(cache.control_style)

    @lang.cached_function
    def raw_request(self) -> dict[str, ta.Any]:
        raw_request: dict = {
            'model': self._model.key.id,
        }

        if self._options.max_tokens is not None:
            raw_request[self._compat.max_tokens_field or 'max_completion_tokens'] = self._options.max_tokens

        self._add_cache_options(raw_request)

        #

        raw_messages: list[dict] = []

        if self._context.system_prompt:
            raw_messages.append({
                'role': 'system',
                'content': self._context.system_prompt,
            })

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
                text_parts: list[str] = []
                raw_tool_calls: list[dict] = []

                for c in msg.content:
                    if isinstance(c, TextContent):
                        text_parts.append(c.text)

                    elif isinstance(c, ThinkingContent):
                        # The api has no representation for replayed thinking.
                        pass

                    elif isinstance(c, ToolCall):
                        raw_tool_calls.append({
                            'type': 'function',
                            'id': c.id,
                            'function': {
                                'name': c.name,
                                'arguments': json.dumps(c.args),
                            },
                        })

                    else:
                        raise TypeError(c)

                raw_messages.append({
                    'role': 'assistant',
                    'content': ''.join(text_parts),
                    **({'tool_calls': raw_tool_calls} if raw_tool_calls else {}),
                })

            elif isinstance(msg, ToolResultMessage):
                raw_messages.append({
                    'role': 'tool',
                    'tool_call_id': msg.tool_call_id,
                    'content': '\n'.join([c.text for c in msg.content]),
                })

            else:
                raise TypeError(msg)

        raw_request['messages'] = raw_messages

        #

        if self._context.tools:
            raw_tools: list[dict] = []

            for tool in self._context.tools:
                raw_properties: dict = {}
                raw_required: list[str] = []
                for param in tool.params or []:
                    raw_properties[param.name] = {
                        **({'type': param.type} if param.type else {}),
                        **({'description': param.description} if param.description else {}),
                    }
                    if not param.optional:
                        raw_required.append(param.name)

                raw_tools.append({
                    'type': 'function',
                    'function': build_tool_json_schema(tool),
                })

            raw_request['tools'] = raw_tools

        #

        return raw_request

    @lang.cached_function
    def raw_headers(self) -> ta.Mapping[str, str]:
        raw_headers: dict[str, str] = {}

        # OpenRouter load-balances across upstream providers, whose implicit prompt caches are per-provider. The session
        # affinity header routes repeat requests to the same upstream, which is what makes cache hits attainable at all
        # - so the cache key rides it rather than any request body field.
        if (
                (cache := self._model.cache) is not None and
                cache.control_style == 'openrouter' and
                (cache_key := self._options.cache_key) is not None
        ):
            check.state(cache.key)
            raw_headers['x-session-id'] = check.non_empty_str(cache_key)

        return raw_headers
