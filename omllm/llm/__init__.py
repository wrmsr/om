# fmt: off
# ruff: noqa: I001
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(globals()):
    ##

    from .backends.anthropic.messages.immediate import (  # noqa
        AnthropicMessagesImmediateBackend,
    )

    from .backends.anthropic.messages.stream import (  # noqa
        AnthropicMessagesStreamBackend,
    )

    from .backends.google.generative.immediate import (  # noqa
        GoogleGenerativeImmediateBackend,
    )

    from .backends.google.generative.stream import (  # noqa
        GoogleGenerativeStreamBackend,
    )

    from .backends.openai.completions.immediate import (  # noqa
        OpenaiCompletionsImmediateBackend,
    )

    from .backends.openai.completions.stream import (  # noqa
        OpenaiCompletionsStreamBackend,
    )

    ##

    from .backends.scripted.backend import (  # noqa
        ScriptedImmediateBackend,
        ScriptedStreamBackend,
    )

    from .backends.scripted.scripts import (  # noqa
        BackendScriptError,
        BackendScriptExhaustedError,

        BackendScriptTurnExpectation,
        BackendScriptInvocation,

        BackendScriptGate,
        BackendScriptGatePoint,

        BackendScriptTurn,
        BackendScript,
        BackendScriptCursor,
    )

    ##

    from .models.catalog import (  # noqa
        ModelCatalog,
    )

    from .models.default import (  # noqa
        default_models,
        default_model_catalog,
    )

    from .models.modeldb import (  # noqa
        modeldb_token_pricing,
    )

    from .models.pricing import (  # noqa
        estimate_token_cost,
        fill_estimated_token_cost,
    )

    ##

    from .tools.jsonschema import (  # noqa
        ToolJsonschemaBuilder,

        build_tool_dtype_json_schema,
        build_tool_params_json_schema,
        build_tool_json_schema,
    )

    from .tools.reflect import (  # noqa
        ToolDtypeReflector,

        reflect_tool_dtype,
    )

    ##

    from .types.backends import (  # noqa
        Backend,

        ImmediateBackend,

        StreamBackend,
    )

    from .types.compat import (  # noqa
        TokenCostMode,

        Compat,

        OpenaiCompat,
    )

    from .types.content import (  # noqa
        Content,
        ContentBuilder,

        TextContent,
        TextContentBuilder,

        ThinkingContent,
        ThinkingContentBuilder,

        ToolCall,
        ToolCallBuilder,
    )

    from .types.context import (  # noqa
        Context,
    )

    from .types.messages import (  # noqa
        Message,
        MessageBuilder,

        UserMessage,
        UserMessageBuilder,

        StopReason,
        TokenCostSource,
        TokenCost,
        TokenUsage,

        AiMessage,
        AiMessageBuilder,

        ToolResultMessage,
    )

    from .types.models import (  # noqa
        CacheCapabilities,

        TokenPricingProvider,
        TokenPricing,

        ModelKey,
        Model,
    )

    from .types.options import (  # noqa
        CacheRetention,

        Options,
    )

    from .types.streams import (  # noqa
        AiStreamEvent,
        AiStream,

        ContentAiStreamEvent,

        StreamStartAiStreamEvent,
        StreamEndAiStreamEvent,

        TextStartAiStreamEvent,
        TextDeltaAiStreamEvent,
        TextEndAiStreamEvent,

        ThinkingStartAiStreamEvent,
        ThinkingDeltaAiStreamEvent,
        ThinkingEndAiStreamEvent,

        ToolCallStartAiStreamEvent,
        ToolCallDeltaAiStreamEvent,
        ToolCallEndAiStreamEvent,
    )

    from .types.tools import (  # noqa
        ToolDtype,
        PrimitiveToolDtype,
        OBJECT_PRIMITIVE_TOOL_DTYPE,
        NULL_PRIMITIVE_TOOL_DTYPE,
        PRIMITIVE_TOOL_DTYPE_MAP,
        UnionToolDtype,
        NullableToolDtype,
        SequenceToolDtype,
        MappingToolDtype,
        TupleToolDtype,
        EnumToolDtype,
        ObjectToolDtype,

        ToolParam,
        Tool,
    )
