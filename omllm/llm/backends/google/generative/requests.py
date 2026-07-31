import typing as ta

from omcore import lang

from ....types.content import TextContent
from ....types.content import ThinkingContent
from ....types.content import ToolCall
from ....types.context import Context
from ....types.messages import AiMessage
from ....types.messages import ToolResultMessage
from ....types.messages import UserMessage
from ....types.models import Model
from ....types.options import Options


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

    def _check_cache_options(self) -> None:
        if self._options.cache_key is None and self._options.cache_retention is None:
            return

        # Gemini 2.5+ implicit caching is automatic and exposes no generation-request cache controls. Explicit caching
        # requires creating and managing a cachedContents resource, then passing its name as cachedContent; that
        # lifecycle cannot be represented by request-scoped Options and is intentionally not implemented here yet.
        raise ValueError(
            f'Model supports only implicit request-scoped caching: {self._model.key!r}',
        )

    @lang.cached_function
    def raw_request(self) -> dict[str, ta.Any]:
        self._check_cache_options()

        raw_request: dict = {}

        raw_generation_config: dict = {}

        if self._options.max_tokens is not None:
            raw_generation_config['maxOutputTokens'] = self._options.max_tokens

        if self._options.thinking:
            raw_generation_config['thinkingConfig'] = {
                'includeThoughts': True,
            }

        if raw_generation_config:
            raw_request['generationConfig'] = raw_generation_config

        #

        if self._context.system_prompt:
            raw_request['systemInstruction'] = {
                'parts': [{
                    'text': self._context.system_prompt,
                }],
            }

        raw_contents: list[dict] = []

        for msg in self._context.messages or []:
            if isinstance(msg, UserMessage):
                if isinstance(msg.content, str):
                    raw_contents.append({
                        'role': 'user',
                        'parts': [{
                            'text': msg.content,
                        }],
                    })

                elif isinstance(msg.content, TextContent):
                    raw_contents.append({
                        'role': 'user',
                        'parts': [{
                            'text': msg.content.text,
                        }],
                    })

                else:
                    raise TypeError(msg)

            elif isinstance(msg, AiMessage):
                raw_parts: list[dict] = []

                for c in msg.content:
                    if isinstance(c, TextContent):
                        # Any thought signature issued on a text part is echoed back with it.
                        raw_parts.append({
                            'text': c.text,
                            **({'thoughtSignature': c.backend_signature} if c.backend_signature else {}),
                        })

                    elif isinstance(c, ThinkingContent):
                        # Thought summaries are display-only and are not sent back - required signatures ride the text
                        # and functionCall parts.
                        pass

                    elif isinstance(c, ToolCall):
                        # Tool call ids are not sent - google does not reliably issue them, so they may be locally
                        # fabricated, and those must not be echoed back. Function responses are matched by name. Thought
                        # signatures however must be echoed back with their function calls - gemini rejects
                        # tool-calling requests whose replayed function calls lack them.
                        raw_parts.append({
                            'functionCall': {
                                'name': c.name,
                                'args': c.args,
                            },
                            **({'thoughtSignature': c.backend_signature} if c.backend_signature else {}),
                        })

                    else:
                        raise TypeError(c)

                raw_contents.append({
                    'role': 'model',
                    'parts': raw_parts,
                })

            elif isinstance(msg, ToolResultMessage):
                raw_contents.append({
                    'parts': [{
                        'functionResponse': {
                            'name': msg.tool_name,
                            'response': {
                                'result': '\n'.join([c.text for c in msg.content]),
                            },
                        },
                    }],
                })

            else:
                raise TypeError(msg)

        raw_request['contents'] = raw_contents

        #

        if self._context.tools:
            raw_decls: list[dict] = []

            for tool in self._context.tools:
                raw_properties: dict = {}
                raw_required: list[str] = []
                for param in tool.params or []:
                    raw_properties[param.name] = {
                        **({'type': param.type.upper()} if param.type else {}),
                        **({'description': param.description} if param.description else {}),
                    }
                    if not param.optional:
                        raw_required.append(param.name)

                raw_decls.append({
                    'name': tool.name,
                    **({'description': tool.description} if tool.description else {}),
                    # A parameterless declaration must omit its schema entirely - google rejects empty OBJECT schemas.
                    **({'parameters': {
                        'type': 'OBJECT',
                        'properties': raw_properties,
                        **({'required': raw_required} if raw_required else {}),
                    }} if raw_properties else {}),
                })

            raw_request['tools'] = [{
                'functionDeclarations': raw_decls,
            }]

        #

        return raw_request
