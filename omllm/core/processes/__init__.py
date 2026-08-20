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

    from .asyncio.manager import (  # noqa
        AsyncioProcessManager,
    )

    ##

    from .managers.base import (  # noqa
        BaseProcessManager,
    )

    from .managers.process import (  # noqa
        BaseProcess,
        ProcessStdinWriter,
    )

    from .managers.types import (  # noqa
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

    from .sandbox.bwrap import (  # noqa
        BwrapSandbox,
    )

    from .sandbox.factory import (  # noqa
        platform_sandbox,
    )

    from .sandbox.policy import (  # noqa
        SandboxExecPaths,
        SandboxDevAccess,
        SandboxDefaults,
        SandboxPolicy,
    )

    from .sandbox.seatbelt import (  # noqa
        SeatbeltSandbox,
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
        ProcessError,
        SpawnError,
        ProcessTimeoutError,
        ProcessNotAliveError,
        ProcessPoisonedError,
        StuckProcessError,
        ScopeClosedError,
        NotAPtyError,
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
        ProcessOption,
        ProcessOptions,
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
        Target,
        Sandbox,
    )

    from .types.specs import (  # noqa
        ProcessSpec,
        ProcessStdio,
        PtyStdio,
    )

    from .types.states import (  # noqa
        ProcessState,
    )

    ##

    from .targets.docker import (  # noqa
        DockerExecTarget,
    )

    from .targets.ssh import (  # noqa
        SshTarget,
    )

    ##

    from .handles import (  # noqa
        Process,
        ProcessInfo,
        ProcessControl,
        ProcessStdin,
        ProcessOutput,
        ProcessPty,
        ProcessWaiter,
    )

    from .inject import (  # noqa
        bind_process_manager,
    )
