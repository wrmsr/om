# Development 06: health and owned probe execution

## Intent

Make health policy a deterministic part of reconciliation rather than a runtime side channel. Probe scheduling,
thresholds, startup eligibility, readiness, recovery, and stale-result handling belong to the pure engine; only the
individual observation belongs to an OS adapter.

## Engine model

- Added globally monotonic health-check identities distinct from service run identities and generic lifecycle deadline
  identities.
- Each configured probe has serialized state: config digest, role, status, threshold counters, last start/completion/
  success times, last message/data, scheduled deadline, in-flight check, and recovery latch.
- Startup stability and startup health are independent gates. A service reaches `RUNNING` only after `start_secs` has
  elapsed and every startup probe has crossed its success threshold, in either order.
- Readiness is independent from process lifecycle. No readiness probes means a running service is ready; otherwise all
  readiness probes must be passing. Existing `requires: ready` dependencies now respond to readiness changes in the
  same reconciliation step.
- Liveness and startup failures can apply `none`, `restart`, or `stop` recovery after their failure threshold. Restart
  still travels through the ordinary owned-run stop and replacement path; stop changes desired state with an explicit
  health origin.
- Probe intervals are engine deadlines and results are facts. A changed probe definition replaces its state and makes
  an older in-flight result stale. Run replacement similarly invalidates every old check.
- Live health edits preserve unchanged probe histories by config digest, schedule newly relevant probes, remove stale
  schedules without needing timer cancellation, and immediately recompute startup/readiness gates.

## Runtime probes

- Added an injected health-runner interface and an fdio implementation. The runtime supports process ownership checks,
  TCP connects, plain-HTTP requests, command exit status, and stdout/stderr activity.
- TCP connects are nonblocking. HTTP connects transition into an
  `omcore.io.pipelines` fdio driver containing the omcore HTTP request encoder and response decoder; the probe never
  uses urllib, threads, asyncio, or a blocking HTTP client.
- HTTP configuration is deliberately plain `http://` for now. TLS needs an fdio TLS pipeline and explicit trust
  configuration rather than an accidental blocking fallback.
- Log activity uses the injected monotonic clock and the channel's creation/last-append time. A captured channel that
  has not emitted yet is therefore measured consistently rather than being indistinguishable from an uncaptured
  channel.
- Every check has a runtime timeout even if its adapter stalls. Network handlers are closed on timeout. Completion is
  idempotent, so an fd becoming ready concurrently with timeout cannot produce two facts.

## Command ownership

Command probes intentionally do not use `subprocess` and are not anonymous children. The process manager creates them
through the same fork/exec preparation, identity switching, environment setup, exec-error handshake, pidfd, `WNOWAIT`
observation, and explicit reap path as services.

Health command runs occupy a reserved negative internal run-ID namespace and carry an explicit
`HEALTH_COMMAND` purpose plus health-check identity in process state schema version 2. Service run IDs are required to
be positive, so the namespaces cannot silently collide. The runtime coordinator routes exec and exit observations for
the reserved run back to the health runner rather than into the service state machine.

Commands always get an isolated session. Timeout selects process signaling until the exec handshake establishes that
session ownership, then session signaling. Both paths go through a process-manager signal lease; group cleanup after
leader exit likewise retains the leader's wait right. No raw PID or process group can enter the health API.

## Validation and testing

Validation now rejects zero/negative intervals and timeouts, invalid thresholds, NUL-bearing command arguments,
unsupported HTTP schemes/methods/statuses, invalid TCP ports, and invalid log channels/quiet periods.

Pure tests drive startup gates, readiness thresholds, dependency release, liveness recovery, live-edit staleness, and
state round trips with virtual time and no sleeps. Runtime tests use explicit fd checkpoints and hard outer deadlines:

- log activity is checked directly with a fake clock;
- a real command probe is observed as an owned child and gates startup;
- TCP and HTTP readiness probes run against an in-process fdio/pipeline server;
- a process probe confirms the service run remains in the owned running state.

## Problems found and decisions

The first command design considered a second child manager. That would have split wait ownership and complicated
SIGCHLD routing. Reserved typed runs in the existing manager keep one authoritative child table and make future state
rehydration explicit.

A command timeout cannot always signal its session: before a successful exec handshake the child may not yet have
called `setsid`, and the parent has not recorded the isolated-session capability. Timeout therefore examines only the
owned state record to choose the capability scope; it never speculates from a PID.

Health deadlines share the engine deadline ID sequence but live in per-probe state, allowing lifecycle and multiple
probe timers to coexist without widening the old single lifecycle timer fields. Stale timer delivery is harmless and
observable.

## Next

Finish Phase 6 with collection-level desired state, `stop_together` failure propagation, compose-style foreground
operation semantics, and focused collection tests. Composite probes remain deferred until there is a concrete boolean
composition syntax; silently inventing one would freeze the wrong configuration contract.
