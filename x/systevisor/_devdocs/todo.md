# Open work

What is known to be unfinished, untested, or undecided, as of the audit and hardening recorded in `dev_13` through
`dev_17`. Each item says how it is known: **reproduced** means it was seen happening, **read** means it follows from
the code and has not been run, **decision** means the code is waiting on a choice rather than a fix. Items are grouped
by what kind of work they are, not by importance; a suggested order is at the end.

Remove an item when it is done and say so in that phase's journal. Add to "Checked and dropped" when something
suspected turns out not to be a problem, so nobody spends the same afternoon on it twice.

## Gates that have never been run

Nearly every real defect so far was found by running the manager rather than reading it, and these are the places it
has not been run. They come before everything else here.

- **Docker scenarios.** `SYSTEVISOR_DOCKER_TESTS=1 ./python -m pytest -q x/systevisor/tests/test_docker.py` needs a
  Docker daemon, which no development sandbox so far has had. They are the only tests of the manager as PID 1 and of
  self-update inside a container under CPython 3.8. `tests/test_handoff.py` now covers the exec, resume, and rollback
  spine without Docker, but not PID 1: reaping adopted orphans, and being the process whose exit ends the container.
- **Root.** Nothing has run as root, so none of this has executed against a real kernel: dropping the manager's and a
  unit's identity (`setgroups`/`setgid`/`setuid` ordering), creating and joining a real cgroup v2 run group, writing
  real limit files, and `unshare`/mount/hostname in the child. The cgroup and namespace tests use fakes; the sweep of
  stale run groups was exercised against an ordinary directory tree only.
- **macOS.** The design names Darwin as a primary platform and nothing has been executed there. Known to differ and
  untested: the kqueue poller, no pidfds (so exits rely on `SIGCHLD` and the wait poll), no procfs (so no birth
  identity and no enumeration of adopted children), `libproc` sampling through ctypes, and the launchd plist.
- **A real systemd.** The generated unit (`Type=notify`, `KillMode=mixed`, optional `TimeoutStopSec`) has only been
  rendered and string-matched. Worth checking under an actual systemd: readiness and stopping notifications, that
  `MAINPID` holds across a self-update, and that a manager killed outright takes its children with it.
- **Real clock steps.** Scheduler behaviour across wall-clock jumps is tested with a fake clock only.

## Decisions

Things the code cannot settle by itself.

- **Self-update across schema changes.** A handoff is refused unless the new image accepts every state schema version
  exactly and marshals the active configuration to the same digest (`selfupdate/codec.py`, the probe in
  `selfupdate/runtime.py`). That fails closed, which is right, but it means a live update only works between images
  that did not change any carried state: the engine state schema alone went from 2 to 4 during the hardening phases,
  and the cgroup run schema from 1 to 2. As self-update is the reason much of the code is shaped the way it is, this
  is the largest open design question. Options run from "document that a schema bump means a restart" through
  one-version-back decoders in the new image, to explicit migrations carried with the artifact.
- **A deadline for operations.** A start or restart operation waits on instance state with no limit
  (`SystevisorControlService._refresh`). It now fails promptly when a run it is waiting on dies after reaching
  `running`, but it still waits forever on a requirement that never becomes ready, on readiness that never arrives,
  and on a unit held down because it follows a requirement. Under `concurrency: skip` a schedule whose operation never
  finishes is suppressed for as long. Needs a policy: a per-operation timeout, a default one, or failing as soon as
  the instance is blocked.
- **A subscriber that raises.** The event bus drops a callback subscriber for good the first time it raises, and most
  publishers discard the list of failures that would say so (`SystevisorEventBus.publish`, marked `TODO`). Losing the
  control service this way leaves every later operation pending; losing the reload hook makes `SIGHUP` do nothing.
  Choose between keeping the subscriber and reporting, marking it failed where an operator will see it, or treating
  it as fatal like any other failure in a part that drives the engine.
