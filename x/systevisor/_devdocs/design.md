# Design

## Boundary

Systevisor is split into a deterministic engine and an effect-executing runtime. The engine receives commands and
observed facts, updates serializable dataclass state, emits effects, and commits events. It does not call clocks,
`fork`, `wait`, signal functions, file APIs, or network APIs. The runtime owns those capabilities and feeds their
results back as facts.

Dependency injection assembles long-lived boundaries: clock, process manager, reactor, resource registry, config
source, storage, health runners, log sinks, and transports. Data objects and changing config are ordinary arguments,
not injector bindings. Reload never reconstructs the injector.

## Identity hierarchy

- A unit is configured behavior.
- An instance is a stable replica slot of a unit.
- A run is one execution generation of an instance.
- A collection is a compose-like selection/grouping of units.
- A process session/group is a kernel resource belonging to one run and is never called a collection.

Names are stable mapping keys. Renames are remove/add unless an explicit future stable ID says otherwise. A run ID,
not its current PID, appears in effects and events.

Collection, unit, and dependency desire are explicit claims with documented precedence. An inactive configured
collection contributes no claim; a manually stopped or failed collection contributes a veto; more specific unit and
instance overrides win. Dependency claims are a recomputed transitive closure and disappear when their final active
dependent disappears.

## Configuration transaction

Sources are discovered deterministically, parsed by extension, merged with strict duplicate rules, explicitly
rendered, unmarshaled, semantically validated, normalized, and hashed. Only a complete candidate becomes a desired
snapshot. A failed live candidate records diagnostics but produces no reconciliation effects.

Runtime-owned config consumers participate in a two-phase transaction. They prepare reversible resources against a
complete candidate before the engine sees it, then commit only after snapshot acceptance. Preparation failure becomes
a config diagnostic and rolls back all earlier participants. HTTP listener binding is the first implementation of this
contract.

Each instance records desired and applied specification hashes. The reconciler classifies changed fields. Live policy
or sink changes update in place; execution changes create a replacement run; grouping-only changes adjust the graph.

## Process capability model

The child process manager is the sole creator and waiter of managed children. A live owned-process handle contains the
run identity, direct-child PID, birth information, optional pidfd, wait state, and optional isolated-session identity.
It is not serializable as an object; its resource facts have a separate state representation.

A signal effect identifies a run and scope. The runtime obtains a non-reaping lease from the process manager. The
actual signal primitive accepts that lease rather than an integer. Individual Linux signals use pidfds when possible.
Portable direct-child signaling relies on the invariant that the manager has not reaped the child. Group signaling
requires a new session and retains the leader's wait right through shutdown/escalation.

Manager-originated signal forwarding is configuration, not ambient proxy behavior. Reserved termination signals enter
ordered shutdown, HUP enters transactional reload, and CHLD enters wait observation. Other configured catchable
signals are dynamically installed, normalized, submitted as typed engine commands, rewritten per unit, and emitted as
run-scoped signal effects. A session forwarding scope is restart-required so the child was already prepared as an
owned session leader.

All wait and signal call sites are confined and checked statically. Unknown adopted processes have no control
capability and are only reaped.

Child modifiers have explicit parent-prepare, parent-spawned, failed-spawn, child-pre-exec, and parent-retired hooks.
Preparation happens before `fork`; failures unwind prepared capabilities before any child exists. The child closes all
ambient descriptors except the exec-status pipe and descriptors named by modifiers. Reserved child descriptor ranges
can force relocation of the exec-status pipe, preventing activation sockets from silently overwriting it.

## Host boundary

Manager bootstrap happens only after a complete cold candidate has compiled and before the injector constructs the
reactor or any managed child. The injected platform runtime owns daemonization, cwd/umask and resource-limit setup,
manager identity reduction, Linux subreaper setup, process title, manager logging, the locked pidfile, and service
notification. Fields which establish process-global bootstrap state are immutable during live reload. Manager log
settings, ANSI policy, and a non-null process-title replacement are live fields and participate in the same prepared
configuration transaction as HTTP listeners.

The pidfile is an open, exclusively locked capability rather than a stale PID hint. Cleanup compares device/inode and
will not unlink a path replaced by another actor. It is manager coordination only and is never converted into a child
signaling capability.

On Linux, direct children are enumerated through procfs for unknown-adoptee cleanup. The process manager first excludes
every PID in its owned-run map, observes an unknown exit with `waitid(..., WNOWAIT)`, and reaps it without ever creating
a signal lease. Reap polling remains active when configured even if no managed run exists, covering PID 1 startup
races and already-zombied adoptees.

systemd sees Systevisor as one `Type=notify` service and receives readiness/stopping datagrams. Its generated unit uses
`KillMode=process`, leaving delegation and draining to Systevisor rather than exposing children as platform units.
launchd likewise receives a single direct-exec plist. Neither adapter projects the internal unit graph outward.

## Observation and isolation

Resource samples are observations of an owned run, never a source of process authority. The sampler receives an
owned-process snapshot and indexes its result by run ID. Linux procfs sampling reads stat/status/io, checks the
recorded start-time identity before the sample and again after all other reads, and reports CPU, memory, faults, I/O,
thread, and context-switch counters. Darwin uses `proc_pidinfo(PROC_PIDTASKINFO)` through ctypes. The observer derives
rates from monotonic deltas, records failures and recoveries, retains a configured number of ended runs, and exposes
the latest typed state through HTTP. It does not signal, wait, or discover arbitrary PIDs.

