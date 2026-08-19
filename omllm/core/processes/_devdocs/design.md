# Design

## Big picture

- One `ProcessManager` (impl: `AsyncioProcessManager`) per python process, injector-managed, no global state.
- It owns a **tree of `ProcessScope`s** rooted at `manager.root`. Every spawned `Process` handle lives in exactly one
  scope until it is reaped or abandoned. Backgrounding == `scope.adopt(process)` on an ancestor (reparent).
- Every local spawn: `ShimLauncher` builds `python -I -S -c <bootstrap> <payload_fd>`; the shim (pure stdlib,
  `_spawn/shim.py`) applies `Credentials`/`Umask`/`Rlimit`/`Deathsig`, `chdir`, env, resets signal dispositions,
  reports pre-exec failures over a status fd, then `os.execvpe`. Session/group creation happens at spawn level
  (`os.posix_spawn` `setsid` / `setpgroup`).
- Output: one **spool** per process — an append-only *framed* byte stream (fd, flags, len, t_mono_ns, t_wall_ns,
  seq + payload). Memory holds the suffix (byte cap, `None`-able), a spill file holds the prefix. Cursor == byte offset
  into the framed stream. Renderers are stateful views (raw / arrival-merged / tagged lines).
- Exit observation via `waitid(WNOWAIT)` in a per-process daemon thread; reap is a deliberate step at handle close,
  after group teardown, under the handle lock. Signals only while unreaped and not poisoned.

## Types (`types/`)

- `ProcessSpec(argv, *, cwd, env, stdio, name)`; `ProcessStdio(stdin, stdout, stderr)` with literal modes
  `'pipe' | 'devnull' | 'inherit'` (+ `'stdout'` for stderr merge) or an int fd. `env=None` means inherit
  `os.environ` at spawn time; `{}` means clean.
- `ProcOption(tv.TypedValue)` families (`ProcOptions = tv.TypedValues[ProcOption]`): `TerminationPolicy`
  (signal, grace_s, kill_s, close_stdin, process_group, drain_s, on_stuck), `SpoolPolicy` (memory_cap, spill,
  keep_spill), `SessionMode` ('session' | 'group'), `Credentials` (user, group, extra_groups), `Umask`, `Rlimit`
  (non-unique), `Deathsig`, `RunTimeout`, `Tag` (non-unique), `PassFd` (non-unique). Layering:
  `layer_options(base, *overrides)` = `TypedValues.update(mode='override')`.
- `ProcessState`: SPAWNING → RUNNING → EXITED → REAPED; side states ABANDONED, POISONED.
- Events (`ProcessEvent`): `ProcessSpawnedEvent`, `ProcessExitedEvent`, `ProcessReapedEvent`,
  `ProcessAbandonedEvent`, `ProcessPoisonedEvent`, `ProcessReparentedEvent`, `ScopeOpenedEvent`, `ScopeClosedEvent`.
- Errors: `SpawnError(stage, errno, message)`, `ProcessTimeoutError`, `ScopeClosedError`, `ProcessPoisonedError`,
  `StuckProcessError`, `ManagerClosedError`.

## Spool (`spool/`)

- `frames.py`: `FRAME_HEADER = struct.Struct('<BBHIqqQ')` (32 B). `SpoolRecord(fd, data, t_mono_ns, t_wall_ns, seq,
  offset)`; `encode_frame`, `iter_frames(buf, base_offset)`.
- `storage.py`: `SpoolStorage(memory_cap, spill_dir)`: `append(frame)`, `read(start, end) -> bytes`,
  properties `total`, `available_start` (bytes before it are gone: dropped only when spill is disabled or a spill
  write fails), `spilled_end`, `spill_path`.
- Lifetime: a spool outlives its process (so output can be read after `aclose()`); it is released by `close()` -
  `ProcessScope.run` and the exec/tool paths do that once they have the output - or, failing that, when its handle is
  dropped (weakref finalizer) or the manager closes. `SpoolPolicy.keep_spill` exempts the spill file.
- `spool.py`: `OutputSpool(storage, notifier)`: `append(fd, data) -> SpoolRecord`, `mark_ended()`,
  `read(cursor=None, *, wait=None, max_bytes=None) -> SpoolRead`, `subscribe(from_cursor=None) -> async iterator of
  SpoolRead`, `head(n)`/`tail(n)` helpers. `Notifier` is a tiny abstract (`notify()`, `async wait(timeout) -> bool`)
  so the spool is loop-agnostic; `asyncio/notifier.py` implements it.
- `SpoolRead(records, start, end, total, dropped_before, ended, more)` — the out-of-band framing tools use.
- `render.py`: `Renderer.render(read) -> str` stateful views: `RawRenderer(fds)`, `ArrivalMergedRenderer`,
  `TaggedLinesRenderer(ts=True, fd=True, resume_gap_s=None, ts_format=...)`.

## Scopes / handles / manager

- `ProcessScope(name, parent, ops)`: `spawn(spec, *options)`, `run(spec, *options, timeout=None) -> ProcessRun`
  (spawn + wait + drain + close), `child(name)`, `adopt(process)`, `processes`, `children`, `aclose()`,
  `async with`. `ScopeManager` (impl hook): `spawn(scope, spec, options)`, `close_processes(procs, policy)`.
