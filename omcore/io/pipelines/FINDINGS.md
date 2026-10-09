# io.pipelines review findings

Working notes from an adversarial review of the half-close + multiplex work (commits `719299245`..`a450aa24d`),
covering `omcore.io.pipelines` (core, drivers, multiplex, TLS, sched) and the touched `omcore.http.pipelines` parts.
Kept up to date as the review proceeds. Nothing here is committed.

Status legend:

- `FIXED` - an inline fix is in the working tree, with a passing regression test.
- `OPEN` - reproduced and enshrined in a test which fails on purpose until the finding is resolved.
- `NOTE` - an observation worth knowing, not a defect (or not clearly one).

Test modules added by the review:

| Module | Contents |
| --- | --- |
| `tests/test_regressions.py` | passing regression tests for fixed core findings |
| `tests/test_findings.py` | failing demonstrations of open core findings |
| `drivers/tests/test_regressions.py` | passing regression tests for fixed driver findings |
| `drivers/tests/test_findings.py` | failing demonstrations of open driver findings |
| `multiplex/tests/test_regressions.py` | passing regression tests for fixed multiplex findings |
| `multiplex/tests/test_findings.py` | failing demonstrations of open multiplex findings |

Run everything but the deliberately failing demonstrations with:

```
./python -m pytest omcore/io/pipelines omcore/http/pipelines --deselect omcore/io/pipelines/tests/test_findings.py \
    --deselect omcore/io/pipelines/drivers/tests/test_findings.py \
    --deselect omcore/io/pipelines/multiplex/tests/test_findings.py
```

## Summary

| ID | Area | Severity | Status | One line |
| --- | --- | --- | --- | --- |
| F1 | core | medium | FIXED | a second `FinalOutput` crashed every driver instead of being rejected |
| F2 | drivers/sync | medium | FIXED | `FdSyncIoPipelineDriver` left a shared open file description nonblocking |
| F3 | multiplex | low | FIXED | destroying a child from its own `FinalOutput` completion reset the stream |
| F4 | multiplex | medium | FIXED | remote close behind a pending parent flush completed a later fence first |
| O1 | drivers/sync, asyncio | high | OPEN | both peers draining at once deadlock (pure/fdio discard input, these do not) |
| O2 | multiplex | medium | OPEN | manual-read child never sees typed messages queued after end-of-input |
| O3 | multiplex | medium | OPEN | adapter failures while encoding escape as unhandleable driver failures |
| O4 | multiplex | low-medium | OPEN | receive-credit accounting drifts from the wire after local finish |
| O5 | multiplex | low-medium | OPEN | a stream spec factory which raises fails the whole connection |
| O6 | core | low | OPEN | a message injected before `InitialInput` poisons the input lifetime |
| O7 | ssl | low-medium | OPEN | strict ragged-EOF detection is a no-op on Python 3.8 |
| O8 | drivers/asyncio | medium | OPEN | no timers run while the graceful writer close after `FinalOutput` is awaited |

## Baseline

- Before any change: `./python -m pytest omcore/io/pipelines omcore/http/pipelines` - 840 passed in ~12s.
- With the fixes below and the new regression tests: 846 passed (findings modules deselected).

## Fixed

### F1. A second `FinalOutput` reaching the terminal crashed every driver

- Where: `core.py` `IoPipeline._terminal_outbound`.
- What: the `FinalOutput` branch was checked before `_saw_final_output`, so a second `FinalOutput` was appended to the
  output queue instead of being rejected. Every reference driver then failed on it with a bare `check` error
  (`ValueError: Must be None`) and went `FAILED`; the asyncio driver silently "completed" it. DESIGN 4 says nothing may
  reach the terminal after `FinalOutput`.
- Fix: check `_saw_final_output` first; a second `FinalOutput` now fails with `SawFinalOutputIoPipelineError` and is
  reported as an inbound `Error`, like any other post-final output, and the driver closes gracefully.
- Test: `tests/test_regressions.py::TestSecondFinalOutput`.
- Pre-existing (not introduced by the reviewed commit).

