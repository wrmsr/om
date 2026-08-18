# Development 00: initial architecture

## Objective

Start `x/systevisor` as a greenfield package after reading the old `x/supervisor` attempt, relevant omcore lite
infrastructure, upstream Supervisor behavior, gosu, dumb-init, nginx process control, and the separate non-lite daemon
experiments.

## Decisions entering implementation

- The center is a deterministic reconciliation engine with an OS reactor around it.
- The engine exchanges commands/facts/effects/events and never performs OS or clock operations.
- Runtime state is explicit, dataclass-heavy, versionable, and free of live object references.
- `omcore.lite.inject` composes stable capabilities; reload replaces desired data rather than the object graph.
- Unit, instance, run, collection, and Unix process session are separate concepts.
- Supervisor lifecycle names remain familiar but desired state, readiness, health, and generations are orthogonal.
- Configuration candidates are atomic. Rejected live candidates leave active state untouched; invalid cold starts fail
  loudly rather than silently using stale state.
- Config directories use deterministic ordering, strict duplicate definitions, and retained source provenance.
- Literal argv arrays and strings are the default. Minja is later, explicit, trusted, and snapshot-time only.
- Events are immutable, sequenced, replayable facts. HTTP streaming is bounded NDJSON by default.
- Child logs stay bytes through capture/back-buffer/file stages.
- The project will be prepared for self-update from the first resource and state types, although update execution is a
  late phase.

## Hard process-control decision

No supported signaling path will accept an integer PID or PGID. Effects identify run IDs. The child process manager
is the sole waiter and resolves a run to a live handle. A temporary signal lease prevents reaping while signal delivery
is in progress. Linux uses pidfds where possible; Darwin relies on direct-child wait ownership and an unreaped PID pin.
Group signaling requires a session created and owned by the run, and retains the direct leader until cleanup finishes.
Unknown PID 1/subreaper adoptees are reap-only.

This is stronger than the repo's external-daemon pidfile verification and intentionally rejects the direct `killpg`
style in `omcore.daemons.children`.

## Amalgamation decision

Amalgamation performs no name mangling. Every package-owned top-level symbol therefore includes `Systevisor`,
`systevisor_`, or a module-specific `_systevisor_<module>_` prefix. The rule includes private helpers, loggers,
constants, type aliases, registration functions, and exceptions. A source-level guard test will enforce it rather than
depending on review.

## Work started

- Created the lite package/subpackage skeleton.
- Added durable intro, research, requirements, design, plan, and this chronological journal.
- Added source-level checks for amalgamation-safe globals, confinement of signal/wait calls, and the absence of
  subprocess-based runtime machinery.
- Added an import smoke suite intended to run on both the repository default interpreter and the Python 3.8 lite
  environment.
- Next: verify and commit the foundation, then begin the configuration/domain phase.
