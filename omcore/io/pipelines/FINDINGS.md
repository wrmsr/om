# io.pipelines aggressive-review findings

Working document tracking a deep audit of `omcore.io.pipelines` (and the http pipelines bits touched by commit
`719299245` - "Add protocol-agnostic stream multiplexing and output half-close support").

Status legend: **SUSPECT** (not yet confirmed), **CONFIRMED** (demonstrated by a test), **FIXED** (inline fix applied),
**REPORTED** (called out to user, left as-is).

## Methodology

- Read the full change `719299245` and everything it touches.
- Write adversarial integration tests (no mocks/patches - real pipelines, pure drivers, socket pairs, TLS via real
  `ssl` contexts where feasible) targeting the new multiplex + half-close machinery first, then general pipeline
  robustness.
- Keep Darwin portability in mind (no Linux-only APIs in tests, avoid depending on specific `poll`/`select` behavior).

## Audit notes (code-reading suspicions, to be verified by test)

### Multiplex

1. **P1 - `credit.receive` before state check in `_data`/`_message` (handlers.py)**: `_data` checks
   `stream.can_receive_data` *before* debiting credit (good), but for a stream that is `remote_ended` yet still live
   (`HALF_CLOSED_REMOTE`, `can_receive_data` False), data raises `StreamStateMultiplexError` rather than being
   discarded-with-connection-window-accounting. Doc on `conn.data` says data for "a stream which already ended - reset,
   closed, or refused" is "counted against any connection-level window and dropped" - only *terminal* streams hit that
   path. Data arriving after `end()` on a live stream raises instead. Maybe intended (protocol violation), but H2
   allows DATA before... no, H2 forbids DATA after END_STREAM. OK probably fine.
2. **P2 - `_data` when `stream.local_finished` and `cost` is None**: `cost = len(data)` computed first, fine.
3. **P3 - `_close` on a stream in `_pending_establish` whose child is not yet created**: child is None ->
   `stream.close()` + completes open msg. But stream is in the table now CLOSED; `_release_done` will remove it since
   child is None -> child_done. OK.
4. **P4 - `_pump_child` when `self._parent_batch_open`**: delivery into children is suppressed while a parent batch is
   open, but `deliver_input()` is *also* the only place `FinalInput` is delivered. If input ends while a batch is
   permanently open (adapter always consumes without FlushInput and the batch-ending Defer...). Actually the
   batch-defer ends the batch. Need to check: `_end_batch` only runs when the defer was requested, which happens when
   the first non-lifecycle frame arrives. OK.
5. **P5 - `_emit_streams` budget check ordering**: budget/yield checked *after* `scheduler.next()` but *before*
   `_emit_unit`; when the budget runs out mid-turn, `continuation_pending` defers `_resume`. If the parent driver is a
   pure driver with nothing else to do, the Defer is processed as output - fine. But if the turn budget is exhausted by
   a *fence* (cost 0), no continuation issue. OK.
6. **P6 - `collect_output` runs child `Defer` synchronously via `pipeline.run_deferred`** - a defer whose fn feeds
   more output is collected in the same loop - fine. But a defer whose fn raises: `_fail`s the child. Hmm, and
   `run_deferred` calls `ctx._run_deferred` which `set_failed` + `_handle_error`... fine.
7. **P7 - `_remote_closed` drain (`_drain_remote_closed`)**: pops output; for fences other than final, completes with
   StreamResetMultiplexError. For 'final': completes and `child.finish()`. But note `child.complete(item.msg)` for
   'final' completes the FinalOutput *before* the data before it was emitted... but stream is remote-closed so data is
   discarded anyway. Design says "fences other than FinalOutput failing" - consistent.
8. **P8 - `_release_done` requires `child_done`**: a stream whose child is running but peer closed + child never
   finishes (app never sends FinalOutput) stays in the table forever. That's app policy, fine.
9. **P9 - `MultiplexChild.deliver_input` consumed-cost return on partial batch**: if `flush_segs()` fails mid-batch
   (child died), `return consumed` - costs of data already popped are returned - fine.
