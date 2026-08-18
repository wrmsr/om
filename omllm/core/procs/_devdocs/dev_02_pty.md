# dev 02 — PTY support (2026-08-18)

Phase 5. Processes can now run under a real pseudo-terminal: the child gets a controlling tty, the handle exposes the
merged master as output + a writable stdin, and `resize()` delivers SIGWINCH. `make fix gen check` clean;
`pytest omllm/core/procs` 30 passed / 1 skipped (the 4 new pty tests + everything prior).

## Heads-up for the next worker: the package was renamed out from under us

An external snapshot/apply committed phase 1 and then, in commit `1015fbdbd` ("Rename internal spawn module and update
resource paths"), renamed `omllm/core/procs/_spawn/` -> `omllm/core/procs/spawn/` and updated
`launch/shim.py`'s `get_relative_resources('..spawn', ...)`. The shim module is `spawn/shim.py` now (no underscore). A
stale empty `_spawn/` dir was left behind (removed). If you're diffing against my earlier journal entries, that's why
the path differs.

## What landed

- `types/specs.py`: `PtyStdio(rows, cols, term)` + a `Stdio = ProcessStdio | PtyStdio` union on `ProcessSpec.stdio`.
  Pty output is a single interleaved stream (a tty has no separate stderr) presented in the spool under fd 1
  (`asyncio/pty.PTY_OUTPUT_FD`).
- `spawn/shim.py`: a `set_ctty` stage - `ioctl(0, TIOCSCTTY, 0)` after chdir, before fd scrub. Gated on a payload
  flag. fd 0 is the slave (Popen dup2'd it) and the child is a session leader (start_new_session), so this acquires
  the slave as the controlling terminal.
- `launch/shim.py`: derives `set_ctty` from `isinstance(spec.stdio, PtyStdio)` and threads it into the payload.
- `asyncio/pty.py`: `open_pty()` (master non-inheritable, slave inheritable), `set_winsize`/`get_winsize` (TIOCSWINSZ
  / TIOCGWINSZ), `Winsize`, `PTY_OUTPUT_FD`.
- `asyncio/manager.py::spawn`: a pty branch - openpty, winsize on the slave, TERM injected into the child env (unless
  the spec sets it), session mode forced to 'session', slave -> child 0/1/2. The master is duped twice: one dup feeds
  a read transport (spool fd 1), one feeds the stdin write transport; the original master is the handle's control fd
  for resize. All three are `parent_fds` (closed on spawn error) and adopted on success.
- `handles.py`: `ProcessPty` role (`has_pty`, `resize`, `get_winsize`) mixed into `Process`.
  `asyncio/process.py`: `has_pty` is a stable "launched under a pty" fact; `resize` raises `NotAPtyError` for
  non-pty procs and `ProcessNotAliveError` once the master fd is torn down; the master control fd is closed in
  `_force_close_output`.
- Tests: `asyncio/tests/test_pty.py` (4). Demo: `tests/demos/pty.py`.

## Verified mechanics (this box, Linux)

- Without `TIOCSCTTY` the slave is the child's stdio but `ps -o tty=` shows `?` (no ctty). With it: `pts/N`. Winsize
  and TERM propagate. Cooked-mode echo returns CRLF (`b'one\r\n...'`) - proof it's a real tty, not a pipe.
- asyncio's `_UnixReadPipeTransport` accepts char devices (S_ISCHR) and special-cases pty `EIO` on child exit in
  `_fatal_error` (no exception-handler call) -> our read protocol's `connection_lost` resolves it as a clean
  output-end. The write transport also accepts char devices and does NOT run the reader-close trick for them.
- `resize()` -> `get_winsize()` reflects the change; the kernel SIGWINCHes the foreground group.

## Notes / possible follow-ups

- `SessionMode('group')` + pty is contradictory (a ctty needs a session leader); the manager silently forces
  'session'. Could make that an explicit error instead.
- Output-only pty (like `docker run -t` without `-i`) isn't a distinct mode yet - PtyStdio always wires stdin too.
- The vt100 tmux-style future (raw master bytes -> `omcore.term.vt100` emulator -> screenshot tool) sits directly on
  top of this: the spool records are raw bytes, so an emulator can replay them. Nothing here blocks it.
- Not exercised on macOS yet; watch for TIOCSCTTY/openpty differences (BSD ptys behave a little differently, and the
  master EIO-vs-EOF behavior on child exit may differ). The zombie-EPERM fix from dev_01 already applies.
