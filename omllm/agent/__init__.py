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

    from .exec.permissions import (  # noqa
        ExecPermissionTarget,
        ExecPermissionMatcher,
    )

    from .exec.ops import (  # noqa
        ExecParams,
        ExecResult,
        ExecOps,

        LocalExecOps,
    )

    ##

    from .fs.tools.edit import (  # noqa
        EditToolParams,
        EditTool,
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

    from .permissions.types import (  # noqa
        PermissionState,

        PermissionRequestor,
        DecidedPermissionState,
        PermissionDeniedError,
        PermissionDecider,

        PermissionTarget,
        PermissionMatcher,
        PermissionRule,
        PermissionAsker,
    )

    ##

    from .tools.classes import (  # noqa
        ToolClass,
    )

    from .tools.reflect import (  # noqa
        instantiate_tool_params,

        reflect_tool_params,
        reflect_tool_fn,
    )

    ##

    from .types.contexts import (  # noqa
        Context,
    )

    from .types.events import (  # noqa
        Event,

        LlmAiStreamEvent,

        AgentStartEvent,
        AgentEndEvent,

        TurnStartEvent,
        TurnEndEvent,
    )

    from .types.messages import (  # noqa
        AgentMessage,

        Message,
        MESSAGE_TYPES,

        InfoAgentMessage,
    )

    from .types.states import (  # noqa
        State,
    )

    from .types.tools import (  # noqa
        ToolExecutor,

        ToolEnvironment,
        ToolContext,
        ToolResult,

        ToolDescription,
        Tool,
        ToolSet,
    )

    from .types.turns import (  # noqa
        TurnConfig,
        TurnResult,
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
