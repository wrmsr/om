# fmt: off
# ruff: noqa: I001
from omcore import lang as _lang


with _lang.auto_proxy_init(globals()):
    ##

    from .agent import (  # noqa
        AgentEventSubscribers,
        agent_event_subscribers,

        HasOnEventAgent,
        bind_on_agent_event_subscriber,

        TURN_SCOPED,
        TURN_SCOPE,

        TOOL_INVOCATION_SCOPED,
        TOOL_INVOCATION_SCOPE,
    )

    from .commands import (  # noqa
        commands_binder,
        bind_command_singleton,
    )

    from .inject import (  # noqa
        bind_tui,
    )

    from .subagents import (  # noqa
        SUBAGENT_TURN_SCOPED,
        SUBAGENT_TURN_SCOPE,

        SUBAGENT_TOOL_INVOCATION_SCOPED,
        SUBAGENT_TOOL_INVOCATION_SCOPE,

        bind_subagent_agent,
        ChildInjectorSubagentRunner,
    )

    from .tools import (  # noqa
        AgentTools,
        agent_tools,
        bind_agent_tool_class,

        bind_tool_infrastructure,
        bind_tool_classes,
    )
