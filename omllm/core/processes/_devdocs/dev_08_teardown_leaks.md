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

## Also found, not yet fixed (see the review notes for details)

- Spools (memory suffix + spill fd/file) are retained in `manager._spools` for the manager's lifetime - a per-command
  leak in a long session; needs a retention policy.
- `bwrap` on merged-usr distros: `/lib64` etc. are realpath'd to `/usr/...` and never recreated in the sandbox, so no
  dynamically linked binary can exec; `--tmpfs /tmp` is emitted after the binds (shadows roots under `/tmp`);
  `--new-session` means only bwrap itself sees our TERM.
- `read_available(max_bytes=…)` overshoots by a record per 64 KiB chunk; `_wait_exited` timeout/exit race; Targets treat
  `env={}` as inherit; poisoned handles leave their stdin transport open (abandoned ones now abort it).
