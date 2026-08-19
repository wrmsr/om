# dev 08 — teardown leak fixes (2026-08-19)

A bug-hunt pass over the whole package turned up four ways a child could escape management (a zombie held forever, or
a live process nobody would ever signal) - all in the "zero tolerance for leaks / zombies" bucket. Each was reproduced
with a probe first, then fixed with a regression test in `asyncio/tests/test_asyncio.py`.

## What was wrong / what changed

1. **Cancellation between `Popen()` and the handshake leaked the child** (`asyncio/manager.py::spawn`). The fork is
   sync, but the pipe connects (`loop.connect_*_pipe`) that followed it were awaited *before* the handle was created /
   registered / watched and before the `try` that handles `CancelledError`. A cancel requested while Popen ran (an
   `asyncio.timeout` around the spawn expiring, say) landed at the first connect - child forked, never registered,
   never signaled, never reaped, fds leaked. Now the `AsyncioProcess` + exit watcher are set up synchronously right
   after Popen and *every* suspension point (connects, handshake, spawned event) sits inside the one try whose handlers
   `aclose()` the handle (in the background when cancelled). Raw parent fds not yet handed to a transport are tracked
   (`pending_fds`) and closed by hand on bail-out; `_set_stdin` / `_add_read_transport` refuse (and close) a transport
   that arrives after the handle was already torn down.
   - Test: `test_spawn_cancelled_during_setup_is_torn_down` (`loop.call_soon(task.cancel)` lands the cancel exactly at
     the first connect; asserts a `ProcessReapedEvent` per attempt, pipes and pty variants).

2. **A spawn racing its scope's close registered into a closed scope** (`scopes/scope.py::spawn` checked `_check_open`
   once, then awaited). The scope's close snapshotted its processes before the spawn registered, so the handle ended up
   in `manager._processes` but in a scope nothing would ever close - it survived manager close. `spawn` now re-checks
   `scope.closing` right before registration (and again after the handshake), raising `ScopeClosedError` after
   closing the handle.
   - Test: `test_spawn_racing_scope_close`.

3. **The scope-close backstop could abandon an already-`EXITED` handle** (`close_processes` timeout →
   `_abandon()`), whose exit watcher had already fired - so nothing ever reaped it (held zombie forever) and its group
   never got the KILL sweep. `_abandon` now finishes (sweeps + reaps) an `EXITED` handle instead of abandoning it,
   aborts stdin, and the backstop passes `kill=True` so live leftovers are SIGKILLed before being abandoned to their
   lingering watchers (they used to be left running).
   - Tests: `test_scope_close_backstop_reaps_already_exited`; `test_scope_close_policy_backstop` no longer needs to
     kill by hand.

4. **A cancelled `ProcessScope.aclose()` bricked the scope**: `_closing` was set up front and any later `aclose()`
   returned immediately - including the manager's own root close - leaving live processes behind. `aclose` no longer
   early-returns on `_closing`: a concurrent or retried close runs the (idempotent, concurrency-safe) steps to
   completion; only the first completer publishes `ScopeClosedEvent`. Same for `AsyncioProcessManager.aclose`
   ('closing' no longer short-circuits; the sync tail is guarded so it runs once).
   - Test: `test_scope_close_retry_after_cancel_and_concurrent_close`.

## Second pass: retention, caps, bwrap

5. **Spools were retained for the manager's lifetime** (`manager._spools` was a strong list, closed only at manager
   close): every command that produced output pinned its memory suffix, spill fd and spill file until the session
   ended. Spools are now owned by their handles: `ProcessScope.run` (and `ProcessesExecOps.exec`, `process_kill`)
   `spool.close()` once they have collected the output; the manager tracks spools in a `WeakSet` (for the close-time
   sweep) with a `weakref.finalize` backstop that releases a spool nobody closed when its handle is dropped.
   `SpoolStorage.close()` now also drops the memory suffix, and reads on a closed storage fail with a clear
   `check.state` rather than tripping on the missing spill fd. `keep_spill` still survives all of that (and the manager
   won't remove its spill dir if anything was kept).
   - Test: `test_spools_released`.

6. **`max_bytes` was a floor, not a cap**: `read_available` took at least one record *per 64 KiB chunk*, so it returned
   the smallest whole-record prefix reaching `max_bytes` (60_000 over 50_000-byte records -> 100_000). The spool tests
   actually asserted that, but both docstrings and the `process_read` tool ("Maximum number of output bytes") promised a
   cap. It is a cap now: records are taken while they fit, the first always is (`decode_frames(at_least_one=)`), a
   capped read reports `more`, and `read(wait=)` returns as soon as a read is capped.
   - Tests: `test_spool_max_bytes_across_chunks`, updated `test_spool_basic_reads` / `test_spool_wait_and_subscribe`.

7. **bwrap on merged-/usr hosts**: roots were bound at their `realpath` only, so `/lib64` (-> `usr/lib64`), `/bin`,
   ... never existed inside the sandbox and no dynamically linked binary could exec (`/lib64/ld-linux-*.so` is the ELF
   interpreter of everything). `build_bwrap_argv` now recreates every symlink on the way to a root with `--symlink`
   (`iter_symlink_prefixes`), binds the real path, and keeps `--chdir` at the given (symlinked) name.
   - Test: `test_bwrap_recreates_symlink_prefixes`. **Still not live-tested** (no userns here); the live test's
     usability probe now uses our own rendering, so it no longer self-skips on merged-/usr hosts once userns works.

8. **`--tmpfs /tmp` (and `--dev`/`--proc`) came after the binds**, shadowing any root under `/tmp` - including every
   pytest `tmp_path`. Fresh mounts now go first so binds land inside them.
   - Test: `test_bwrap_mounts_before_binds`.

9. **`--new-session` is now opt-in** (`BwrapSandbox.new_session`, default off): the setsid detached a `PtyStdio` from
   its controlling tty (no job control, `tty` fails) and diverted our TERM to the outer bwrap only. It was there for
   TIOCSTI hardening, but the manager already makes every child a session leader without a controlling terminal (or
   with our own pty), so there is no user terminal to inject into. Documented in the module: bwrap does not forward
   signals, and `--die-with-parent` (kept - it also binds the sandbox to *our* lifetime) SIGKILLs the sandbox when the
   outer bwrap dies of our TERM, so a sandboxed command effectively gets no grace period. A graceful remote stop needs
   the in-sandbox pid - the same open item as the docker/ssh targets.

## Still open (low)

- `_wait_exited` timeout/exit race (a `wait_for` timing out just as the exit lands); Targets treat `env={}` as inherit
  and the pty `TERM` injection lands on the local docker/ssh client; poisoned handles leave their stdin transport open
  (abandoned ones now abort it); `TaggedLinesRenderer.flush()` returns an unprefixed tail.
