# Development 02: deterministic lifecycle engine

## Intent

Turn desired snapshots into a pure, serial transition system before introducing a reactor or real process. The engine
must be exhaustively drivable by injected facts and virtual time, and it must never expose an integer PID as a control
target.

## Model

- Inputs are commands or observed facts. Time is an explicit `now` argument, never read from a clock.
- Outputs are effects and immutable, monotonic-sequence events.
- Effects address process runs by `SystevisorRunId`; the future runtime alone will resolve a run to an owned process
  capability.
- Instances retain stable `unit:slot` identity while each spawn receives a new monotonic run ID.
- Deadline effects have unique IDs. Superseded deadline facts are harmless and observable as stale.
- Armed deadline IDs, kinds, and absolute monotonic targets are retained in engine state for later rehydration. Engine
  input time is monotonic and time reversal is rejected.

## Lifecycle work

- Implemented STOPPED, STARTING, RUNNING, BACKOFF, STOPPING, EXITED, FATAL, and UNKNOWN vocabulary with separate
  desired state and desired-origin axes.
- Added startup confirmation/stability windows, bounded exponential backoff, retry exhaustion, expected/unexpected
  exit handling, explicit restart, graceful stop, and deadline-driven escalation.
- Added stale run-fact rejection. A late exit for an old run cannot mutate its replacement.
- Added shutdown behavior and priority-ordered start/reverse-priority stop ordering.
- Added hard dependency conditions (`started`, `running`, `ready`, `completed`) and soft ordering for `wants`, `after`,
  and `before`. Required/wanted units are activated transitively unless a manual stop override exists.

## Reconciliation work

- Snapshot application adds/removes replica instances and preserves stable ones.
- Unit changes are classified by child-FD topology and process setup. Exec, identity, stdin, redirect, and FD-topology
  changes require replacement. Restart/stop policy, dependency/health policy, priority/tags, and managed output sink
  changes apply live.
- Removed live instances are stopped before their state is forgotten. Identical snapshot content is a process no-op.
- Manual desired overrides survive config reloads; config-owned desired state tracks autostart.

## Testing

The engine harness owns virtual monotonic time and a deadline queue. Tests explicitly acknowledge spawn effects,
inject exits/failures, and advance to deadlines. They cover dependency gating, stable startup, retry/fatal behavior,
live versus replacement config, removal, session-scoped escalation, stale facts, shutdown ordering, and identical
config no-ops without sleeps or subprocesses. The live engine state is also round-tripped through the lite marshaler
while a deadline is armed, and identical input/time traces are asserted to produce identical outputs and state.

## Next

The owned-process kernel will execute these effects. Its API will intentionally make unsafe use awkward: no public
signal method accepts a PID, wait ownership is centralized, and signal delivery requires a live anti-reap lease.