10. **P10 - `in_messages` limit check happens only for `cost == 0` messages** - a flow-controlled message bypasses the
    count limit. Documented ("uncontrolled typed input by a separate message-count limit"). OK.
11. **P11 - `_emit_unit` data path when `send_available - overhead <= 0`** returns 0 with no scheduler change; caller
    `_emit_streams` then `set_ready(key, False)` because cost <= 0 and no progress. Wait: `cost = 0` and queue
    unchanged -> `set_ready(key, False)`. But `_is_ready` would have returned False in this case
    (`send_available - overhead > 0` required) - and `_emit_streams` checks `_is_ready` first, so this path is
    unreachable... unless credit changed between check and emit (reentrancy). Defensive. OK.
12. **P12 - Refcounting/GC**: `_Connection` ctx manager sets `conn._h = None` on exit - but if adapter code raises,
    `self._fail(e)` is invoked in `inbound` *outside* the `with self._connection()`? No - the try wraps the with.
    Fine.
13. **P13 - `_open_local` with explicit=False**: `self._pending_establish[stream.key] = (msg.spec, msg)` - then the
    pump establishes and completes the OpenStream with `MultiplexOpenedStream`. OK.
14. **P14 - `OpenStream` fed when handler not in pipeline / already final-output**: `_open_local` completes with
    ConnectionClosedMultiplexError via `_complete_later`, then `_turn` runs `_emit` which completes it. But if
    `_final_output_sent`, `_emit` clears control q and returns *before* completions? Look: completions are pumped
    first in `_emit`, *then* `if self._final_output_sent: clear + return`. OK, completions still happen.
15. **P15 - `_fail` -> `_emit` ordering**: `_fail` sets `_dirty = True` so turn loops; `_release_done` removes terminal
    streams; then `accepting` False; FinalOutput sent when table empty. But `_fail` calls `_reset_stream` for every
    stream with `by='local'`... without `encode=True`, so no reset frames emitted (connection is dying; goodbye
    instead). OK.
16. **P16 - `shutdown` race**: `_on_shutdown` -> adapter.on_shutdown -> `conn.begin_shutdown()` sets
    `_shutting_down=True`. Then `_emit`: when table empty -> FinalOutput. But what if shutdown is requested while
    streams are active and then all streams end: `_release_done` removes, then next `_emit` sees empty table ->
    FinalOutput. But what if `_shutting_down` and table empty *from the start* (no streams): FinalOutput immediately.
    OK.
17. **P17 - `_on_input_ended` + `begin_shutdown` from default `on_input_ended`**: after EOF, streams not reset carry
    on... but `accepting` False now (`_input_ended`). `Shutdown` + table eventually empties -> FinalOutput. OK.
18. **P18 - `MultiplexChildScheduling._fire`** runs `fn` inside `pipeline.enter()` and calls
    `host.on_child_activity(ctx)` - the `ctx` here is the *parent ctx* supplied by the parent's scheduling service via
    `schedule_context(parent_ctx.ref, ...)`. Parent service supplies its own ctx. OK.
19. **P19 - child `feed` from `FeedStream` after child finished**: `feed` returns False if not running; msgs dropped.
    Documented ("Ignored if the stream has no running pipeline"). OK.
20. **P20 - `_emit` child awaits**: forwards as parent Await; if parent driver can't await (pure/sync driver) - the
    Await reaches the parent's terminal as *unhandled output* - returned from `next()`. Documented. OK.
21. **P21 - `emit` phase: `self._want_parent_read` reset BEFORE `maybe_ready_for_input`** - re-entrant events could set
    `_want_parent_read` again; handled since turn loops on dirty. OK.
22. **P22 - `_queue_grants` skips grant for stream with `remote_ended`** - but *connection-level* grants (key None) are
    always emitted. Hmm: after Shutdown (connection closing), do we keep granting connection credit? `_release_done`
    -> `pending_grants()` emitted even when shutting down - harmless control output. OK.
