# Research notes (verified on CPython 3.14.7, Linux; macOS from docs)

## Prior art in-repo (read, not imported)

- `omcore/subprocesses/*` + `omcore/asyncs/asyncio/subprocesses.py`: lite run-and-done wrappers. Reused: only
  `omcore.subprocesses.wrap.subprocess_maybe_shell_wrap_exec` (as a `SpecTransform`). Checklist items: channel
  option normalization, `extra_env`, timeout coercion, `VerboseCalledProcessError`.
- `omcore/daemons`: `children/supervisors.py` escalation (TERM → grace → KILL → kill_timeout → error) and
  `stopping.py` pin → re-verify → `pidfd_send_signal` discipline; `startup.py::_PipeLaunchMonitor` (one JSON line
  over a dedicated pipe) is the same shape as our shim status handshake.
- `omcore/resources`: `AsyncKeyedExitStack` (keyed unlink), `AsyncResourceManager`. Not used in v1 scopes (we need
  concurrent process teardown, LIFO only over child scopes) — may be used later.
- `omcore/inject`: `make_async_managed_provider` for the manager singleton; `DelimitedScope` +
  `ContextVarScopeContext` exist for future turn/tool scopes.
- `omcore/typedvalues`: `TypedValue`/`UniqueTypedValue`/`TypedValues.update(mode='override')` for option layering
  (`omcore/marshal/api/options.py` is the reference user).
- `omdev/dockerdev`: docker CLI via stdlib subprocess, no exec/stop, label-only identity, image CMD is
  `dumb-init -- sleep infinity` (ready for `docker exec`). `omcore/docker/cli.py::cli_ps` for discovery.
- `omcore/diag/procfs.py`: `PGRP`, `STARTTIME`, `get_process_start_time()` — Linux process-tree walking later.
- `omcore/os/deathsig.py` (`prctl(PR_SET_PDEATHSIG)` via ctypes), `omcore/term/vt100` (future PTY consumer).

## Stdlib facts the design depends on

(Items 1, 2 and parts of 6 describe `Popen`, which the manager no longer uses at all - see `dev_10`. They are kept as
the record of *why*: they are the behaviors we had to neutralize, and the reason there is no Popen object anywhere now.)

1. `Popen.__del__` with `returncode is None` calls `waitpid(pid, WNOHANG)` — it would reap a zombie we hold; else it
   appends the object to `subprocess._active`, which every later `Popen()` reaps via `_cleanup()`. `send_signal()`
   calls `poll()` first (reaps), and documents a residual pid-reuse race anyway. `__exit__` waits. => We use a
   private Popen subclass with a no-op `__del__` and raising wait/signal methods, hold a strong ref for the handle
   lifetime, and set `returncode` after our own reap.
2. `Popen(..., pass_fds=...)` never uses `posix_spawn`, never closes user-supplied fds (we close child ends), and
   with `start_new_session=True` / `process_group=0` the group exists before `Popen()` returns.
3. `os.waitid(P_PID, pid, WEXITED | WNOWAIT)` returns exit info without reaping (repeatable, `|WNOHANG` ok); the
   leader stays a zombie; `os.killpg(pid, 0)` still succeeds; `os.waitpid(pid, 0)` then reaps; afterwards `killpg` →
   ESRCH. 3.14's own `asyncio._ThreadedChildWatcher._do_waitpid` uses exactly this (works on macOS).
4. While a group leader is unreaped, no unrelated process can obtain its pid (zombie owns it) nor create a group with
   that pgid (`setpgid`/`setsid` only create groups with pgid == caller pid). So `killpg(leader)` while unreaped only
   reaches our descendants (minus ones that `setsid()`'d out — not ours, never signaled).
5. `SIGCHLD = SIG_IGN` (or `SA_NOCLDWAIT`) makes children auto-reap; `waitid`/`waitpid` then raise `ChildProcessError`
   → pid immediately recyclable. Guard at manager start + poison handles on runtime ECHILD.
6. Shim: `python -I -S -c pass` ≈ 9 ms; `+os,sys,json` ≈ 20 ms; `marshal`/`_signal`/`resource`/`pwd`/`grp` ≈ 0 ms;
   `ctypes` +8 ms. => marshal payload, `_signal`, ctypes only for deathsig. `os.setsid()` in the shim fails (EPERM)
   after `process_group=0`/`start_new_session=True` — group creation happens at Popen level. When `posix_spawn` lacks
   setsid support, spawning without group changes lets the shim create the session itself. `pass_fds` clears FD_CLOEXEC
   in the child → shim must re-set non-inheritable on the status fd and close the payload fd. Python ignores
   `SIGPIPE`/`SIGXFSZ` at startup and exec preserves the blocked mask → shim resets to `SIG_DFL` and clears the mask.
   `PR_SET_PDEATHSIG` binds to the forking *thread* (spawn from the loop thread) and is cleared by uid/gid changes (set
   it after). `os.execvpe` resolves `argv[0]` against the *passed* env's PATH.
7. `loop.connect_read_pipe(proto, open(fd, 'rb', buffering=0))` accepts FIFO/socket/char device (pty master ok), sets
   non-blocking, and closes the file object itself on EOF/close. `connect_write_pipe`: `close()` flushes then EOF;
   writes after peer exit → `BrokenPipeError` → `connection_lost(exc)`.
8. `os.pidfd_open` + `loop.add_reader` + `waitid(P_PIDFD, ..., WNOWAIT)` is a drop-in thread-free path on Linux
   (future). macOS: `select.kqueue` `EVFILT_PROC/NOTE_EXIT` (future).

## External prior art (from memory)

- Claude Code: foreground bash w/ timeout, `run_in_background` + polling tool + kill tool, ~30k char truncation w/
  full output persisted, process-group kill on abort.
- Codex: unified exec sessions (PTY, `write_stdin`, `yield_time_ms` = the batching model), sandbox wrapping at spawn.
- pi-mono: bash tool with `onUpdate` streaming to UI, abort signal, tail truncation.
