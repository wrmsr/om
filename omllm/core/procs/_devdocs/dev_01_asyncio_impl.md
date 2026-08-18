# dev 01 — shim, scopes, asyncio impl, phase-1 complete (2026-08-17)

Phase 1 is done: a tested, injector-bindable `AsyncioProcessManager` with the full scope tree, spool, spawn shim,
teardown/escalation, and no-zombie guarantees. `make fix gen check` is clean; `./python -m pytest omllm/core/procs`
is 24 passed / 1 skipped (root-only credentials test), and the wider `omllm/{agent,harness,core}` suites still pass
(351/2skip together).

## What landed since dev_00

- **`_spawn/shim.py`** — the pure-stdlib child shim. marshal payload (not json: 0ms import, carries bytes), applies
  umask/rlimits/gosu-credentials/deathsig(Linux)/chdir, scrubs fds (status fd made non-inheritable, payload fd
  closed), resets SIGPIPE/SIGXFSZ + clears the blocked signal mask, then `execvpe`. Reports pre-exec failures as a
  marshal'd `(stage, errno, msg)` over the status fd; EOF-with-no-data == exec succeeded. ~10-12ms/spawn.
- **`launch/`** — `Launcher`/`SpecTransform`/`LaunchPlan`; `ShimLauncher` (bootstrap `python -I -S -c`, payload in an
  unlinked temp file); `ShellWrapTransform` (wraps `omcore.subprocesses.wrap`), `EnvScrubTransform`.
- **`scopes/`, `handles.py`, `manager.py`** — the loop-agnostic tree + roles + abstract manager (`ScopeOps` is the
  impl hook so scopes stay asyncio-free).
- **`asyncio/`** — `_SpawnerPopen` (no-op `__del__`, all wait/signal methods raise), `ExitWatcher` (waitid WNOWAIT
  thread → call_soon_threadsafe, never reaps), pipe protocols (`connect_read/write_pipe`, own the fds), `notifier`
  (broadcast future), `AsyncioProcess` (per-handle lock over the signal/reap critical section, state machine, poison
  flag), `AsyncioProcessManager` (SIGCHLD guard + self-test, ordered event drain, registry, spill dir).
- **`inject.py`** — `bind_process_manager()` via `inj.make_async_managed_provider` (started on provision, aclosed on
  injector teardown; no globals).
- **Tests**: `test_spool` (7), `test_asyncio` (16), `test_inject` (1). Demo `tests/demos/basic.py`.

## What I wanted vs what happened (notable)

- **Popen-as-spawner is a live footgun.** Confirmed against 3.14 source (via the red-team pass): `Popen.__del__`
  reaps a held zombie, `subprocess._active`/`_cleanup` reaps parked ones on the next `Popen()`, `send_signal` polls
  first. Neutralized with the `_SpawnerPopen` subclass; we set `returncode` after our own reap. This is THE
  correctness lynchpin — do not "simplify" it away.
- **setsid can't go in the shim** (EPERM for a group leader). Session/group is chosen at Popen level
  (`start_new_session=True` default). The group therefore exists before `Popen()` returns → `killpg` is race-free.
- **read(wait=) semantics bit the tests.** `read(wait=t)` collects for the whole window unless output ends or
  max_bytes hits. When a child holds a pipe open (e.g. `... & sleep 100`), output never ends, so the read blocks the
  full window. Tests that needed "first line, now" must poll `read_available` instead (see `_read_first_line`).
- **mypy narrows property calls across awaits.** `assert p.state is ProcessState.X` twice → the second looks
  always-false → "unreachable". Worked around in tests by asserting on `.state.name` (a str). Worth remembering:
  don't assert the same bool/enum property twice around awaits.
- **`@om-lite` doesn't work for a module under `omllm.core`.** The lite precheck does `import <dotted.module>` under
  py3.8, which runs the non-lite `omllm/core/__init__.py` (imports omcore → 3.8 `list[]` subscript failure). So the
  shim is NOT marked `@om-lite`; it keeps 3.8-compatible source + `# type:` comments + a `UP*` noqa and a docstring
  note. It's shipped as *text* and exec'd standalone, so it never imports as a package module anyway. Verified it
  loads under `.venvs/8` with the precheck's own standalone loader.