23. **P23 - `discard_receive` on StreamMultiplexCreditStrategy returns ()** - fine, no connection window.
24. **P24 - `ConnectionMultiplexCreditStrategy.receive` with `connection_replenish_on='receive'`**: connection window
    is freed on arrival (`self._recv.consume(cost)`) -> `pending_grants()` -> advertised if policy says. Note
    `HalfWindow` policy: `unadvertised * 2 >= window`. As cost arrives, `unadvertised` grows; once half, re-advertise.
    OK. BUT `receive` calls `self._recv.receive(cost)` via `check.state(...)` after checking `cost >
    self._recv.outstanding` - consistent.
25. **P25 - `_RecvAccount.advertise` requires `amount <= unadvertised`**: replenish policy returns `min(unadvertised,
    ...)`? `HalfWindow.replenish(window, unadvertised)` returns `unadvertised` - ok. A *custom* policy returning more
    than unadvertised trips check.arg - acceptable (policy contract).

### Half-close / core

26. **P26 - core `_terminal_outbound`**: when `_saw_shutdown_output` and msg is ShutdownOutput again -> raises
    SawShutdownOutputIoPipelineError (good, dup shutdown rejected). When `_saw_final_output`, *any* further message
    raises SawFinalOutputIoPipelineError - including AfterShutdownOutput ones. Correct per contract ("No output may
    reach the pipeline terminal after FinalOutput").
27. **P27 - `OutboundBytesBufferIoPipelineHandler` on ShutdownOutput**: flushes, forwards. But note the flush does NOT
    announce writability; next `ReadyForOutput` from downstream... `_downstream_writable` unchanged. Hmm - after
    ShutdownOutput passes, any later FlushOutput calls `_flush(ctx)` (announce allowed). Edge.
28. **P28 - SSL handler `_hold_behind_retained_fence`**: when `_close_requested` and `not _final_output_sent`, fences
    (incl. a second FinalOutput? no - FinalOutput handled by `_on_outbound_final_output` which returns early for
    duplicates... wait: `_on_outbound_final_output` checks `if self._close_requested or self._final_output_sent:
    return` - it *drops* a duplicate FinalOutput silently after `mark_propagated`. But the duplicate is MustPropagate -
    mark_propagated called at top. But the Completable never completes! A second FinalOutput is bound to the pipeline
    in `_outbound` (pending_completables) and never completed -> `pipeline.destroy()` will fail it. Actually does
    destroy fail pending completables? Need to check core destroy. If yes, ok-ish. But the *first* FinalOutput
    completes normally when driver finishes. Duplicate final output is an app bug; failing it on destroy is fine.
29. **P29 - SSL `_on_outbound_shutdown_output` when state is CLOSED (e.g. after peer close + error)**: 
    `_shutdown_output_requested = True`, `_pending...`, `_turn` -> `_step_shutdown` -> `_step_half_close`? state CLOSED
    -> `_step_shutdown` returns False (state == CLOSED). So no close_notify. Then `_emit` step 3: pending and no flush
    and `_close_notify_sent or state == CLOSED` -> state CLOSED -> `_send_shutdown_output`. OK, forwarded.
30. **P30 - SSL: app sends ShutdownOutput *before* InitialInput/handshake (state NEW/HANDSHAKE)**: `_step_half_close`
    returns False for NEW/HANDSHAKE ("session established first"). Once handshake completes (ESTABLISHED), pump
    progresses and `_step_shutdown` runs `_step_half_close`. If handshake never completes (no peer), shutdown stays
    pending; FinalOutput later -> `_step_close` sees NEW/HANDSHAKE -> if `_write_q or _shutdown_output_requested or
    _pending_flush_outputs` -> returns False -> stuck until handshake timeout -> `_on_state_timeout` releases pending
    shutdown + final. Covered by timeouts only when configured. Fine.
31. **P31 - SSL `inbound` FinalInput consumed + `mark_propagated`, then synthetic FinalInput fed later**: if engine
    already at `_plaintext_eof` and `_inbound_eof_sent`? Only once. OK.

### Drivers

32. **P32 - pure driver `_do_read` when `remaining < 1` but input queue still has msgs**: breaks, next read continues.
    OK. But note: `feed_eof` appends FinalInput to transport queue; `_do_read` pops msgs until FinalInput; msgs after?
    None can be fed after feed_eof (check.state(not self._fed_final_input)). OK.
33. **P33 - pure driver `_poll` order: output poll before input_q feed** - output generated, then input fed, loop. But
    when `_transport_final_output` set -> clears *transport* input queue (discard) and returns 'write'. But
    `self._input_q` (already-decoded msgs) still fed first (the `if self._input_q` branch is before). Hmm - after
    FinalOutput, pipeline saw final output; feeding more input msgs is allowed (AfterFinalInput check in _feed_in_to
    only). Wait: `_feed_in_to` raises SawFinalInputIoPipelineError if msg not AfterFinalInput *after FinalInput seen* -
    but FinalOutput doesn't block input. OK.
34. **P34 - sync driver `next(read=False)`**: writes drained, fences complete, listener output processed via
    `pipeline.output.peek() is not None` continue. But *input_q* messages? `continue` re-polls: `_poll` feeds input_q
    then... returns 'read' if want_read; next(read=False) -> `return None`. So enqueued input is processed even in
    read=False mode. Hmm - "process output generated by fence-completion listeners during the same step". OK.
35. **P35 - fdio `_handle_output` FlushOutput with empty write_q completes immediately** - but there might be a
    *previously completed* shutdown... fine.
36. **P36 - fdio `on_writable` -> `_try_flush_write_q` -> `_complete_shutdown_output` -> `sock.shutdown` fails with
    OSError (e.g. not connected / already shut down by peer?) -> `_fail()` + raise. On Darwin, shutdown(SHUT_WR) on a
    socket where peer already closed can raise ENOTCONN? Actually shutdown after peer close is usually fine; ENOTCONN
    if never connected. Edge.

## Findings

### F1 - CONFIRMED - Duplicate `FinalOutput` crashes pure/sync/fdio drivers with a bare `ValueError`

The pipeline terminal (`IoPipeline._terminal_outbound`, core.py:1614-1617) accepts a second `FinalOutput` (it only
raises `SawFinalOutputIoPipelineError` for messages sent *after* one). But three of the four drivers do
`check.none(self._transport_final_output)` when handling it:

- `drivers/pure.py:451` - `check.none` raises bare `ValueError: Must be None` out of `_poll` -> `next()`, failing the
  whole driver and losing the first FinalOutput's graceful drain.
- `drivers/sync.py:555` - same in `_handle_output`, raised out of `next()`.
- `drivers/fdio.py:464` - same: the first FinalOutput returns 'stop', the *next* `poll()` raises `ValueError`.
- `drivers/asyncio.py` - the outlier: `_handle_output_final_output` re-runs the final path; the first FinalOutput
  succeeds, the second is failed gracefully by pipeline destroy. No crash.

Reproducer (no mocks, verified pure + sync + fdio): from inside a handler feed `FinalOutput()` twice before the driver
polls, then `next()`.

Net: an app bug (double close) turns into a hard driver failure with a confusing `ValueError: Must be None` on 3 of 4
drivers, inconsistent with both the terminal's tolerance and asyncio's graceful handling. Suggested fix: when
`_transport_final_output` is already set, fail the duplicate as a Completable (`msg.set_failed(...)`) and drop it,
rather than `check.none`.

Demo tests: `/tmp/muxscratch/t48_dupf.py` (pure+sync), `/tmp/muxscratch/t49_dupf_fdio.py` (fdio),
`/tmp/muxscratch/t50_dupf_aio.py` (asyncio - graceful).

**STATUS: FIXED inline** (not committed). The three drivers now fail a duplicate FinalOutput as a Completable with
`SawFinalOutputIoPipelineError` instead of `check.none`-crashing, matching asyncio's graceful handling and the
terminal's tolerance. Regression test enshrined at
`omcore/io/pipelines/drivers/tests/test_dup_final_output.py` (3 tests, all pass post-fix; all fail pre-fix).
`omdev/scripts/ci.py` regenerated via `make gen` (it amalgamates `drivers/sync.py`). `make fix check` clean;
full `omcore/io/pipelines` + `omcore/http/pipelines` suite: 843 passed.

### F2 - RESOLVED (not a bug) - reset of a finished stream completes its pending FinalOutput on flush

Initially suspected a fence-completion leak: a reset arriving while a finished stream's parent flush fence is pending.
Verified the weakly-referenced `_on_parent_flush_done` still completes the FinalOutput once the parent drains, both for
reset and close. The completion happens at transport-boundary time, not at reset time - consistent with the fence
contract. If the connection dies before the flush, pipeline destroy fails the pending fence. No bug.

### F3 - NOTE (UX footgun) - `_check_can_add` raises `TypeError: unhashable` for unhashable handler

`IoPipeline._check_can_add` does `check.not_in(handler, self._unique_contexts)` (a dict membership) before any
isinstance check; an unhashable object (e.g. an `IoPipeline.Spec` mistakenly fed as a handler) produces
`TypeError: cannot use ... as a dict key (unhashable type)` rather than a clean "not a handler" error. Cosmetic.

### Additional probes - all correct behavior (no bugs)

- Reentrant `OpenStream` from within an open-completion listener: completes correctly after confirm.
- Reentrant `Shutdown` from a completion listener: connection begins draining.
- Grants for a stream reset/ended in the same parent batch are correctly suppressed (no grant on a dead stream).
- Parent flush failure (pipeline destroy mid-drain) fails *all* folded child fences.
- Child timer failure resets only its own stream; healthy siblings survive; no connection failure.
- Child timers are cancelled on stream reset; child pipeline is GC-collectable after close (no cycles).
- Manual-read children: one token = one batch bounded by `read_batch_max_bytes`; an oversized single data unit is
  delivered whole (documented "whole data units"); a token arriving with nothing queued remains outstanding.
- Control output during a prolonged parent pause is bounded by `max_control_during_pause`, then fails the connection
  with `ControlOutputLimitMultiplexError`.
- DRR scheduler fuzzed (200 seeds): no rotation/ready divergence, no starvation.
- Credit strategies fuzzed (300 + 400 + 60 seeds): send/recv conservation holds; overruns detected;
  connection-level `receive`/`consume` replenish both conserve the window exactly against a reference ledger.
- TLS half-close during handshake with queued plaintext works over pure drivers with real `ssl`.
- Full-duplex 2MiB concurrent half-close over real TCP (asyncio driver) works.
- Child `Await` is forwarded to the parent (unhandled on pure driver as documented; awaited on asyncio driver).
- Child `Defer` runs and can produce output reentrantly.

### Further probes - all correct (no bugs)

- Emit order within a single turn: control output (LAccept) precedes stream output (LData); completions precede both.
- Remote-closed stream: further child output discarded, non-final fences fail with `StreamResetMultiplexError`,
  FinalOutput completes and releases the stream.
- Turn budget: a single data unit may overshoot the budget by up to `max_data_unit` (documented "units are never
  split"); with a small `max_data_unit` the budget is respected to within one unit and emission continues via parent
  Defer. Not a bug.
- Fence-only stream under zero credit: emits immediately, no emit-loop spin.
- Typed-message splitting across credit works; an adapter whose `split_message` violates the cost contract trips
  `check.state` (loud failure - correct; the adapter contract is documented).
- Mass teardown (parent destroy with pending opens, fences, timers, remote+local streams): all opens and fences
  resolve, all child pipelines collectable. No cycles. (One apparent "leak" was the test holding
  `MultiplexOpenedStream.pipeline` - by design.)
- `FdSyncIoPipelineDriver` with the same socket fd for read+write: ShutdownOutput works via the dup-and-shutdown path.
- fdio driver in DRAINING discards transport input so a blocked peer finishes; closes cleanly.
- Sync driver: 1MB half-close stress over a real socket pair with a slow reader - correct ordering, both fences
  complete.
- Stream outbound queue: `pop_out_data` splits memoryviews mid-segment, `out_head_data_bytes` stops at the first
  non-data item, `pop_out_item` on a data head raises and restores, `clear_out` returns only non-data items.

### Test battery 1 (16 tests) - all passing

Wrote `/tmp/muxscratch/test_mux_adversarial.py`: open/refuse/limit races, dup remote key -> connection error,
half-close ordering under credit block, write-after-child-shutdown, reset dropping queued output and failing fences,
truncated/opening streams on EOF, negative window adjust, zero window, per-frame overhead credit accounting. All pass.