- Handles (`handles.py`): `ProcessInfo` (id, pid, spec, options, state, returncode, scope, name), `ProcessControl`
  (`signal`, `terminate`, `kill`, `aclose(policy=None)`), `ProcessStdin` (`write`, `write_eof`, `stdin_closed`),
  `ProcessOutput` (`spool`, `output_ended`), `ProcessWaiter` (`wait(timeout=None)`, `done`, `exited`), `Process`
  composes them.
- `ProcessManager` (abstract): `root`, `processes` (registry view), `subscribe(...)` (events, via
  `omllm.core.eventbus.EventPublisher`), `aclose()`, `async with`. `ManagerConfig(shim_python, spill_dir,
  default_options, close_policy)`.

## Launch (`launch/`)

- `SpecTransform.transform(spec) -> spec` chain (day 1: `ShellWrapTransform` — debugger-friendly `sh -c` wrap via
  `omcore.subprocesses.wrap`; `EnvScrubTransform`).
- `ShimLauncher.plan(spec, options) -> LaunchPlan(argv, env, pass_fds, owned_fds)`: bootstrap `-c` code + one text
  file on the payload fd - a first line of json (`ShimPayload`, a plain dataclass in `spawn/shim.py` that the rest of
  the package imports and builds directly; every field round-trips json as is, OS strings as surrogate-escaped str)
  followed by the shim source. The bootstrap execs the source as module `__procs_shim__` and calls
  `main(ShimPayload(**payload))`. Unlinked temp file, any size, no pipe stalls. Shim source loaded once via
  `lang.get_relative_resources('..spawn', globals=globals())['shim.py']` (never `__file__`).
- Status protocol: parent reads the status pipe until EOF. EOF with no data == exec happened. Any data == a json
  `[stage, errno, message]` error record from the shim → `SpawnError`; the shim then `os._exit(127)`.
- Division of labor: `spawn_child` (`os.posix_spawn`) does only what must happen between fork and exec - dup2 of 0/1/2,
  setsid / setpgroup, default signal dispositions; the shim (a full python of ours) does everything else, including
  closing every fd >= 3 except `status_fd` + `keep_fds` (so a stray inheritable fd can reach the shim, never the
  target). `pass_fds` are made inheritable in the parent for the duration of the spawn and restored.

## Managers (`managers/`) and the asyncio impl (`asyncio/`)

- `BaseProcessManager(config, *, asynclite)` (runtime-agnostic): `start()` (SIGCHLD guard + self-test spawn, mkdtemp,
  validate shim python), `spawn` (`setup_stdio` fd plumbing, launcher plan, `spawn_child`, handle + watcher, pipe
  connects, status handshake, registry, events), the ordered event drain, scope hooks, `close_processes` backstop,
  `aclose()`. Its runtime hooks - all an implementation provides - are `_start_runtime`, `_spawn_task` / `_join_tasks`,
  `_run_all_bounded`, `_new_spool_notifier`, `_new_process`, `_connect_stdin` / `_connect_output` /
  `_read_exec_status`.
- `BaseProcess` (runtime-agnostic): per-handle `threading.Lock` for the signal/reap syscall critical section, asynclite
  events for exited / output-ended / reaped and an asynclite lock for close, state machine, poison flag, the whole
  teardown algorithm; one hook, `_post_threadsafe` (exit-watcher thread -> owner thread).
- `managers/spawn.py::spawn_child`: our own spawner over `os.posix_spawn` returning a bare pid - there is no `Popen`
  object (nor any `_posixsubprocess` use) anywhere.
- `AsyncioProcessManager` / `AsyncioProcess`: the hooks above with asyncio tasks, `connect_read_pipe` /
  `connect_write_pipe` transports (`asyncio/pipes.py`), `AsyncioSpoolNotifier`, `call_soon_threadsafe`.
- Teardown of one handle (`aclose`): close stdin → (if alive) TERM → wait grace → KILL → wait kill_s → stuck →
  abandon/raise; (exited) sweep group: `killpg(TERM)` then wait output EOF up to `drain_s`, `killpg(KILL)`, force
  close read transports; reap; unregister; events.
- Scope close: children reverse-order sequential, then all processes concurrently under `asyncio.timeout(overall)`,
  exceptions gathered into an `ExceptionGroup`.
- Manager close: root scope close, await pending event tasks, remove spill dir (unless kept), mark closed.

## Invariants (repeat in code comments)

1. There is no `Popen`: `spawn_child` returns a pid and nothing but the handle's deliberate `_reap` ever waits on it.
2. Signal only under the handle lock, only while `not reaped and not poisoned`; `killpg` only our own leader pids.
3. Readers always drain into the spool regardless of subscribers.
4. Every handle is in exactly one scope until reaped/abandoned; the registry mirrors scopes.
5. No module-level state; everything hangs off a manager instance.

## Phases

1. types + spool + shim/launch + scopes/handles/manager + asyncio impl + tests + injector binding (this).
2. Agent integration: `ExecOps` over scopes, `ToolContext.processes`, bash/ripgrep, ui/bare wiring, events, `/ps`.
3. Background + `process_*` tools. 4. Sandbox/ulimit transforms, multiprocessing demo. 5. PTY. 6. Docker/ssh targets.
