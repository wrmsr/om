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

    from .commands.base import (  # noqa
        CommandError,
        ArgsCommandError,

        Command,
        Commands,
    )

    from .commands.classes import (  # noqa
        CommandClass,

        ParserCommandClass,
    )

    from .commands.manager import (  # noqa
        RunCommandResult,
        CommandsManager,
    )

    ##

    from .sessions.entries import (  # noqa
        SessionEntry,
    )

    from .sessions.events import (  # noqa
        SessionEvent,

        AgentSessionEvent,
    )

    from .sessions.session import (  # noqa
        Session,
    )

    from .sessions.storage import (  # noqa
        SessionStorage,

        InMemorySessionStorage,

        JsonlSessionStorage,
    )
