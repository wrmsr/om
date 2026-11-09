# Development 10: observation and platform capabilities

## Goal

Add useful psutil-style awareness and optional Linux containment without creating any route around run ownership,
single-threaded fdio operation, transactional config, lite compatibility, or future rehydration. This phase also had
to turn the existing child modifier hook into a real lifecycle boundary instead of a child-only callback.

## Configuration surface

The manager now has nested `observation` and `cgroups` configuration. Observation controls enablement, monotonic sample
interval, ended-run retention, and optional per-sample event emission. `cgroups.root` is an explicit delegated cgroup
v2 directory; it is immutable across live reload because changing it changes process-global ownership assumptions.

Each unit has nested `resources` config:

- `observe` is a live policy switch;
- `cgroup` selects membership plus CPU weight/quota, memory low/high/max, and PID maximum;
- `namespaces` selects Linux mount, IPC, UTS, network, and cgroup namespaces plus an optional UTS hostname; and
- `inherited_sockets` names activation descriptors to copy into this unit.

Cgroup, namespace, and inherited-socket changes are restart-required. Validation catches missing roots, invalid ranges,
hostname/UTS mismatches, and duplicate/invalid socket names. Runtime preparation catches unavailable namespaces,
non-delegated roots, disabled controllers, and socket names not present in the inherited registry before the engine can
change desired state.

## Read-only resource observation

`SystevisorProcessResourceSampler` is injected. The Linux implementation parses `/proc/PID/stat`, `/status`, and `/io`
without importing the old non-lite diagnostic package. It compares the recorded birth identity to stat field 22, reads
the other files, then reads stat again and rejects a changed identity. The Darwin implementation calls
`proc_pidinfo(PROC_PIDTASKINFO)` through ctypes. Both return the same optional typed cumulative counters.

`SystevisorResourceObserver` is an fdio deadline handler and config participant. It sees only positive, service-purpose
owned-process snapshots whose unit has observation enabled. Samples are keyed by run ID and carry both monotonic and
wall timestamps. CPU percentage and byte rates use monotonic deltas; counter rollback yields an unknown rate instead
of nonsense. First failures and recoveries emit typed events, while routine sample events remain opt-in. Ended states
are bounded by `retained_runs`.

The API exposes all state at `GET /v1/resources`, one run at `GET /v1/resources/{run}`, and the CLI mirrors both with
`resources [RUN]`. A returned PID is diagnostic data only: no API endpoint accepts it and no observer code imports a
wait or signal primitive.

## Cgroup v2

The parent prepares a unique, hash-suffixed run directory beneath the configured delegated root, writes configured
control files, and opens `cgroup.procs`. The FD is an explicit child capability. After fork and before identity drop,
the child writes `0` through it, meaning itself; no component takes a numeric PID and converts it into cgroup control.
The parent closes its preparation FD after spawn.

Aggregate CPU, memory, swap, PID, and block-I/O counters supplement the direct-process sample. Retirement removes an
empty group. A populated group is retained and swept on fdio deadlines, including when ordinary observation is off.
This handles descendants which finish shortly after their direct parent without either sleeping or killing them.
There is intentionally no `cgroup.kill` use. Cleanup failures remain visible state and retry.

The configured root must already be delegated and have needed controllers in `cgroup.subtree_control`. Automatically
moving the manager, enabling ancestor controllers, or editing a service manager's hierarchy would exceed the authority
expressed by unit config, so this phase refuses instead.

## Namespaces

An injected backend wraps libc `unshare`, recursive-private mount propagation, and `sethostname`. It runs before
identity reduction and reports failure over the ordinary close-on-exec status pipe. Health-command runs skip isolation
modifiers because they occupy the negative internal run namespace.

PID namespaces were intentionally omitted: `CLONE_NEWPID` affects subsequently created children and would require an
extra fork, changing which process Systevisor owns and waits. User namespaces need synchronized UID/GID map setup from
the parent. Both deserve explicit protocols and fault tests rather than a misleading boolean.

## Inherited sockets and FD collisions

The activation registry is resolved before manager daemonization. It accepts systemd-style descriptors only when
`LISTEN_PID` matches, verifies every descriptor is a socket, rejects duplicate/incomplete names, marks originals
close-on-exec, and consumes the activation environment. Those originals remain manager-owned for repeated spawns and
future handoff.

A unit selects socket names. Per spawn, the modifier duplicates only selected sources to high temporary descriptors.
The child allowlist retains them, maps them to 3..N, marks the targets inheritable, and creates child-correct
`LISTEN_PID/FDS/FDNAMES`. The process manager asks modifiers for reserved targets and relocates its exec-status FD when
necessary. This avoids the classic silent collision where socket fd 3 overwrites the only child-setup error channel.

Launchd's named socket acquisition API is not implemented yet. The registry seam is platform-independent enough for a
future adapter, but inventing untested ctypes bindings here would be worse than the explicit current limitation.

## Process lifecycle seam

`SystevisorChildModifier` now has parent preparation, successful/failed spawn, child environment, preserved/reserved
FD, pre/post-identity, and retirement hooks. Process objects retain their child context until explicit reap. Cgroup and
socket cleanup therefore follows the same wait-owned run lifecycle, and future self-update state can enumerate these
capabilities rather than infer them from ambient descriptors.

## Verification

Pure/fake tests cover proc-stat parsing with parentheses in command names, monotonic rate math, injected sampling
failure/recovery, ended-run state, candidate rejection, prepared cgroup membership, descendant cleanup wakeups,
namespace flags, socket capture/selection, config validation, and restart classification. The existing real POSIX
contract suite adds one targeted fork/exec case proving a named socket arrives as fd 3 with child-correct activation
environment. It does not use an arbitrary sleep.

The final phase verification has 102 tests. On the default interpreter, 101 pass and only the opt-in Docker scenario
skips. Python 3.8 passes all 102 with the Docker scenario and development-only amalgam regeneration check skipped. The
checked artifact is regenerated, compared byte-for-byte, and launched under isolated Python 3.8.

## Next

Phase 10 turns the resource facts established so far into an explicit inheritance manifest and versioned runtime
snapshot. The first self-update slice should be non-destructive: inventory every owned FD, classify preserve/close
policy, serialize state, and let a probe image validate it without taking ownership. Freeze and in-place exec should
come only after that schema and its rejection paths are heavily fault-injected.
