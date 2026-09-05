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

    from .eval.tools.quickjs import (  # noqa
        QuickjsToolParams,
        QuickjsTool,
    )

    from .eval.permissions import (  # noqa
        EvalLanguage,
        EvalPermissionTarget,
        EvalPermissionMatcher,
    )

    ##

    from .exec.ripgrep.tools.ripgrep import (  # noqa
        RipgrepToolParams,
        RipgrepTool,
    )

    from .exec.tools.bash import (  # noqa
        BashToolParams,
        BashTool,
    )

    from .exec.tools.process import (  # noqa
        ProcessSpawnToolParams,
        ProcessSpawnTool,

        ProcessReadToolParams,
        ProcessReadTool,

        ProcessWriteToolParams,
        ProcessWriteTool,

        ProcessKillToolParams,
        ProcessKillTool,

        ProcessListToolParams,
        ProcessListTool,
    )

    from .exec.permissions import (  # noqa
        ExecPermissionTarget,
        ExecPermissionMatcher,
    )

    from .exec.tools.details import (  # noqa
        ExecToolResultDetails,
    )

    from .exec.ops import (  # noqa
        ExecParams,
        ExecResult,
        ExecOutputSink,
        ExecOps,

        ProcessesExecOps,

        format_exec_output,
    )

    ##

    from .fs.tools.details import (  # noqa
        EditToolResultDetails,
        GlobToolResultDetails,
        ReadToolResultDetails,
        WriteToolResultDetails,
    )

    from .fs.tools.edit import (  # noqa
        EditToolParams,
        EditTool,
    )

    from .fs.tools.glob import (  # noqa
        GlobToolParams,
        GlobTool,
    )

    from .fs.tools.ls import (  # noqa
        LsToolParams,
        LsTool,
    )

    from .fs.tools.read import (  # noqa
        ReadToolParams,
        ReadTool,
    )

    from .fs.tools.write import (  # noqa
        WriteToolParams,
        WriteTool,
    )

    from .fs.ops import (  # noqa
        FsOps,

        LocalFsOps,
    )

    from .fs.permissions import (  # noqa
        FsPermissionMode,
        FS_TOOL_PERMISSION_MODES,
        FsPermissionTarget,
        GlobFsPermissionMatcher,
    )

    ##

    from .permissions.collection import (  # noqa
        PermissionRules,
    )

    from .permissions.deciders import (  # noqa
        StaticPermissionDecider,
        DENY_TOOL_PERMISSION_DECIDER,

        StandardPermissionDecider,
    )

    from .permissions.managers import (  # noqa
        PermissionsManager,

        StandardPermissionsManager,
    )

    from .permissions.tools import (  # noqa
        ToolPermissionMatcher,
    )

    from .projection.builders import (  # noqa
        StandardLlmContextBuilder,
    )

    from .projection.messages import (  # noqa
        TypeMapAgentMessageProjector,
    )

    from .projection.types import (  # noqa
        AgentMessageProjector,
        LlmContextBuilder,
    )

    ##

    from .permissions.types import (  # noqa
        PermissionState,

        PermissionRequestor,

        DecidedPermissionState,
        PermissionDeniedError,
        PermissionAskAbortedError,
        PermissionDecider,

        PermissionTarget,

        PermissionMatchContext,
        PermissionMatcher,

        PermissionRule,

        PermissionAsker,
    )

    ##

    from .tools.classes import (  # noqa
        ToolClass,
    )

    from .tools.progress import (  # noqa
        NopToolProgressSink,
    )

    from .tools.reflect import (  # noqa
        instantiate_tool_params,

        reflect_tool_params,
        reflect_tool_fn,
    )

    from .turns.inboxes import (  # noqa
        ListTurnInbox,
    )

    from .turns.loop import (  # noqa
        TurnLoop,
    )

    from .turns.runner import (  # noqa
        TurnLoopRunner,
    )

    ##

    from .types.contexts import (  # noqa
        Context,
    )

    from .types.errors import (  # noqa
        Error,

        AgentError,
        AgentBusyError,

        TurnError,
        UnknownToolError,
        ErrorStopReasonError,
    )

    from .types.events import (  # noqa
        Event,

        LlmAiStreamEvent,
        LlmRetryEvent,

        AgentStartEvent,
        AgentEndEvent,

        MessageAddedEvent,

        TurnEvent,
        TurnStartEvent,
        TurnEndEvent,

        ToolExecutionEvent,
        ToolExecutionStartEvent,
        ToolExecutionUpdateEvent,
        ToolExecutionEndEvent,

        StateUpdateEvent,
    )

    from .types.inboxes import (  # noqa
        TurnInbox,
    )

    from .types.messages import (  # noqa
        AgentMessage,

        Message,
        MESSAGE_TYPES,

        InfoAgentMessage,
    )

    from .types.progress import (  # noqa
        ToolProgressUpdate,
        OutputToolProgressUpdate,

        ToolProgressSink,
    )

    from .types.states import (  # noqa
        State,
    )

    from .types.tools import (  # noqa
        ToolExecutor,

        ToolEnvironment,
        ToolContext,
        ToolResultDetails,
        ToolResult,

        ToolDescription,
        Tool,
        ToolSet,
    )

    from .types.turns import (  # noqa
        LlmRetryConfig,
        TurnConfig,

        AgentEndReason,

        TurnParams,
        TurnResult,

        TurnRunner,
    )

    ##

    from .web.tools.fetch import (  # noqa
        WebFetchToolParams,
        WebFetchTool,
    )

    from .web.tools.search import (  # noqa
        WebSearchToolParams,
        WebSearchTool,
    )

    from .web.fetching import (  # noqa
        WebFetchRequest,
        WebFetchedPage,
        WebFetcher,

        HttpWebFetcher,

        DictWebFetcher,
    )

    from .web.permissions import (  # noqa
        UrlPermissionTarget,
        RegexUrlPermissionMatcher,
    )

    from .web.search import (  # noqa
        WebSearchRequest,
        WebSearchHit,
        WebSearchResult,
        WebSearcher,
    )

    ##

    from .agent import (  # noqa
        Agent,
    )

    from .backends import (  # noqa
        BackendManager,

        DictBackendManager,
    )
