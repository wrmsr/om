# Development 13: runtime hardening after first audit

## Intent

The first hands-on audit ran the manager for real rather than through its fakes, and found that the deterministic core
held up while the shell around it did not: ordinary events could take the manager down, and taking the manager down
left its children running. This phase closes the failures that audit reproduced, without widening the feature set.

## Findings and changes

- A control client that disconnected - Ctrl-C on `events --follow` was enough - raised `BrokenPipeError` out of the
  shared reactor and killed the manager. The omcore pipeline driver fails its connection and then re-raises by
  contract, and health probes already wrapped it; control connections were registered raw. They now go through
  `SystevisorHttpConnectionFdioHandler`, which ends the one connection. The listener likewise survives `accept`
  failures and pauses, rather than spins, on descriptor exhaustion.
- Every exit other than an orderly shutdown orphaned the managed children, and a runtime failure was reported as
  `startup_failed`. The three copies of the main loop are now one, a failure while supervising is reported as
  `runtime_failed` with exit 70, and every exit path closes through `SystevisorEmergencyStop`, which stops whatever the
  process manager still owns using nothing else.
- The resumed-after-self-update loop was one of those three copies and had drifted: it never checked for a prepared
  exec, so a manager could self-update exactly once, and it treated any later runtime error as a failed resume and
  tried to roll back to an image it had already left. Sharing the loop fixes the first; only reconstruction is now
  inside the rollback handler.
- One failing effect abandoned the rest of its step, leaving the engine believing in spawns and signals that never
  happened. Effects are now independent, a spawn failure of any type is an ordinary start failure, and a spawn that
  fails in the parent after the fork kills and reaps the child rather than leaking it. An engine step that raises is
  recorded as fatal instead of being swallowed by whichever caller happened to contain exceptions.
- Log channels were only ever flagged retired: each run kept its ring, its sink descriptor, and its generated file for
  the life of the manager. Channels now settle once retired and at end-of-file, and are retained per instance up to
  `manager.retained_child_log_runs`.
- A unit that got past `start_secs` and then exited was respawned with no delay at all, which is what turned the leak
  above into descriptor exhaustion within seconds. Such restarts now follow the existing backoff curve, tracked in a
  new `unstable_restarts` instance field (engine state schema 3).
- Children inherited the interpreter's ignored `SIGPIPE`/`SIGXFSZ`. Worse, between `fork` and `exec` the child still
  ran the manager's handlers against the manager's wakeup descriptor, so a stop signal racing a spawn was swallowed by
  the child and delivered to the manager as its own `SIGTERM`. Signals are now blocked across the fork and reset in
  the child before anything else.
- The single-file artifact could not load YAML without pyyaml installed, and said so with an empty message: the
  default backend search can only find the bundled goyaml relative to a package, which a flattened artifact does not
  have. The config loader now pins the goyaml backend, which also stops a config parsing differently depending on
  what is installed beside the artifact.
- `tests/utils.py` imported non-lite `omcore.check`, so six test modules had silently stopped importing under CPython
  3.8. It now uses the lite check.
- Found on the way, in omcore: `Logger.exception('message')` with a lone message mistook the message for the
  exception, dropping it and emitting a logging error instead of the traceback. Fixed there with a regression test,
  since every containment path above reports through it. Two existing `error(..., exc_info=...)` calls, which that
  logger rejects outright, were corrected to `exception(..., exc_info=...)`.

## Deliberately not changed

- omcore's fdio manager still propagates handler exceptions and still never calls `FdioHandler.on_error`. Containment
  is per handler where it is sound, and anything else reaching the main loop is fatal on purpose.
- Shutdown is still not dependency-ordered, `requires` still only gates starting, and the control API still has no
  authentication or bind restriction. These were audit findings, not part of this phase.
- The scheduler's clock-step failures, the cgroup stale-directory collision, and the self-update trust check are
  unchanged, though the first two now end in a contained start failure or a clean fatal stop rather than orphans.

## Verification log

- Each fix has a regression test that was run against the pre-fix code and seen to fail for the reported reason: the
  disconnect test reproduces the original `BrokenPipeError`; the fork/exec test sees the swallowed `TERM` and the
  phantom manager signal; the log retention, backoff, effect isolation, and emergency stop tests likewise.
- Live reproduction of the flapping unit (`restart: always`, `start_secs: 0`, file output), 25 seconds: before, 1,495
  runs, 1,517 manager descriptors, 348 MB resident, 1,508 log files; after, 6 runs, 6 descriptors, 43 MB flat, 2 files.
- Live fault injection into the reactor of a manager supervising two children, one ignoring `TERM`: exit 70,
  `runtime_failed`, both children gone, the stubborn one after its own one-second stop timeout.
- The regenerated artifact serves a YAML config under an isolated CPython 3.8 with no third-party packages.
- Default interpreter: 138 passed, 2 Docker scenarios skipped. CPython 3.8 unittest discovery: 140 run, 3 skipped.
  Ruff clean; mypy reports only the three pre-existing unused-ignore notes.
- Docker, root, PID 1, and privileged cgroup/namespace paths were not exercised in this sandbox.

## Next

- Decide the control-API exposure rule for non-loopback TCP binds. The compile pipeline currently rejects on any
  diagnostic, so an explicit opt-in field is a smaller change than introducing non-fatal warnings.
- Dependency-ordered stop, and whether `requires` should propagate a stop to dependents.
- The remaining audit items listed above, each with tests that do not depend on Docker.
