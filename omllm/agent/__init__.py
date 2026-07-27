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

    from .types.contexts import (  # noqa
        Context,
    )

    from .types.events import (  # noqa
        Event,
        EventSink,

        AgentStartEvent,
        AgentEndEvent,

        TurnStartEvent,
        TurnEndEvent,
    )

    from .loop import (  # noqa
        LoopConfig,
        LoopResult,
        Loop,
    )

    from .types.messages import (  # noqa
        Message,
    )

    from .types.tools import (  # noqa
        ToolExecutor,
        ToolContext,
        ToolResult,
        Tool,
        ToolSet,
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
