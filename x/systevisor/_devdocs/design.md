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

## Configuration transaction

Sources are discovered deterministically, parsed by extension, merged with strict duplicate rules, explicitly
rendered, unmarshaled, semantically validated, normalized, and hashed. Only a complete candidate becomes a desired
snapshot. A failed live candidate records diagnostics but produces no reconciliation effects.

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

All wait and signal call sites are confined and checked statically. Unknown adopted processes have no control
capability and are only reaped.

## Event and operation ordering

Inputs are processed serially. A state transition is committed before its event is published. Subscribers may enqueue
new commands but may not reenter the engine. Every event receives an epoch and monotonic sequence. A bounded journal
supports replay; each stream has an independent bounded queue and gap/disconnect behavior.

API requests which cannot complete immediately create operations. The CLI may wait by following operation events, but
the HTTP handler never blocks the reactor waiting for a process transition.

## Time

Relative lifecycle, restart, health, and shutdown deadlines use a monotonic clock. Calendar schedules use wall time
only to calculate the next occurrence, then arm a monotonic deadline. Wall-clock jumps cause recalculation rather than
corrupting relative process timers.

## Output

Child stdout/stderr are byte streams. A channel fanout drains the pipe into a byte-offset ring and configured sinks.
Streaming clients read ranges and receive an explicit gap if requested bytes were evicted. Slow clients never apply
backpressure to the child pipe. Text decoding is an adapter with explicit error policy.

## Health

Health is observed state, not process ownership. Startup probes gate the transition into ordinary readiness/liveness
policy. Readiness gates dependents and availability. Liveness can request recovery. All probe executions are effects;
their results are facts. Transient command probes use the same owned child machinery as services.

## Self-update preparation

Every live OS resource is registered with owner, kind, descriptor, closure policy, and exec inheritance policy. A
future update freezes command acceptance and reactor dispatch only after no signal lease/effect is active. The final
state snapshot and inheritance manifest are versioned. The new image validates parenthood, descriptors, process birth
identity, and schema before resuming.