- **Following a crash.** `follow` on a requirement has `stop`, `restart`, and `failure`. A requirement that crashes
  and is restarted by its own restart policy is none of them, so nothing follows it. Whether that should be a fourth
  value (Erlang's `rest_for_one`) is open; the place for it is `SystevisorEngine._process_exited`, beside the existing
  call sites of `_propagate_restart`.
- **Failures in the scheduler, the resource observer, and the self-update handler.** These do not override
  `on_error`, so an exception in any of them is fatal: the manager stops its children and exits 70. That is the safe
  default and may be too strict for parts that are not needed to supervise - the alternative being a manager that
  carries on without schedules or samples and says so loudly.
- **Probing by name.** Health probe hosts must be IP literals or `localhost`, because there is one thread and no
  nonblocking resolver. If probing by host name is ever needed, it has to be resolved off the reactor - most plausibly
  in an owned helper process, the way command probes already run.

## Accepted for now

Recorded so they are not raised again as findings. Each is a deliberate position, not an oversight.

- **The candidate check is a format check, not a trust check** (`systevisor_self_update_is_amalgamated_source`, marked
  `TODO`). Anyone who can reach the control socket can have the manager exec a file of their choosing. Accepted on the
  terms the socket is deployed under: it is to be treated like the Docker daemon socket. Revisit before that access
  is ever widened.
- **The control API has no authentication.** Same terms. A TCP bind beyond loopback requires `api.allow_remote`.
- **`self_update.enabled` defaults to true.** Follows from the two above.
- **Priority is not waited on.** It orders units within a step, unlike Supervisor's sequential reverse-priority stop.
  The reasoning is in the block comment above `SystevisorEngine._stop_order`.
- **No external watchdog.** The reasoning is in `dev_17`: nothing but a parent can wait on the children, so a watchdog
  could only kill them and start again, which the surrounding service manager or container already does.

## Known gaps

Smaller than the above, and mostly independent of each other.

### Processes and identity

- **Supplementary groups survive an identity drop to a bare numeric uid.** *Read; needs root to confirm.* In
  `_systevisor_processes_resolve_identity`, a `uid` with no passwd entry yields no group list, and the child only
  calls `setgroups` when it has one, so the unit keeps the manager's supplementary groups (root's, typically). `gosu`
  clears them in the same situation. The same applies to a manager given only a `group`.
- **The manager wakes four times a second whenever it owns a process.** `SystevisorProcessWaitFdioHandler` polls
  `waitid` on a 250 ms interval as a backstop to `SIGCHLD` and pidfds. Harmless, but it is not an idle manager.
  Where pidfds exist the poll could be much slower or dropped.
- **Opening a unit's `stdin` file blocks the manager.** *Read.* `_systevisor_processes_open_input` opens the file in
  the parent with a blocking `open`, so a FIFO with no writer, or a stalled network filesystem, stops the reactor.

### Scheduling

- **Day fields beginning with `*/N` do not follow Vixie cron.** *Reproduced against the rule, not a cron binary.*
  Vixie treats any day-of-month or day-of-week field that starts with `*` as a star, which makes the two fields
  combine with AND. Here only a bare `*` counts (`wildcard = source == '*'` in `_systevisor_cron_parse_field`), so
  `0 0 */2 * 1` matches every other day or any Monday instead of Mondays that fall on such a day. A one-line change,
  but one that changes the meaning of existing expressions of that shape.
- **The cron parser accepts integers it should not.** *Reproduced.* `int()` lets through `+5`, `1_0`, and non-ASCII
  digits (`_systevisor_cron_parse_int`).

### Resources

- **Removed cgroup run records are only pruned when observation is on.** *Reproduced.*
  `SystevisorCgroupManager.prune` is called from the observer's sampling pass alone, so with
  `observation.enabled: false` every run that used a cgroup leaves a small record behind for the manager's lifetime.
- **Run groups that could not be removed are retried forever.** *Read.* `RETIRED_POPULATED` and `CLEANUP_FAILED`
  states are swept on every pass with no limit and never pruned.
- **Valid systemd socket activation is rejected in two cases.** *Reproduced.* Duplicate names in `LISTEN_FDNAMES`,
  which systemd produces for one `.socket` unit with several listeners, raise; so does `LISTEN_FDS` without
  `LISTEN_PID`, which should be ignored (`resources/sockets.py`).
- **A process name that is not valid UTF-8 breaks sampling for that run.** *Reproduced.* `resources/sampling.py` reads
  `/proc/PID/stat` in text mode. The observer contains the error but never recovers for that run.
  `_systevisor_processes_read_birth_identity` reads the same file the same way and only catches `OSError`.
- **Darwin CPU times are probably in the wrong unit on Apple Silicon.** *Read.* `pti_total_user`/`pti_total_system`
  are treated as nanoseconds; there they are Mach time units.
- **Namespace preparation checks the platform, not the privilege.** *Read.* An unprivileged manager accepts a config
  with namespaces and then fails every spawn with `EPERM`, instead of rejecting the config.

### Control API and CLI

- **No way to restart a unit or signal one through the API.** `SystevisorControlService.restart_unit` exists and is
  used by schedules, but only instances can be restarted over HTTP, and there is no signal route at all. A typed
  per-unit reload action (nginx `HUP`) is also listed as deferred in `compatibility.md`.
