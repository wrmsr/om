# fmt: off
# ruff: noqa: I001
# @om-recommended-import-alias "har"
from omcore import dataclasses as _dc  # noqa


_dc.init_package(
    globals(),
    codegen=True,
)


##


from omcore import lang as _lang  # noqa


with _lang.auto_proxy_init(
        globals(),
        update_exports=True,
):
    ##

    from .commands.base import (  # noqa
        CommandError,
        ArgsCommandError,

        CommandContextPrinter,
        CommandContext,
        Command,
        Commands,
    )

    from .commands.classes import (  # noqa
        CommandClass,

        ParserCommandClass,
    )

    from .commands.compact import (  # noqa
        CompactCommand,
    )

    from .commands.manager import (  # noqa
        RunCommandResult,
        CommandsManager,
    )

    from .commands.permissions import (  # noqa
        PermissionsCommand,
    )

    from .commands.processes import (  # noqa
        ProcessesCommand,
    )

    from .commands.simple import (  # noqa
        EchoCommand,

        QuitCommand,
    )

    ##

    from .sessions.storage.fs import (  # noqa
        FsSessionStorage,
    )

    from .sessions.storage.inmemory import (  # noqa
        InMemorySessionStorage,
    )

    from .sessions.storage.orm.impl import (  # noqa
        StoreOrm,
    )

    from .sessions.storage.orm.models import (  # noqa
        OrmSession,
        OrmSessionEntry,

        orm_mappers,
    )

    from .sessions.storage.orm.sql import (  # noqa
        SqlOrm,
    )

    from .sessions.storage.orm.sqlite import (  # noqa
        SqliteDbConfig,

        connect_sqlite,
        sqlite_db,
        asyncio_sqlite_db,
    )

    from .sessions.storage.orm.storage import (  # noqa
        OrmSessionStorage,
    )

    from .sessions.storage.orm.types import (  # noqa
        Orm,
    )

    from .sessions.storage.types import (  # noqa
        SessionNotFoundError,
        SessionStorage,
    )

    from .sessions.entries import (  # noqa
        SessionEntry,

        MessageSessionEntry,
        ContextProjectionSessionEntry,
    )

    from .sessions.events import (  # noqa
        SessionEvent,

        AgentSessionEvent,
    )

    from .sessions.session import (  # noqa
        Session,
    )

    from .sessions.types import (  # noqa
        SessionId,
    )
