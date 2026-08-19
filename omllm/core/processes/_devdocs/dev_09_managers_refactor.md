# dev 09 — managers/ refactor: a real base manager, no Popen (2026-08-19)

The manager logic used to live entirely on `AsyncioProcessManager` / `AsyncioProcess`; `asyncio/` owned everything and
the abstract `ProcessManager` was the only layer above it. Now the runtime-agnostic bulk lives in a new `managers/`
package and the asyncio package is just the asyncio bits.

## Layout

- `managers/types.py` <- `manager.py` (`ProcessManager`, `ManagerConfig`; git-moved, refs updated).
- `managers/base.py`: `BaseProcessManager(ProcessManager, ScopeManager, lang.Abstract)` - lifecycle, registry, root
  scope, `spawn` (transforms, stdio, launcher plan, `fork_exec`, handle + watcher, connects, handshake, registration,
  cancellation-safe teardown), the ordered event drain, scope hooks, `close_processes` backstop, `aclose`, spill dir.
- `managers/process.py`: `BaseProcess(Process, lang.Abstract)` - the entire handle (state machine, `threading.Lock`
  signal/reap discipline, `_abandon` / `_poison`, output-ended bookkeeping, `aclose` teardown), plus the
  `ProcessStdinWriter` interface an implementation's stdin channel implements.
- `managers/spawn.py`: `fork_exec(argv, *, env, cwd, stdin_fd, stdout_fd, stderr_fd, pass_fds, session_mode)` over
  `_posixsubprocess.fork_exec` -> pid. **`_SpawnerPopen` is gone**: it subclassed `subprocess.Popen` only to neuter its
  lifecycle (`__del__`, `wait`, `send_signal`, ...) - Popen's actual work for us (arg marshalling, the exec-failure
  error pipe, `close_fds`/`pass_fds`, setsid/setpgid, `restore_signals`) is ~100 lines, reproduced here without the
  Windows / posix_spawn / lifecycle machinery. `check_child_signal_disposition` uses it too. Handles hold a pid, not a
  Popen.
- `managers/stdio.py`: `setup_stdio(stdio) -> StdioSetup` - pipes / pty / devnull / inherit / int-fd / stderr->stdout
  resolution into child 0/1/2 fds plus our ends, with a single-failure-closes-everything guarantee.
- `managers/pty.py` <- `asyncio/pty.py` (git-moved; it never imported asyncio).
- `managers/reaper.py` <- `asyncio/reaper.py`: `ExitWatcher(pid, *, post, on_exit, on_error)` - `post` is the
  thread-safe "run on the owner's thread" callable (asyncio: `call_soon_threadsafe`).
- `spool/spool.py` gained `ImmediateSpoolNotifier` / `NULL_SPOOL_NOTIFIER` (moved out of `asyncio/notifier.py`).
- `launch/shim.py` gained `decode_shim_status` (the status-record protocol belongs with the shim).

## The abstraction seam

Async primitives come from `omcore.asyncs.asynclite` (`Asynclite.make_event()` / `make_lock()`), handed to the base
by the implementation - exactly the "simple lower-level async ops" case asynclite exists for. What asynclite does not
model (tasks, structured concurrency, pipe transports) is a handful of abstract hooks on `BaseProcessManager`:

    _start_runtime()                       bind the loop / thread context
    _spawn_task(coro) / _join_tasks()      fire-and-forget background work + wait for all of it
    _run_all_bounded(coros, timeout)       concurrent run with an overall deadline (scope close)
    _new_spool_notifier()                  loop-aware wake-ups for spool readers
    _new_process(**kw)                     the BaseProcess subclass (asyncio: adds `_post_threadsafe`)
    _connect_stdin(fd) / _connect_output(proc, fd_num, fd) / _read_exec_status(fd, timeout)

`asyncio/manager.py` is now ~120 lines implementing those; `asyncio/process.py` ~20. Nothing asyncio-specific remains
outside `asyncio/`.

## Notes

- Event ordering / `_publish_now` re-entrancy no longer uses `asyncio.current_task()`: a `contextvars.ContextVar`
  (`_IN_DRAIN`) marks "inside the drain", and an asynclite idle event replaces awaiting the drain task.
- Found while wiring `_join_tasks`: 3.14's `asyncio.gather` completes *eagerly* when every future is already done, so
  a `while tasks: await gather(tasks)` never yields for the tasks' discard callbacks - a busy hang. The pre-refactor
  code had the same latent hazard; `_join_tasks` now yields (`sleep(0)`) after each gather.
- Fixed on the way (from the review's low list): `_wait_exited` / `wait` re-check the event after a timeout (the
  timeout-vs-exit race); poisoned handles abort their stdin channel.
- Suite: `pytest omllm/core/processes` 48 passed / 4 skipped; downstream exec/harness/agent suites green; `make fix gen
  check` clean.