### F2. `FdSyncIoPipelineDriver` left a shared open file description nonblocking

- Where: `drivers/sync.py` `FdSyncIoPipelineDriver._prepare_transport`.
- What: the original flags were read and changed one descriptor at a time. When the read and write descriptors are
  dups of one open file description (a process's stdin/stdout on one terminal, the case the commit message says it
  handles), the second descriptor's "original" flags were read after the first had already set `O_NONBLOCK`, and
  restoring them left the description nonblocking - i.e. the caller's terminal is nonblocking after the driver is done.
- Fix: record every original before changing any.
- Test: `drivers/tests/test_regressions.py::TestFdSyncSharedOpenFileDescription`.

### F3. Destroying a child pipeline from its own `FinalOutput` completion reset the stream

- Where: `multiplex/children.py` `MultiplexChild.finish`, `multiplex/handlers.py` `_on_parent_flush_done` and
  `_drain_remote_closed`.
- What: the child was marked finished only *after* its `FinalOutput` was completed, so an application listener on that
  completion which destroys the pipeline (a close hook) was taken for an abandonment: the stream was reset towards the
  peer (`LFinish` then `LReset` on the wire; `reset_local` counted instead of `closed`) even when the adapter had
  already closed it.
- Fix: `finish(final_output)` marks the child finished, then completes, then destroys.
- Test: `multiplex/tests/test_regressions.py::TestChildDestroyedFromItsOwnCompletion`.

### F4. A remote close before the parent flush completed an earlier fence made a later `FinalOutput` complete first

- Where: `multiplex/handlers.py` `_drain_remote_closed`.
- What: a child fence completes once a parent `FlushOutput` issued after its emission completes. When the peer's
  end and close arrived in one read while such a flush was still pending, the child saw `FinalInput`, closed, and its
  `FinalOutput` - discarded output on a remote-closed stream - was completed at once and the child destroyed, which
  failed the earlier, already emitted `ShutdownOutput` / `FlushOutput` with `AbortedIoPipelineError`. DESIGN 5: later
  fences cannot validly complete ahead of an earlier one. Found by the back-to-back SSH-like fuzzer (the peer's EOF and
  CLOSE in one read).
- Fix: the final fence of a remote-closed stream is completed - and the child finished - behind the pending parent
  flush, like a final reached normally.
- Test: `multiplex/tests/test_regressions.py::TestRemoteCloseBehindPendingParentFlush`.

## Open

### O1. Sync and asyncio drivers deadlock when both peers drain at once (high)

- Where: `drivers/sync.py` `_poll` (returns `'write'`/`'stop'` once a `FinalOutput` is held, never `'read'`);
  `drivers/asyncio.py` `_handle_output_final_output` (cancels the read task, then `wait_closed()`).
- What: DESIGN 6/8 require a draining driver to keep taking input off the transport so a peer blocked on output is not
  waited on forever. The commit did this for the pure and fdio drivers only (`test_driver_edges.py` covers those). Two
  sync-driven peers which each send more than the socket buffers hold and then `FinalOutput` wait on each other until
  `wait_timeout_s` fires - forever by default. Two asyncio peers do the same: the transport stops reading once the
  stream reader's buffer is full, and `writer.wait_closed()` then waits for a flush the peer cannot perform.
