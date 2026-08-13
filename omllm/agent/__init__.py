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

    from .fs.tools.edit import (  # noqa
        EditParams,
        EditTool,
    )

    from .fs.tools.ls import (  # noqa
        LsParams,
        LsTool,
    )

    from .fs.tools.read import (  # noqa
        ReadParams,
        ReadTool,
    )

    from .fs.tools.write import (  # noqa
        WriteParams,
        WriteTool,
    )

    from .fs.ops import (  # noqa
        FsOps,

        LocalFsOps,
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

    from .permissions.fs import (  # noqa
        FsPermissionMode,
        FS_TOOL_PERMISSION_MODES,
        FsPermissionTarget,
        GlobFsPermissionMatcher,
    )

    from .permissions.managers import (  # noqa
        PermissionsManager,

        StandardPermissionsManager,
    )

    from .permissions.shell import (  # noqa
        ShellPermissionTarget,
        ShellPermissionMatcher,
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

    from .permissions.url import (  # noqa
        UrlPermissionTarget,
        RegexUrlPermissionMatcher,
    )

    ##

    from .shell.grep.tools.ripgrep import (  # noqa
        RipgrepParams,
        RipgrepTool,
    )

    from .shell.tools.bash import (  # noqa
        BashParams,
        BashTool,
    )

    from .shell.ops import (  # noqa
        ShellExecuteParams,
        ShellExecuteResult,
        ShellOps,

        LocalShellOps,
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

    from .agent import (  # noqa
        Agent,
    )

    from .backends import (  # noqa
        BackendManager,

        DictBackendManager,
    )
