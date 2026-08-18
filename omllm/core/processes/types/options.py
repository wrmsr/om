"""
Per-spawn policies as `TypedValues` families. A `ProcOptions` collection is layered manager -> scope -> spawn via
`layer_options` (unique families override, non-unique families accumulate), so callers only state what differs.
"""
import abc
import signal
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import typedvalues as tv

from .specs import ProcessSpec


##


class ProcessOption(tv.TypedValue, lang.Abstract):
    pass


ProcessOptions: ta.TypeAlias = tv.TypedValues[ProcessOption]


def layer_options(base: ProcessOptions | None, *overrides: ta.Iterable[ProcessOption] | None) -> ProcessOptions:
    cur: ProcessOptions = base if base is not None else tv.TypedValues()
    for ovr in overrides:
        if ovr is None:
            continue
        lst = list(ovr)
        if not lst:
            continue
        cur = cur.update(*lst, mode='override')
    return cur


##


DEFAULT_MEMORY_CAP: ta.Final[int] = 1024 * 1024


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class TerminationPolicy(tv.UniqueTypedValue, ProcessOption, lang.Final):
    # First signal sent when asked to stop a live process.
    signal: int = signal.SIGTERM

    # Seconds to wait after `signal` before escalating to SIGKILL.
    grace_s: float = 5.

    # Seconds to wait after SIGKILL before declaring the process stuck.
    kill_s: float = 5.

    # Close stdin (EOF) before signaling - many programs exit cleanly on EOF alone.
    close_stdin: bool = True

    # Signal the whole process group (our own leader's group) rather than just the leader.
    process_group: bool = True

    # After the leader has exited, seconds to wait for output EOF (stragglers still holding the pipes) before sweeping
    # the group with SIGKILL and force-closing the pipes.
    drain_s: float = 1.

    # A process that survives SIGKILL past `kill_s` (D-state, etc): abandon it (log, event, unregister) or raise a
    # StuckProcessError from the closing scope.
    on_stuck: ta.Literal['abandon', 'raise'] = 'abandon'

    def __post_init__(self) -> None:
        check.arg(self.grace_s >= 0)
        check.arg(self.kill_s >= 0)
        check.arg(self.drain_s >= 0)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SpoolPolicy(tv.UniqueTypedValue, ProcessOption, lang.Final):
    # Max framed bytes held in memory before the oldest are spilled to a file (or dropped if `spill` is false). None
    # disables the cap entirely - beware.
    memory_cap: int | None = DEFAULT_MEMORY_CAP

    # Whether overflow spills to a manager-owned temp file (else it is dropped, and reads report `dropped_before`).
    spill: bool = True

    # Keep the spill file after the process handle is reaped / the manager closes.
    keep_spill: bool = False

    def __post_init__(self) -> None:
        check.arg(self.memory_cap is None or self.memory_cap >= 0)


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SessionMode(tv.UniqueTypedValue, ProcessOption, lang.Final):
    # 'session': the child becomes a session (and group) leader - detached from any controlling terminal, and able to
    # acquire a pty as its ctty later. 'group': a new process group in our session. Either way pgid == pid, which is
    # what makes group signaling safe.
    mode: ta.Literal['session', 'group'] = 'session'


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class Credentials(tv.UniqueTypedValue, ProcessOption, lang.Final):
    """gosu-like privilege drop, applied in the child before exec. Names are resolved in the child."""

    user: int | str | None = None
    group: int | str | None = None
    extra_groups: ta.Sequence[int | str] | None = None


@ta.final
@dc.dataclass(frozen=True)
class Umask(tv.UniqueScalarTypedValue[int], ProcessOption, lang.Final):
    pass


@ta.final
@dc.dataclass(frozen=True)
class Rlimit(ProcessOption, lang.Final):
    """Non-unique: one per resource. `resource` is a `resource.RLIMIT_*` constant."""

    resource: int
    soft: int
    hard: int


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class Deathsig(tv.UniqueTypedValue, ProcessOption, lang.Final):
    """Linux only: signal delivered to the child when the spawning thread dies. Best-effort elsewhere (ignored)."""

    signal: int = signal.SIGTERM


@ta.final
@dc.dataclass(frozen=True)
class RunTimeout(tv.UniqueScalarTypedValue[float], ProcessOption, lang.Final):
    """
    Overall wall-clock timeout for `ProcessScope.run` in seconds; on expiry the process is stopped and the run raises
    `ProcessTimeoutError`.
    """


@ta.final
@dc.dataclass(frozen=True)
class Tag(tv.ScalarTypedValue[str], ProcessOption, lang.Final):
    """Non-unique free-form tags for listing / filtering."""


@ta.final
@dc.dataclass(frozen=True)
class PassFd(tv.ScalarTypedValue[int], ProcessOption, lang.Final):
    """Non-unique: an extra caller-owned fd to keep open (inheritable) in the child."""


##


class Target(tv.UniqueTypedValue, ProcessOption, lang.Abstract):
    """
    Where a process runs. The default (no Target) is local. A Target rewrites the spec into the *local* command that
    reaches the destination - e.g. wrapping argv in `docker exec ...` or `ssh host ...` - so the manager still spawns
    and manages a single local process. Targets also own remote signal semantics (a future concern: killing the local
    `docker exec` client does not necessarily stop the process inside the container).
    """

    @abc.abstractmethod
    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        raise NotImplementedError


##


class Sandbox(tv.UniqueTypedValue, ProcessOption, lang.Abstract):
    """
    Local OS-level confinement (filesystem, network) applied by wrapping the command in a sandbox launcher (bubblewrap
    on Linux, sandbox-exec on macOS). Like Target it rewrites the spec into the local command to run; unlike Target the
    process is still local, just confined. Applied after any Target.
    """

    @abc.abstractmethod
    def transform_spec(self, spec: ProcessSpec) -> ProcessSpec:
        raise NotImplementedError


##


DEFAULT_TERMINATION_POLICY: ta.Final = TerminationPolicy()
DEFAULT_SPOOL_POLICY: ta.Final = SpoolPolicy()
DEFAULT_SESSION_MODE: ta.Final = SessionMode()


def get_termination_policy(opts: ProcessOptions) -> TerminationPolicy:
    return opts.get(TerminationPolicy, DEFAULT_TERMINATION_POLICY)


def get_spool_policy(opts: ProcessOptions) -> SpoolPolicy:
    return opts.get(SpoolPolicy, DEFAULT_SPOOL_POLICY)


def get_session_mode(opts: ProcessOptions) -> SessionMode:
    return opts.get(SessionMode, DEFAULT_SESSION_MODE)