- Test: `drivers/tests/test_findings.py::TestDrainingDuplexDeadlock`, `TestDrainingDuplexDeadlockAsyncio`.
- Suggested fix: sync - while a `FinalOutput` is held, keep selecting for readability too and discard what arrives (as
  fdio's `_discard_input`). asyncio - keep the read task alive during the drain, discarding reads, until the writer is
  closed.

### O2. A manual-read child never sees typed messages queued after end-of-input (medium)

- Where: `multiplex/children.py` `MultiplexChild.deliver_input`.
- What: delivery stops at `MultiplexInputEnd`, feeds `FinalInput`, and consumes the read token. A typed message queued
  behind the end (an SSH `exit-status` request after EOF - the case DESIGN 13 and `tests/sshlike.py` are built around)
  then needs another `ReadyForInput`, which a child has no reason to send once it has seen `FinalInput`. The message
  sits in the stream queue forever (visible in `stats.queued_input`). The existing SSH-like test passes only because
  its children are auto-read.
- Test: `multiplex/tests/test_findings.py::TestManualReadMessageAfterEnd`.
- Suggested fix: typed messages behind end-of-input (which must be `AfterFinalInput` anyway) are not reads: deliver
  them without a token, both within the batch that carried the end and when they arrive later.

### O3. Adapter failures while encoding escape as unhandleable driver failures (medium)

- Where: `multiplex/handlers.py` - every `encode_*` call, `claim_output`/`message_cost`/`split_message`/
  `max_data_unit`/`data_unit_overhead`, and `on_stream_released` are unguarded; `inbound`, `open_local`,
  `on_shutdown`, `on_input_ended`, `on_stream_finished` are wrapped and route to `_fail`.
- What: an adapter raising in a guarded call fails the connection gracefully (connection error encoded for the peer,
  streams aborted, `FinalOutput`). The same adapter raising in `encode_data` propagates out of the handler's `inbound`
  as an `Error` which, with the multiplexer innermost, is `MessageReachedTerminalIoPipelineError` - unhandleable - and
  takes the driver down `FAILED` with no connection error on the wire. Raising in `on_stream_released` surfaces as a raw
  exception out of the driver's fence completion.
- Test: `multiplex/tests/test_findings.py::TestAdapterFailuresWhileEncoding`.

### O4. Receive credit accounting drifts from the wire once the local side finished (low-medium)

- Where: `multiplex/handlers.py` `_data` / `_message` (consume at once when `local_finished`) and `_queue_grants`
  (drops grants for `local_finished` streams, *after* the strategy has already advertised them).
- What: on a half-closed-local stream the peer's data is consumed immediately and the strategy re-advertises the credit
  internally (`recv_advertised`, `recv_outstanding` grow), but the grant is never encoded. The multiplexer then believes
  the peer has more credit than it was told: a conforming peer stalls on a window which is never replenished, and a
  misbehaving one can overrun the real window by the dropped amount before `FlowControlMultiplexError` triggers. With
  `on_finish='close'`/`'reset'` adapters (SSH CLOSE, h2 RST_STREAM) the window is short-lived; with `'wait'` it is not.
- Test: `multiplex/tests/test_findings.py::TestReceiveCreditAfterLocalFinish`.
- Suggested fix: either keep encoding grants on half-closed-local streams (the peer may legitimately keep sending), or
  skip the strategy's replenishment for them too, so `recv_advertised` always equals what went on the wire.

### O5. A stream spec factory which raises fails the whole connection (low-medium, design)

- Where: `multiplex/handlers.py` `_open_remote` (the factory is called inside the adapter's `inbound`, so the
  exception is caught as a connection failure).
- What: DESIGN 13 treats a child which cannot be built as a refusal of that stream. A factory which raises - an
  application error for one request - instead produces a connection error (GOAWAY-like) and aborts every other stream.
- Test: `multiplex/tests/test_findings.py::TestStreamSpecFactoryFailure`.

### O6. Injecting a message before `InitialInput` poisons the input lifetime (low)

- Where: `core.py` `IoPipeline._feed_in_to` sets `_saw_any_input` for every message, including ones injected at a
  handler's position with `feed_in_to`.
- What: `multiplex/README.md` documents `feed_in_to(mux_ref, OpenStream(...))` as the way to open a stream from
  outside the pipeline. Done after the driver has built the pipeline but before its first step (which feeds
  `InitialInput`), the open counts as input and the `InitialInput` is rejected with `SawInitialInputIoPipelineError`,
  failing the driver. Reachable through public API (`PureIoPipelineDriver.drain_output()` builds the pipeline without
  stepping), though it takes some effort.
- Tests: `tests/test_findings.py::TestInjectedInputBeforeInitialInput`,
  `multiplex/tests/test_findings.py::TestOpenBeforeInitialInput`.

### O7. Strict ragged-EOF detection does not work on Python 3.8 (low-medium, portability)

- Where: `ssl/handlers.py` `_read_engine` (`if not b: self._plaintext_eof = True`).
- What: with `Config(suppress_ragged_eofs=False)` a transport EOF without the peer's close_notify is meant to be
  reported as an error (truncation detection). Under the lite target, Python 3.8 (here 3.8.20 with the same OpenSSL
  3.0.13 as 3.14), `SSLObject.read()` returns `b''` for such an EOF rather than raising `SSLEOFError`, so the handler
  takes it for a clean EOF and strict mode is a no-op. Verified with a bare `MemoryBIO` probe on both interpreters.
- Test: the existing `ssl/tests/test_handlers.py::TestSslHandlers::test_ragged_eof_strict` fails under
  `.venvs/8` (`.venvs/8/bin/python -m unittest discover -s omcore/io/pipelines -t .`); everything else in the package
  passes there apart from this review's deliberate `test_findings` modules and N11.
- Pre-existing; relevant because the TLS half-close tests rely on strict EOFs to prove close_notify ordering.

### O8. The asyncio driver runs no timers while awaiting the graceful close after `FinalOutput` (medium)

- Where: `drivers/asyncio.py` `_handle_output_final_output` (`await self._gracefully_close_writer()` inside the
  command loop).
- What: the writer's `close()` + `wait_closed()` waits for the transport to flush, which a peer that has stopped
  reading prevents indefinitely. Scheduled callbacks reach the pipeline through the command queue, which is not being
  serviced meanwhile, so a `WriteTimeoutIoPipelineHandler` timing the `FinalOutput` fence - the one tool DESIGN 7 gives
  an application to bound exactly this - never fires; nor does anything else (idle events, `Await`s). The sync driver
  runs its timers from its readiness wait and delivers the timeout at the configured time; fdio likewise via the
  manager's deadlines. Verified with a 4 MiB payload against a non-reading socket pair: asyncio hangs until cancelled
  from outside, sync reports `TimeoutIoPipelineError` at 0.3s.
- Test: `drivers/tests/test_findings.py::TestAsyncioTimersDuringGracefulClose`.
- Suggested fix: perform the graceful close as a task (like drains) and keep servicing commands until it completes,
  or bound it.

## Known items from TODO.md deliberately not re-reported

These were already recorded by the author in `TODO.md` and were confirmed but not duplicated here: `ReadyForOutput`
still announced after `ShutdownOutput` by the TLS handler and HTTP chunking; host-facing messages not yet marked
`AfterShutdownOutput`; TLS reporting a pending `ShutdownOutput` as successful when a failed or EOF'd handshake drops
queued plaintext; the asyncio `ShutdownOutput` completing after `write_eof()` plus a drain rather than once the FIN
is sent; `_pending_awaits` not cleared on asyncio `close()`; the pure driver not modelling write failures.

## Notes

- N1. `Completable.get_result()` / `get_exception()` raise a bare `AttributeError` once the completable is done, even
  though `is_succeeded()` / `is_failed()` say it is: outcomes are released with the listeners (DESIGN 5). The API shape
  invites the mistake (the review's own first regression test made it). A clearer error, or a docstring on the getters,
  would help.
- N2. Darwin: nothing darwin-specific was found by reading. Checked: `shutdown(SHUT_WR)` semantics (ENOTCONN after a
  reset peer on both platforms, which the drivers turn into a driver failure); `socket.socket(fileno=os.dup(fd))` in
  `FdSyncIoPipelineDriver._shutdown_output` works without `SO_DOMAIN`/`SO_PROTOCOL`; `fcntl` flag handling; asyncio's
  `write_eof()` path. Note that `socket.socketpair()` buffers are far smaller on darwin (~8 KiB), so O1 bites sooner
  there, and the large-payload duplex tests take more round trips.
- N3. The pure, sync, and fdio drivers run a parent `Defer` as soon as it reaches the terminal, between the messages
  of one read batch. The multiplexer's `_end_batch` coalescing (DESIGN 13.5) therefore covers the frames decoded from
  one `feed_in` call - one decoded buffer - not the whole `_input_q` batch. Correct, just narrower than the asyncio
  driver, which feeds a whole batch in one call.
- N4. `IdleStateIoPipelineHandler` keeps firing `ALL_IDLE` after both `FinalInput` and `ShutdownOutput`, when no further
  activity is possible until `FinalOutput`. Matches its docstring ("leaving ... the combined state running"); possibly
  useful as a "close the zombie" signal, but worth a deliberate decision.
- N5. `PollAsyncioStreamIoPipelineDriver._drain_again` / `_next_drain_flush_outputs` are effectively unreachable:
  fences are held in `_post_drain_output_q` while a drain is pending, so `_request_drain` never sees one. Harmless.
- N6. A connection failure originating inside the multiplexer (adapter exception, control-output limit) is not reported
  to the parent pipeline as an `Error`: the parent only sees the encoded connection error frames and `FinalOutput`. An
  application monitoring the connection cannot tell a failure from a graceful shutdown without inspecting
  `MultiplexIoPipelineHandler._failed`.
- N8. `MultiplexCreditStrategy` has `adjust_all_send` but no receive-side counterpart: a protocol which changes its
  *own* advertised initial window (HTTP/2 `SETTINGS_INITIAL_WINDOW_SIZE`, which servers commonly raise) cannot
  adjust the windows of existing streams in the strategy - `_RecvAccount.advertise` only re-advertises consumed credit.
  The test adapter's `SendSettings` consequently only shifts the *peer's* send credit; raising it mid-stream makes the
  peer overrun the window the strategy still enforces, which the first version of the review's HTTP/2-like fuzzer did.
- N9. `IoPipeline.destroy()` called reentrantly from a handler's `Removed` notification fails a `check.state` (the
  pipeline is `DESTROYING`) with a bare `RuntimeError`, though the pipeline does end up `DESTROYED`.
- N10. Feeding through an invalidated context raises `AttributeError` (`_next_in` was deleted on removal) from
  `feed_in` / `feed_out` rather than `ContextInvalidatedIoPipelineError`, which only `_inbound` / `_outbound` check.
- N11. `drivers/tests/test_driver_edges.py::TestFdSyncSharedOpenFileDescription._fds` asserts `slave < read_fd`
  after `os.dup`, which depends on descriptor numbering; it held under pytest on 3.14 but failed under the 3.8
  unittest run (a lower descriptor was free). Harmless, but the test's premise comment ("whether it happens depends on
  the iteration order of `{read_fd, write_fd}`") describes the same ordering hazard F2 fixes for the restore path.
- N12. An application policy which destroys the pipeline from a timer callback while the sync driver is draining
  (the natural reaction to a write timeout during close) makes the driver fail with a bare `RuntimeError` from a
  `check.state(pipeline.is_ready)` in `next()`, rather than a pipeline error type; fdio's `on_timeout` has the same
  check.
- N7. Randomized testing done (throwaway scripts, not checked in): a loopback fuzzer driving one multiplexer with
  random conforming peer frames and local app actions under credit-conservation and data-order invariants (1050
  seeds x 300 steps, including yield policies, strict input flow, and apps which write on `ReadyForOutput`); two
  SSH-like multiplexers back to back over bounded pure links with random stream behaviors (120 seeds; found F4); two
  HTTP/2-like multiplexers likewise with padding, two-level credit, both replenish policies, and settings changes
  (120 seeds); two TLS peers over a pure link with random payloads, partial writes, link capacities, TLS 1.2/1.3,
  strict/lenient EOFs, and extra fences (150 seeds); and random multiplexed sessions over real socket pairs with the
  asyncio driver, with and without TLS (60 seeds). Nothing beyond the findings above surfaced.
