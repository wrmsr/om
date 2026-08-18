# omllm.core.processes — intro

`omllm/core/processes` is the subprocess manager for the om LLM harness: a single injector-managed `ProcessManager`
owning a tree of `ProcessScope`s (ui → agent → turn → tool-call), spawning arbitrarily long-lived, mostly non-python
child processes with streaming output, strict no-zombie / no-leak guarantees, and an LLM-friendly output model.

It is *not* a replacement for `omcore/subprocesses` (lite, run-and-done, amalgamation-friendly) and it does not
import `omcore/daemons`. It is custom built for the harness first; it may graduate to `omcore` later.

## Reading order for a new worker

1. `requirements.md` — what the user asked for, verbatim-ish, and the decisions taken.
2. `design.md` — the architecture: types, spool, scopes, launcher + shim, asyncio impl, invariants.
3. `research.md` — the stdlib facts we verified that the design depends on (pid ownership, Popen pitfalls,
   waitid(WNOWAIT), pipe transports, shim latency).
4. `dev_NN_*.md` — running journal, newest last. Start at `dev_00_initial.md`.

## Where things are

```
omllm/core/processes/
  types/     specs, TypedValues options, states, events, errors, ids
  spool/     framed output log: frames, storage (memory + spill), spool, renderers, text
  scopes/    ProcessScope tree + close policy
  handles.py abstract handle roles (ProcessInfo/Control/Stdin/Output/Waiter -> Process)
  manager.py ProcessManager (abstract) + ManagerConfig
  launch/    Launcher / SpecTransform / ShimLauncher
  _spawn/    the pure-stdlib spawn shim (runs in the child before exec)
  asyncio/   AsyncioProcessManager and friends (the only impl for now)
  tests/     pytest
  _devdocs/  these notes
```