Cgroup v2 is optional and requires an explicitly configured, already delegated root. Preparation verifies cgroup-v2
control files and every controller needed by configured limits. A per-run directory and `cgroup.procs` FD are prepared
in the parent; after `fork`, the child writes `0` through that FD before dropping identity. Systevisor never writes
`cgroup.kill`. CPU, memory, PID, and aggregate descendant I/O counters are observable. Empty groups are removed;
populated descendant groups are retained and retried by an fdio deadline even when ordinary sampling is disabled.

Linux mount, IPC, UTS, network, and cgroup namespaces are optional child-pre-exec capabilities backed by injected
ctypes syscalls. A new mount namespace is made recursively private, and UTS can set a hostname. PID namespaces are not
offered because they require another fork and would break direct-child wait ownership. User namespaces are not offered
without a parent/child UID/GID-map protocol. Unsupported hosts reject the candidate during runtime preparation.

Systemd-style activation sockets are captured before daemonization only when `LISTEN_PID` names the manager. The
registry verifies socket descriptors, gives them collision-safe names, sets close-on-exec in the manager, and owns
them until shutdown. Units opt into names explicitly. Each spawn duplicates only those descriptors, maps them to the
contiguous range beginning at 3, and creates child-correct `LISTEN_PID`, `LISTEN_FDS`, and `LISTEN_FDNAMES` values.
Unknown names reject configuration before reconciliation. Launchd named-socket acquisition is not implemented yet.

## Artifact boundary

`__main__.py` is the amalgamation root and continuously generates `_bin/systevisor.py`. The checked-in artifact has
only standard-library imports and is loaded from an unrelated temporary path in tests, so package/PYTHONPATH leakage
cannot satisfy missing internal imports. Development-time regeneration is compared byte-for-byte. Python 3.8 loads
and executes the checked artifact even though the development amalgamator itself now requires a newer interpreter.

## Event and operation ordering

Inputs are processed serially. A state transition is committed before its event is published. Subscribers may enqueue
new commands but may not reenter the engine. Every event receives an epoch and monotonic sequence. A bounded journal
supports replay; each stream has an independent bounded queue and gap/disconnect behavior.

API requests which cannot complete immediately create operations. The CLI may wait by following operation events, but
the HTTP handler never blocks the reactor waiting for a process transition.

Finite control responses close their HTTP connection. Follow responses use chunked NDJSON and receive same-thread
event/log callbacks through pipeline notifications. Each stream has a bounded application queue and emits a gap record
after eviction; transport backpressure never reaches child-pipe draining.

## Time

Relative lifecycle, restart, health, and shutdown deadlines use a monotonic clock. Calendar schedules use wall time
only to calculate the next occurrence, then arm a monotonic deadline. Wall-clock jumps cause recalculation rather than
corrupting relative process timers.

The first calendar implementation accepts classic five-field cron in UTC. Each schedule records the last occurrence
it evaluated, not merely the last action it fired. Missed-run policy selects skip, latest, or a bounded all; concurrency
policy can suppress a fire while the prior operation remains pending. A schedule invokes the ordinary control service,
so restart/start/stop/shutdown has exactly the same validation, events, and process ownership path as HTTP or CLI.

Durable schedule state is a versioned atomically replaced JSON file beneath the effective state directory. A matching
per-schedule fingerprint resumes its last evaluated occurrence; a changed definition establishes a new current-time
baseline and never reinterprets old occurrences under new policy. The store is injected so SQLite or another backend
can replace it if history or distributed claims eventually justify that complexity.

## Output

Child stdout/stderr are byte streams. A channel fanout drains the pipe into a byte-offset ring and configured sinks.
Streaming clients read ranges and receive an explicit gap if requested bytes were evicted. Slow clients never apply
backpressure to the child pipe. Text decoding is an adapter with explicit error policy.

Rotating files, manager stdout/stderr, and an injected syslog writer are independent sinks. File output without an
explicit path derives a run-specific filename beneath the absolute child-log directory; cold cleanup can remove only
that generated filename namespace. A sink exception detaches that sink and emits an event without interrupting pipe
drainage or the byte ring.

## Health

Health is observed state, not process ownership. Startup probes gate the transition into ordinary readiness/liveness
policy. Readiness gates dependents and availability. Liveness can request recovery. All probe executions are effects;
their results are facts. Transient command probes use the same owned child machinery as services, carry an explicit
process purpose, and occupy a reserved internal run namespace. Network probes use nonblocking connects and the omcore
fdio/HTTP pipelines. Runtime timeouts close or signal only capabilities held by the probe runner.

## Self-update and handoff

Self-update is an in-place `exec` of one generated amalgamated artifact into another. The candidate is first run as an
internally owned probe child and validates its pinned digest, handoff schema, and active configuration. Only a stable
reactor state may proceed: no process may be starting/stopping, no health or internal child may be active, no effect
or input may remain queued, no signal lease may be held, and no unrelated operation may be pending.

The final versioned JSON manifest includes the configuration and provenance, deterministic engine, direct-child
ownership facts, output-reader descriptors and byte rings, event cursor/journal, operation history, manager/pidfile
state, activation sockets, and cgroup bookkeeping. Each inherited FD records a unique semantic owner plus `fstat`
identity and status flags. The old image writes and fsyncs the manifest before transactionally clearing `FD_CLOEXEC`
on only that inventory. A failed `execve` restores every original flag.

The new image verifies its own path/digest, the unchanged manager PID, every descriptor, direct-child wait rights,
pidfd identity, and process birth identity before rebuilding injected runtime objects. It then restores `FD_CLOEXEC`,
rebinds disposable HTTP listeners, and completes the still-pending update operation. A failure during reconstruction
execs the digest-pinned previous artifact with the same manifest; a successful rollback records the update operation
as failed while preserving the manager PID and children. Accepted HTTP connections are deliberately disposable and
clients reconnect. Only generated self-contained amalgamations are accepted as the running and candidate artifacts.
