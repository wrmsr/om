# Development 07: collection reconciliation and foreground runs

## Intent

Complete the first compose-like unit of management without treating a collection as a Unix process group. A
collection is a desired-state claim over configured units, an aggregate status, and a failure policy. Individual runs
retain their own process/session ownership and dependency behavior.

## Desired claims

The engine now serializes collection state independently from instance state: typed name, desired flag/origin,
aggregate status, activation sequence, and a latched failure instance/reason. Configured `autostart` collections claim
their units at initial reconciliation; the `run` entrypoint can instead select exactly one startup collection and
suppress unrelated unit and collection autostart.

Effective unit desire has explicit precedence:

1. shutdown;
2. instance or unit manual override;
3. an explicit stopped collection or a latched `stop_together` failure veto;
4. an active collection claim;
5. ordinary unit autostart.

An explicit unit/instance start can therefore recover one resource despite a broader collection veto. A collection
configured inactive is not a veto: it simply contributes no claim. This distinction permits overlapping collections
without making every inactive grouping shut down shared units.

Starting a stopped collection clears its failure latch and increments its activation sequence. Reactivation resets a
terminal oneshot/FATAL instance only when effective desire actually crosses inactive to active; ordinary reconciliation
does not accidentally rerun a completed oneshot or clear a persistent fatal state.

## Dependency claims

The earlier dependency propagation mutated an inactive dependency to config-active and never released it. That was
acceptable for simple startup tests but wrong for a collection: stopping a web stack could leave the database it had
pulled in running forever.

Dependency desire is now recomputed as a transitive closure on each engine input. Config/collection/dependency-managed
instances first get their base claim; active manual and base units seed `requires`/`wants` traversal; the closure gets
an explicit `DEPENDENCY` origin. Removing the last seed releases the dependency in the same reconciliation step.
Explicit unit stops and instance/health stops remain stronger and can leave dependents observably blocked.

## Aggregate state and failure

Collection status is one of `INACTIVE`, `STARTING`, `READY`, `STOPPING`, `DEGRADED`, or `FAILED`.

- Services are ready only when `RUNNING` and readiness-true; oneshots are ready after a successful observed exit.
- A readiness probe which has crossed into failing makes an active collection degraded; an initial/pending readiness
  check remains starting.
- Fatal startup, a non-restarted terminal service exit, or health recovery `stop` is a member failure.
- With `stop_together: true`, the first such failure latches the collection failed, installs a collection-failure veto,
  and reconciles all peers toward stopped. All signals remain ordinary run-scoped effects.
- With `stop_together: false`, the collection stays desired and becomes degraded, allowing unaffected members to
  continue.

Collection desired/status transitions have first-class engine events. The control service now waits for collection
`READY`/`INACTIVE`, rather than pretending that a collection operation is merely a snapshot of member operations.
Unit and collection starts also respect readiness; they no longer report success at bare `RUNNING` when readiness
probes are configured.

## Foreground compose mode

`./python -m x.systevisor run COLLECTION -c PATH [...]` uses the normal injected runtime, transactional config
controller, HTTP control plane, signal manager, process kernel, logging, and health machinery. Before initial reload it
records a serialized startup-collection selector. Reconciliation then activates only that collection (plus transitive
dependencies), even if unrelated units or collections say `autostart`.

The runner remains in the foreground while services are healthy. It exits zero when an all-oneshot collection
completes or an operator stops the collection, exits one after a collection failure/degraded terminal set, and exits
two for invalid config, a missing selected collection, or its removal on reload. In every terminal case it submits the
normal reconciled manager shutdown and drains owned children before returning. SIGTERM/INT/QUIT use the same path.

The selected config's Unix/TCP API remains available during the run, so the mode is not a separate miniature runtime.
`GET /v1/collections` and the `collections` CLI command expose aggregate state.

## Testing

Lock-step tests cover autostart claims, manual stop veto/restart, failure latching and peer stop, degraded non-coupled
collections, startup selection, explicit unit precedence, transitive dependency release, oneshot reactivation, and
state round trips. Control tests cover readiness-aware collection operations and API state. Entrypoint tests invoke
`systevisor_main` in-process with real fork/exec boundaries: a selected oneshot completes while an unrelated autostart
unit provably never runs, and an unknown selection starts nothing.

No test uses `time.sleep`; real boundaries use fdio polling with hard outer deadlines.

## Next

Phase 7 turns the working package into its deployable artifact: a continuously tested single-file amalgamation,
manager logging/process title/PID-1 behavior, opaque systemd/launchd integration, and the reusable one-container-per-
test harness requested for difficult platform bugs.
