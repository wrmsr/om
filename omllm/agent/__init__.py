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
        EventSink,

        LlmAiStreamEvent,

        AgentStartEvent,
        AgentEndEvent,

        TurnStartEvent,
        TurnEndEvent,
    )

    from .types.messages import (  # noqa
        Message,
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
        State,
        Agent,
    )

    from .backends import (  # noqa
        BackendManager,

        DictBackendManager,
    )