## Verified invariants (tests)

- Exit observed without reaping: process is a `Z` zombie, `_reaped()` false, still signalable; reap only at aclose.
- Escalation TERM→grace→KILL kills the whole group incl. grandchildren; a `setsid`'d grandchild is NOT signaled.
- Stuck process (kill_s=0) → abandon+event (default) or StuckProcessError (on_stuck='raise'); lingering watcher
  reaps it once it finally dies.
- Reparent survives a child scope closing (backgrounding).
- Big output spills to file; cursor reads with max_bytes walk the whole stream; no-spill mode reports dropped_before.
- wait() cancellation doesn't leak; 20 concurrent runs; spawn failure leaves an empty registry; manager
  re-instantiable after aclose; SIGCHLD-ignored refused at start.
- After manager close: `waitpid(-1)` → ECHILD (no children remain).

## Next (phase 2)

- `omllm/agent/exec/ops.py`: reimplement `ExecOps` over a `ProcessScope` (spawn+wait+render → text + framing:
  rc, truncation, spill path). Put the tool-call scope on `ToolContext`. `bash`/`ripgrep` honor `timeout_s`, include
  stderr/rc. Wire the manager into `ui/bare` (managed injector). Publish process events on the agent bus. `/ps`.
- Watch out: `ExecOps.exec` currently returns `ExecResult(rc, stdout, stderr)` and is used by bash/ripgrep — keep a
  compatible convenience path (run + collect) while exposing spawn/read for the future background tools (phase 3).

## Test layout convention (2026-08-18)

Tests live in a `tests/` subpackage *inside the most specific package they exercise*, not lumped under
`procs/tests/`:
- `asyncio/tests/test_asyncio.py` — the AsyncioProcessManager/handle/reaper tests.
- `spool/tests/test_spool.py` — frames/storage/spool/renderers.
- `procs/tests/test_inject.py` — stays here because `inject.py` lives directly in `procs/`.
- `procs/tests/demos/basic.py` — a package-level demo of the whole public API, stays at the package root.

A "general" test module for a package may share the package's name (`test_asyncio.py` under `asyncio/`). Mind the
relative-import depth when adding tests: from `asyncio/tests/`, asyncio-internal imports are `..`, procs-level are
`...`; from `spool/tests/`, the sibling asyncio notifier is `...asyncio.notifier`.

## macOS/BSD: EPERM when signaling a zombie (2026-08-18)

Reported failing on darwin: the group-sweep `killpg` in `aclose` raised `PermissionError: [Errno 1] Operation not
permitted`. Cause: **macOS/BSD return EPERM (not Linux's ESRCH/success) when signaling a zombie process, or a
process group whose only remaining members are zombies.** Our teardown signals the leader *after* it has exited (we
hold it as a zombie), so on darwin nearly every close of an exited process EPERM'd — and `run()` (spawn→wait→close)
hits it every time, so "all tests failed."

Fix (`asyncio/process.py::_signal_locked`): on `PermissionError`, probe liveness non-reapingly with
`_is_exited_nowait` (`waitid(P_PID, pid, WEXITED|WNOHANG|WNOWAIT)`); swallow the EPERM iff the target is confirmed
dead (the benign zombie quirk), re-raise iff it is genuinely still alive. This is sound because the "never signal an
unowned pid" guarantee comes from the *state check* (never signal REAPED/POISONED) plus the held zombie — not from
the signal succeeding. ESRCH is still swallowed unconditionally.

Regression tests (`test_zombie_signal_eperm_tolerated`, `test_is_exited_nowait`) inject EPERM via `monkeypatch` on
`os.killpg`/`os.kill` (the codestyle's sanctioned external-dep fault-injection exception) so the darwin path is
exercised on Linux too: swallowed for a real held zombie, surfaced for a live process.

Watch for other latent darwin differences as they surface (waitid/pidfd/kqueue paths, pipe transports); this was the
first, and the only one reported so far.