- **Control connections are unlimited and never time out.** *Reproduced in part.* An idle connection is kept
  indefinitely, there is no cap on how many are open, and the listener's backlog is 1 (`sock.listen(1)` in omcore's
  `ServerSocketFdioHandler`): with 200 idle connections held, a new client could not connect. Only reachable by
  someone who already has the socket.
- **`logs` without `--follow` prints base64 JSON.** Only the following form decodes the bytes
  (`_systevisor_main_client`).
- **The default client endpoint is in `/tmp`.** `unix:/tmp/systevisor.sock` is where the CLI looks when given
  nothing, though no manager listens there unless configured to.
- **`GET /v1/state` and `GET /v1/config` return every unit's environment.** By design, and worth remembering when
  deciding who may read from the socket.

### Logs and events

- **A sink that fails once is detached for the rest of the run.** `SystevisorLogManager.append` closes and drops a
  sink on any exception, so one full-disk moment or one `EAGAIN` on the manager's stdout ends that run's file or
  stdout output until the unit restarts. The byte ring is unaffected.
- **Writing child output to the manager's stdout is synchronous.** *Read.* `SystevisorFdLogSink` writes until done; if
  the manager's stdout is a pipe whose reader has stalled, the manager stalls with it.
- **Events carry only monotonic timestamps.** `SystevisorBusEvent.at` and `SystevisorEvent.at` come from the
  monotonic clock, which cannot be lined up with anything outside the process. A wall-clock field would have to be
  added to both and to the handoff codec.

### Self-update

- **The handoff manifest is written to the system temp directory when no state directory is configured.** It holds
  every unit's environment. The directory is created 0700 and the files 0600, so this is about predictability of
  location, not exposure (`SystevisorSelfUpdateManager`, `tempfile.mkdtemp(..., dir=state_directory)`).
- **The whole handoff is one JSON document capped at 64 MiB**, log rings included
  (`_SYSTEVISOR_SELF_UPDATE_MAX_DOCUMENT_BYTES`). Retention now bounds how many rings there are, but large
  `back_buffer_bytes` across many units can still exceed it. It fails safe: the update is refused and the old manager
  carries on.
- **An image that cannot run at all after the exec leaves its children to the host.** Not fixable from inside the
  process; see "No external watchdog" above. Listed so that the dependence on `KillMode=mixed` or PID 1 stays visible.

### Configuration

- **Relative paths resolve against the manager's working directory**, not the config file that names them. Only
  `child_log_directory` is required to be absolute, so a relative `api.unix_socket` or `state_directory` lands
  wherever the manager happened to be started.
- **The launchd plist has not been reviewed** against any of the changes that the systemd unit got.

### Housekeeping

- `mypy` reports three unused `type: ignore` comments, in `platforms/runtime.py`, `resources/namespaces.py`, and
  `resources/cgroups.py`. They are platform guards that the Linux run no longer needs.
- `tests/test_handoff.py` adds about fifteen seconds to the suite, nearly all of it the interpreter compiling the
  single-file artifact on every exec. Worth knowing before adding more scenarios to it.

## Checked and dropped

Suspected during the audit, tested, and not found to be a problem.

- **A unit that writes output as fast as it can does not starve the manager.** The read loop in
  `SystevisorProcessOutputFdioHandler` has no bound, but the pipe empties faster than `yes` fills it; the API stayed
  responsive and a `TERM` was honoured within a second, at the cost of one core.
- **A unit's last output is not lost at shutdown.** Eight runs of a unit printing from its `TERM` handler all kept
  the line.
- **Closing inherited descriptors is not slow on CPython 3.8 with a large descriptor limit.** Forty spawns took
  0.66 s at `RLIMIT_NOFILE` 1024 and 0.76 s at 524288.

## Before promotion out of `x/`

Not defects; the distance from this code to `CODESTYLE.md`.

- Most constructors do not call `super().__init__()`.
- Several modules are far past the few-hundred-line target: `core/engine.py` (about 1,700 lines),
  `runtime/processes.py` (about 1,350), `selfupdate/codec.py` (about 1,000), `configs/validation.py` (about 850).
  `main.py` holds the CLI parser, the server context, and the API client in one module.
- There is no package `README.md`. `_devdocs/operator.md` and `design.md` are most of what one would say.
- `make fix` and `make check` do not cover `x/`, so Ruff and mypy are run by hand until the package moves.

## Suggested order

1. Run the gates: Docker and a root host first, then a Mac, then a real systemd.
2. Decide what self-update does about schema changes.
3. Take the operation deadline and the raising subscriber together; both leave something pending forever.
4. Clear the known gaps in a batch or two, starting with supplementary groups once there is a root host to confirm it.
5. Promotion cleanup.
