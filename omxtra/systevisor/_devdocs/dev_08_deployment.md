# Development 08: deployment, host runtime, and the first real artifact

## Goal

This phase was meant to prove that the architecture built so far is deployable in the forms which motivated the
project: one source file on a stock Python 3.8 installation, a foreground development process, PID 1 in a container,
or one opaque systemd/launchd service. It also needed to turn the previously exposed manager configuration into real
behavior without weakening child identity and signal safety.

## Amalgamation

`x/systevisor/__main__.py` is now an `@om-amalg` root and generates
`x/systevisor/_bin/systevisor.py`. The artifact is checked in so deployment does not require this repository or the
development amalgamator. Regeneration is:

```text
./python -m omdev.amalg gen -m omcore x/systevisor
```

The first generation was immediately valuable. The amalgamator moves typing assignments to a shared early section,
and `SystevisorApiResult` referenced response classes which had not been defined there. Package imports had hidden the
ordering issue. The alias is now explicitly kept in source order. This is exactly why generation is part of ordinary
tests rather than a release-day task.

The artifact tests do three different jobs:

- compare a fresh generation byte-for-byte with the checked-in file on the development interpreter;
- parse top-level imports and reject anything outside an explicit standard-library root set; and
- execute the artifact namespace from an unrelated temporary location, including on Python 3.8.

The current result is roughly 988 KB / 29,800 lines. `VENV=8 ./python -I` successfully runs both help and service
template commands, demonstrating that neither the checkout nor site-level package imports are required.

The development amalgamator itself imports modern non-lite repo code and cannot run under Python 3.8. The 3.8 test
therefore loads the checked artifact while the default-interpreter test performs regeneration. This distinction is
intentional: the product supports 3.8; its repository build tool does not need to.

## Manager bootstrap

The new injected platform composition root supplies four boundaries:

- `SystevisorProcessBootstrap` for daemonization and process-global setup;
- `SystevisorManagerLogging` for handlers owned specifically by Systevisor;
- `SystevisorPidFileManager` for the held single-instance lock; and
- `SystevisorServiceNotifier` for optional host-service status.

Cold configuration is compiled before any fdio/reactor object is constructed. A valid candidate is then used to apply
daemon mode, cwd, umask, minimum `RLIMIT_NOFILE` / `RLIMIT_NPROC`, Linux child-subreaper mode, manager UID/GID, and
`omcore.os.setproctitle`. Only after that does the regular injected runtime exist and reconcile the snapshot. An
invalid candidate still goes through the config-attempt recorder so a requested bootstrap state directory receives
its atomic diagnostic file, but it never applies manager-global state.

Manager logging uses the omcore standard formatter/filter, with independently owned stderr, rotating-file, and
journald handlers. Reconfiguration prepares new handlers before committing and does not remove unrelated handlers
from an embedding application. The original target logger level is restored on close. Logging, process-title changes,
and the existing ANSI policy are live; fields such as UID, cwd, pidfile, daemon mode, and subreaper mode reject a live
reload at the prepare stage.

The pidfile remains open and exclusively `flock`ed for the manager lifetime. It is truncated/written only after the
lock is acquired. Cleanup compares the live path's device/inode to the locked descriptor and therefore leaves an
external replacement untouched. This pidfile is never accepted by any signaling method.

## PID 1 and adoptees

Linux `prctl(PR_SET_CHILD_SUBREAPER)` is used through ctypes when configured; PID 1 is already treated as a subreaper.
Unknown direct children are enumerated through procfs. The process manager excludes every known owned PID, observes a
candidate with `waitid(P_PID, ..., WNOWAIT)`, and then reaps exactly that PID. The returned fact contains only PID and
exit status. There is deliberately no run identity, signal lease, or method which can signal it.

The wait poll remains armed while unknown-child reaping is enabled, even with no managed runs. This covers an adopted
child which becomes a zombie before the signal wakeup handler is installed or after the last managed leader exits.
Contract tests fork real children, explicitly establish the exited checkpoint with non-reaping `waitid`, and prove
both that an unknown child is consumed and that a PID present in the owned map is never consumed by this path.

Darwin continues to support all known direct-child management. The default unknown-child provider is empty without
Linux procfs; there is no attempt to shell out to `ps` in the runtime.

## systemd and launchd

When `NOTIFY_SOCKET` exists, startup, readiness, and stopping messages use the native systemd datagram protocol. The
implementation supports filesystem and abstract socket addresses and has an actual Unix-datagram contract test.

The local `service-template` command emits either:

- a `Type=notify`, `NotifyAccess=main`, `KillMode=process` systemd unit; or
- a direct `ProgramArguments` launchd plist with restart-on-failure behavior.

Templates are emitted only; Systevisor does not write platform directories, run service-manager commands, or expose
its unit graph to either manager. Quoting is handled without a shell, including systemd percent escaping and XML
escaping. `KillMode=process` is important: the host stops the one opaque manager, and Systevisor performs its own
owned, deadline-bound child delegation.

## Docker harness

The opt-in harness creates a fresh uniquely named container per context, bind-mounts a temporary directory containing
the artifact and scenario files, and unconditionally force-removes the container and volume state on exit. It does
not use Docker's `--init`, allowing the artifact itself to be PID 1.

Coordination uses a bind-mounted FIFO carrying structured NDJSON checkpoints. The host blocks in `select` with a hard
deadline; there are no arbitrary sleeps or log-text polling. Container exit uses `docker wait` with a timeout. On
failure, the harness includes container logs in its exception. The first scenario runs the artifact in
`python:3.8-slim`, launches a selected oneshot collection, and has the child report that its parent PID is 1.

These tests require `SYSTEVISOR_DOCKER_TESTS=1`. The current sandbox has a Docker client but no reachable daemon, so the
scenario could not be executed here; normal/default and Python 3.8 suites verify that it skips cleanly. The harness
itself is ready for a workstation or CI runner with an explicitly enabled daemon.

## Verification

Focused verification at this checkpoint covered:

- manager runtime setup/live-field policy;
- locked and replacement-safe pidfiles;
- owned logging handler replacement;
- systemd datagrams and both template formats;
- unknown-child reap and owned-child exclusion;
- default and Python 3.8 package suites;
- fresh artifact generation, isolated namespace loading, and Python 3.8 `-I` command execution; and
- Ruff/mypy over the complete `x/systevisor` tree.

The repository-wide `make fix gen check` and final full suites are run immediately before the phase commit.

## Next

The next discrete phase builds scheduling over the deterministic deadline foundation. It should keep calendar
calculation, missed-run policy, and persistence independent: wall time selects an occurrence; monotonic time arms it;
an atomic store records only the durable facts needed to decide what was missed after restart. Scheduled work should
submit the same typed control commands as HTTP/CLI rather than acquiring a separate path to process resources.
