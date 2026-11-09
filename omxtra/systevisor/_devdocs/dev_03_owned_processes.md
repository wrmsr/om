# Development 03: owned process kernel

## Intent

Execute spawn/signal effects without ever making a bare PID or PGID a supported control-plane target. This is the
boundary where a PID-reuse bug stops being a normal implementation mistake and becomes an impossible API shape.

## Ownership and waiting

- The process manager is the only creator and waiter of managed children. It indexes live resources by run ID and
  keeps PID lookup private.
- Exit detection uses `waitid(P_PID, ..., WEXITED | WNOHANG | WNOWAIT)`. Observation and reaping are separate acts,
  and a direct child remains unreaped until the engine has consumed its exit.
- Every signal acquires a manager-issued lease. A leased process is skipped by wait observation, and explicit reap is
  rejected while any lease exists. Signal backends receive the lease capability, not a PID argument.
- Linux opens a pidfd when the stdlib or libc exposes it and prefers pidfd signal delivery. Portable fallback is safe
  because the target remains this manager's unreaped direct child for the entire lease.
- Session signaling is permitted only for a child that created a fresh session whose ID equals its pinned leader PID.
  The session capability is not activated until the close-on-exec handshake proves that `setsid` and all child setup
  completed; a merely requested session is not signalable as a group.
  Exit acknowledgement takes a cleanup lease, sends a final group KILL while the zombie leader still prevents PGID
  reuse, then reaps. A child that did not create such a session cannot be group-signaled.
- Unknown/adopted PIDs have no registration or signaling path. Generic `waitpid(-1)` is absent.

## Fork/exec

- Parent-side preparation resolves users/groups, supplementary groups, environment, stdio topology, maximum FD, and
  other fallible setup before fork.
- Child setup supports injected before/after-identity modifiers and explicit preserved FDs. Unapproved descriptors are
  closed before modifier callbacks run, so a modifier cannot accidentally depend on ambient supervisor resources.
- The child can create a session, change directory/umask, wire stdin/stdout/stderr, drop groups/GID/UID, close all
  unapproved descriptors, and use `execvpe`.
- A close-on-exec error pipe distinguishes successful exec from setup/exec failure without sleeping or guessing.
- Managed stdout/stderr modes always yield nonblocking parent read FDs. Retirement transfers those descriptors so a
  later log manager can drain tail bytes before closing them.

## State and update preparation

Each live process exposes a serial `SystevisorOwnedProcessState` containing run/instance identity, direct PID, pidfd,
session ID, Linux birth identity when available, status, owned descriptors, return code, and lease count. Rehydration
is intentionally not implemented yet, but every resource needed by its future inheritance manifest is explicit.

## Tests

Most behavior remains covered in the no-process deterministic engine suite. The kernel has a deliberately small set
of real-fork integration tests using exec-error and wait state as synchronization points—never `time.sleep`. They
cover successful exec/observed-before-reap semantics, lease exclusion from waiting, run-scoped signal delivery,
rejection of unknown/session-unowned targets, and exec failure while retaining wait ownership. Every test registers
exact cleanup before making assertions.

## Next

Connect process descriptors, pidfds/SIGCHLD, deadlines, and signal intake to the fdio reactor. Then introduce byte
stream log channels and the event journal without allowing either slow consumers or control requests to block child
drainage.
