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

    from .handles import (  # noqa
        Process,
        ProcessInfo,
        ProcessControl,
        ProcessStdin,
        ProcessOutput,
        ProcessWaiter,
    )

    from .manager import (  # noqa
        ManagerConfig,
        ProcessManager,
    )

    from .scopes.policies import (  # noqa
        ScopeClosePolicy,
    )

    from .scopes.scope import (  # noqa
        ProcessScope,
        ProcessRun,
        ScopeCloseResult,
    )

    ##

    from .launch.launcher import (  # noqa
        Launcher,
        LaunchPlan,
        SpecTransform,
    )

    from .launch.shim import (  # noqa
        ShimLauncher,
    )

    from .launch.transforms import (  # noqa
        EnvScrubTransform,
        ShellWrapTransform,
    )

    ##

    from .spool.frames import (  # noqa
        SpoolRecord,
    )

    from .spool.render import (  # noqa
        SpoolRenderer,
        RawRenderer,
        ArrivalMergedRenderer,
        TaggedLinesRenderer,
    )

    from .spool.spool import (  # noqa
        OutputSpool,
        SpoolRead,
    )

    ##

    from .types.errors import (  # noqa
        ProcsError,
        SpawnError,
        ProcessTimeoutError,
        ProcessNotAliveError,
        ProcessPoisonedError,
        StuckProcessError,
        ScopeClosedError,
        ManagerClosedError,
        ManagerNotStartedError,
        UnsafeChildSignalDispositionError,
    )

    from .types.events import (  # noqa
        ProcessEvent,
        ProcessSpawnedEvent,
        ProcessExitedEvent,
        ProcessReapedEvent,
        ProcessAbandonedEvent,
        ProcessPoisonedEvent,
        ProcessReparentedEvent,
        ScopeOpenedEvent,
        ScopeClosedEvent,
    )

    from .types.ids import (  # noqa
        ProcessId,
        ProcessIdGenerator,
        CountingProcessIdGenerator,
    )

    from .types.options import (  # noqa
        ProcOption,
        ProcOptions,
        layer_options,

        TerminationPolicy,
        SpoolPolicy,
        SessionMode,
        Credentials,
        Umask,
        Rlimit,
        Deathsig,
        RunTimeout,
        Tag,
        PassFd,
    )

    from .types.specs import (  # noqa
        ProcessSpec,
        ProcessStdio,
    )

    from .types.states import (  # noqa
        ProcessState,
    )

    ##

    from .asyncio.manager import (  # noqa
        AsyncioProcessManager,
    )

    from .inject import (  # noqa
        bind_process_manager,
    )
