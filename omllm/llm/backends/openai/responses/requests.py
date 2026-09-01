import typing as ta

from omcore import check
from omcore import lang
from omcore.formats.json import all as json

from ....tools.jsonschema import build_tool_params_json_schema
from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.errors import BackendError
from ....types.messages import AiMessage
from ....types.messages import ToolResultMessage
from ....types.messages import UserMessage
from ....types.models import Model
from ....types.options import CacheRetention
from ....types.options import Options
from .signatures import parse_text_signature
from .signatures import parse_thinking_signature
from .signatures import parse_tool_call_signature


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

    def _add_cache_options(self, raw_request: dict[str, ta.Any]) -> None:
        cache_key = self._options.cache_key
        cache_retention = self._options.cache_retention
        if cache_key is None and cache_retention is None:
            return

        cache = self._model.cache
        if cache is None or cache.control_style not in ('openai_legacy', 'openai_ttl'):
            raise ValueError(f'Model does not support OpenAI prompt cache controls: {self._model.key!r}')

        if cache_key is not None:
            if not cache.key:
                raise ValueError(f'Model does not support prompt cache keys: {self._model.key!r}')

            raw_request['prompt_cache_key'] = check.non_empty_str(cache_key)

        if cache_retention is not None:
            if cache_retention not in (cache.retentions or ()):
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
                raise BackendError(cache.control_style)

    def _add_ai_message_content(self, raw_input: list[dict], msg: AiMessage) -> None:
        for c in msg.content:
            if isinstance(c, TextContent):
                # Empty text carries nothing worth replaying.
                if not c.text:
                    continue

                # A signed text block replays as the full output item it came from, preserving its identity for
                # same-model replay. Unsigned text (such as from a different backend) replays as a plain assistant
                # message, which the api accepts without item identity.
                if (raw_sig := parse_text_signature(c.backend_signature)) is not None:
                    raw_input.append({
                        'type': 'message',
                        'role': 'assistant',
                        'status': 'completed',
                        'id': raw_sig['id'],
                        **({'phase': raw_phase} if (raw_phase := raw_sig.get('phase')) else {}),
                        'content': [{'type': 'output_text', 'text': c.text}],
                    })

                else:
                    raw_input.append({
                        'role': 'assistant',
                        'content': [{'type': 'output_text', 'text': c.text}],
                    })

            elif isinstance(c, ThinkingContent):
                # Reasoning is opaque and must be replayed as the verbatim item to be preserved. Unsigned thinking
                # (such as from a different backend) cannot be represented, and is dropped.
                if (raw_item := parse_thinking_signature(c.backend_signature)) is not None:
                    raw_input.append(dict(raw_item))

            elif isinstance(c, ToolCall):
                raw_input.append({
                    'type': 'function_call',
                    **(
                        {'id': raw_sig['id']}
                        if (raw_sig := parse_tool_call_signature(c.backend_signature)) is not None
                        else {}
                    ),
                    'call_id': c.id,
                    'name': c.name,
                    'arguments': json.dumps(c.args),
                })

            else:
                raise TypeError(c)

    @lang.cached_function
    def raw_request(self) -> dict[str, ta.Any]:
        raw_request: dict = {
            'model': self._model.key_.id,

            # This backend is stateless: the full context is replayed each turn, nothing is retained server-side, and
            # reasoning is returned encrypted so replaying it is possible at all (these models reason by default, even
            # when no reasoning options are requested).
            'store': False,
            'include': ['reasoning.encrypted_content'],
        }

        if self._options.max_tokens is not None:
            raw_request['max_output_tokens'] = self._options.max_tokens

        if self._options.thinking:
            # Reasoning itself is not opt-in - this only requests readable summaries of it.
            raw_request['reasoning'] = {'summary': 'auto'}

        self._add_cache_options(raw_request)

        #

        if self._context.system_prompt:
            raw_request['instructions'] = self._context.system_prompt

        raw_input: list[dict] = []

        for msg in self._context.messages or []:
            if isinstance(msg, UserMessage):
                if isinstance(msg.content, str):
                    raw_text = msg.content
                elif isinstance(msg.content, TextContent):
                    raw_text = msg.content.text
                else:
                    raise TypeError(msg)

                raw_input.append({
                    'role': 'user',
                    'content': [{'type': 'input_text', 'text': raw_text}],
                })

            elif isinstance(msg, AiMessage):
                self._add_ai_message_content(raw_input, msg)

            elif isinstance(msg, ToolResultMessage):
                raw_input.append({
                    'type': 'function_call_output',
                    'call_id': msg.tool_call_id,
                    'output': '\n'.join([c.text for c in msg.content]),
                })

            else:
                raise TypeError(msg)

        raw_request['input'] = raw_input

        #

        if self._context.tools:
            raw_tools: list[dict] = []

            for tool in self._context.tools:
                raw_tools.append({
                    'type': 'function',
                    'name': tool.name,
                    **({'description': tool.description} if tool.description else {}),
                    'parameters': build_tool_params_json_schema(tool),
                })

            raw_request['tools'] = raw_tools

        #

        return raw_request
