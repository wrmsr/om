# io.pipelines proposed fixes

Proposed fixes for the open findings in [FINDINGS.md](FINDINGS.md). Nothing described here is implemented; the fixed
findings F1-F4 are in the tree and not repeated. Each section names the exact code to change, the mechanics, the
edge cases that need care, and the test migration: every open finding has a deliberately failing test in a
`test_findings.py` module which becomes a passing regression test in the sibling `test_regressions.py` once the fix
lands.

Decisions already taken:

- O2: typed messages queued behind end-of-input are delivered without a read token.
- O4: the protocol adapter owns whether credit is re-advertised on a half-closed-local stream; the core's accounting
  must follow what the adapter actually put on the wire.
- O7: not fixed in code. Documented loudly; no exception, no warning.

Suggested order: O6, O5, O2 (small and independent) - O3 - O4 - O1 sync - O1 asyncio with O8 (one change) - O7 docs.

---

## O1 (sync half). `SyncIoPipelineDriver` keeps reading, and discards, while draining

Files: `drivers/sync.py`.

### Change

Mirror `IoPipelineDriverSocketFdioHandler`, which already does this (`readable()` returns `not _drain_input_ended`
while `DRAINING`, `on_readable()` calls `_discard_input()`).

1. State. Add `self._drain_input_ended = False` in `__init__`, reset it in `close()` and `_fail()` alongside
   `_pending_read_error`.

2. Discarding. Add to the abstract base:

   ```python
   def _discard_input(self) -> None:
       buf = memoryview(bytearray(self._config.read_chunk_size))
       for _ in range(self._config.read_batch_max_reads):
           try:
               n = self._read_into(buf)
           except BlockingIOError:
               return
           except OSError:
               self._drain_input_ended = True
               return
           if not n:
               self._drain_input_ended = True
               return
   ```

   It uses the subclass's `_read_into`, so it works for sockets and descriptor pairs alike.

3. Waiting. In `next()`, where `want_read` / `want_write` are computed before `_wait_for_io_or_timer`:

   ```python
   draining = self._transport_final_output is not None
   if draining:
       want_read = not self._drain_input_ended and not pipeline.saw_final_input
   else:
       want_read = not pipeline.saw_final_input and self._want_read
   ```

   and after the wait, on `readable`: `self._discard_input()` when draining, else the existing
   `self._input_q.extend(self._do_read())`. Treat a discard as progress (`progressed = True`) only if something was
   read, otherwise the loop spins; simplest is to make `_discard_input` return a bool.

4. `_poll()` is unchanged: while draining it still returns `'write'` (queue non-empty) or `'stop'`. The only new
   behavior is that the readiness wait during `'write'` also watches the read side.

### Edge cases

- Input already in `_input_q` when `FinalOutput` is handled stays there and is dropped on close, as today. Input has
  no consumer after `FinalOutput`; feeding it would reach a pipeline whose output terminal is closed.
- `pipeline.saw_final_input` true means the transport already returned EOF: nothing more will arrive, so the read
  side is not watched. If a read error is pending (`_pending_read_error`), `_poll` raises it before draining matters.
- `read=False` is unchanged (it never waits).
- The write-side failure when the peer closes first: the loser of the symmetric case gets `BrokenPipeError` /
  `ConnectionResetError` from `_write`, which `_try_write` turns into `_fail()` + raise. That is the outcome the fdio
  test asserts and `drivers/tests/test_findings.py::TestDrainingDuplexDeadlock` expects.
- Darwin: nothing platform-specific; `recv_into` and `os.read` behave the same.

### Tests

- Move `TestDrainingDuplexDeadlock.test_sync_both_draining` to `drivers/tests/test_regressions.py`.
- Add a descriptor-pair variant (`FdSyncIoPipelineDriver` over a `socketpair` fd pair) to cover `_read_into` via
  `os.read`.
- The conformance suite (`drivers/tests/test_conformance.py`) and `test_sync.py` must stay green; the sync scenarios
  that end with `FinalOutput` while the peer still sends will now discard that input instead of leaving it in the
  socket, which no existing assertion depends on.

### Docs

DESIGN 8's driver-specific list: the sentence "While draining after `FinalOutput`, the pure and fdio drivers keep
taking input off the transport and discard it" extends to the sync driver.

---

## O1 (asyncio half) + O8. Graceful close as a task, commands serviced while draining

Files: `drivers/asyncio.py`.

These are one change: the deadlock exists because the read task is cancelled and the close is awaited inside the
command loop; the dead timers exist because the close is awaited inside the command loop.

### Current flow

`_handle_output_final_output` sets `_shutdown_event` (which stops the read task, makes `enqueue` refuse, and stops
drain callbacks from posting), awaits the pending drain's cancellation, cancels the read task, awaits
`_gracefully_close_writer()` (`writer.close()` + `wait_closed()`), finishes fences and the `FinalOutput`, and returns
`'stop'`, on which `next()` destroys the pipeline and goes `CLOSED`. While `wait_closed()` is pending nothing in the
driver runs.

### Change

1. New state: `self._close_task: ta.Optional[asyncio.Task] = None` and a `_CloseCompletedCommand(task)` dataclass
   with a handler registered in `_build_command_handlers`. Keep `self._transport_final_output` (the `FinalOutput`
   being drained) as the sync/fdio drivers do.

2. `_handle_output_final_output(msg)` becomes non-blocking:
   - `self._state = DRAINING`; `self._transport_final_output = msg`.
   - Do **not** set `_shutdown_event`; the read task must keep running (see 4).
   - Cancel a pending drain task synchronously (`task.cancel()`, `self._drain_task = None`, `_drain_again = False`)
     but keep its fences in `_drain_flush_outputs`; they complete when the close completes, exactly as today.
     `_handle_command_drain_completed` already ignores a task which is no longer `self._drain_task`.
   - Start `self._close_task = asyncio.create_task(self._graceful_close_writer())` with a done callback posting
     `_CloseCompletedCommand(task)` (unconditionally; the handler checks identity).
   - Return `'handled'`.

3. `_handle_command_close_completed(cmd)`:
   - If `cmd.task is not self._close_task`: return. Else `self._close_task = None`.
   - `cmd.task.result()` inside `try`. On an exception `e` (the peer reset the connection mid-flush, say): finish the
     fences from `_take_drain_flush_outputs()` with `e`, `_finish_final_output(msg, e)`, `await self._fail()`, raise.
   - On success: `_finish_flush_outputs(self._take_drain_flush_outputs())`, then `_finish_final_output(msg)`, then
     set `_shutdown_event`, `_want_read_event.set()`, cancel the read task (`await self._cancel_tasks(self._read_task)`)
     and post `_ShutdownCommand()`. The existing loop in `next()` breaks on `_ShutdownCommand`, destroys the pipeline
     and sets `CLOSED` - the same tail as today's `'stop'`.

4. Reads while draining are discarded, not fed. In `_handle_command_read_completed`: if `self._state is DRAINING`,
   drop the data, do not feed the pipeline, and (manual mode) `self._want_read_event.set()` so the read task keeps
   going; on EOF (`not data`) nothing further is needed since the read task exits by itself. The transport stops
   buffering once the stream reader's limit is hit, which is why the peer stalled before; a continuously consumed
   reader keeps it reading.

5. `enqueue` / `enqueue_waitable`: replace the `_shutdown_event` check with `check.state(self._state in (NEW,
   RUNNING))` so injected input is still refused while draining.

6. `close()`: cancel `_close_task` too (same pattern as `_cancel_drain_task`), before `_abort_writer()`.
   `_has_pending_work()` includes `_close_task`.

7. The `_start_drain` done callback keeps its `_shutdown_event` guard (the event is only set once the close
   completed or `close()` ran).

8. Output during draining: after F1, every message reaching the terminal after `FinalOutput` is rejected by the core,
   so the loop sees no further pipeline output; commands (timers, awaits, drain and close completions) are the only
   work, and they are now serviced.

### Edge cases

- A timer firing during the drain whose callback destroys the pipeline (the natural reaction to a write timeout, N12):
  `_handle_command_scheduled` runs it; afterwards the pipeline is `DESTROYED`. Add to `_handle_command`: if the
  pipeline is no longer ready and the state is `RUNNING` or `DRAINING`, `await self.close()` and stop the loop. The
  `_finish_*` helpers already tolerate a completable the destroy failed (`is_done()` guards).
- Write timeout then nothing else: the close task stays pending until the peer reads or the transport is aborted;
  bounding the close with a timeout is a separate decision, not needed to fix O1/O8.
- `wait_closed()` raising `ConnectionResetError` after a deliberate close is the success-or-failure path in 3; the
  pending drain task is cancelled first so it cannot report that reset ahead of the close (today's reason for
  cancelling it).
- The pure driver's `drain_output()` semantics are unaffected.
- The `test_duplex.py` asyncio cases, `test_asyncio.py`, `test_asyncio_backpressure.py`, the ASGI/HTTP backpressure
  tests, and the conformance suite exercise this path heavily; run all of them.

### Tests

- Move `TestDrainingDuplexDeadlockAsyncio.test_asyncio_both_draining` and
  `TestAsyncioTimersDuringGracefulClose.test_write_timeout_fires_while_final_output_drains` from
  `drivers/tests/test_findings.py` to `drivers/tests/test_regressions.py`.
- Add: an idle-state or scheduled callback running during the drain of a peer which *does* read (close completes
  normally and `FinalOutput` succeeds, `CLOSED`); a close task failing with a reset peer (`FinalOutput` failed,
  `FAILED`); `close()` while the close task is pending.

### Docs

DESIGN 8 asyncio bullet: the graceful close happens in a task; commands, timers and reads (discarded) proceed
meanwhile. Add the asyncio driver to the "discard input while draining" sentence.

---

## O2. Typed messages behind end-of-input are delivered without a read token

Files: `multiplex/children.py` (`MultiplexChild.deliver_input`), DESIGN 13.

### Change

The outer loop in `deliver_input` breaks in manual mode when no token is outstanding. Once `FinalInput` has been
delivered only `MultiplexInputMessage` items can remain (`push_in_data` refuses data behind an end), and they carry
no read semantics, so the token requirement is waived from that point:

```python
while self.is_running and stream.in_head() is not None:
    if not self._auto_read and not self._want_read and not self._final_input_delivered:
        break
```

That single condition covers both shapes: messages decoded in the same read as the end (the inner loop breaks at
`MultiplexInputEnd`, feeds `FinalInput`, and the next outer iteration now continues into the trailing messages) and
messages arriving later (`deliver_input` is called on every pump; with the end delivered they go straight in).

Nothing else changes: batches of post-EOF messages still carry no `FlushInput` (the existing
`not self._final_input_delivered` guard), `_want_read` is still cleared per batch in manual mode (harmless), and the
`max_stream_input_messages` limit still bounds what can queue.

### Edge cases

- A post-EOF message not marked `AfterFinalInput` fails in the child's `feed_in` with
  `SawFinalInputIoPipelineError`, which fails the child and resets the stream - the same outcome as today, just at
  arrival rather than on a token which never comes. Worth a sentence in DESIGN 13.
- `wants_input` (used only for progress accounting in `_pump_child`) already excludes the post-EOF state; the
  before/after queue-size comparison in `_pump_child` reports the progress.
- Flow-controlled typed messages behind the end (`cost > 0`) are consumed and their credit replenished as before;
  with O4 the adapter decides whether that grant goes out (SSH: not after CLOSE).

### Tests

- Move `TestManualReadMessageAfterEnd` (both tests) to `multiplex/tests/test_regressions.py`.
- `test_flow.py::test_manual_child_receives_nothing_without_tokens` (pre-EOF) must still pass.
- Add an SSH-like end-to-end case with manual-read children on both sides receiving `exit-status` after EOF
  (`test_sshlike.py` has the auto-read version).

### Docs

DESIGN 13 item 5: "A token arriving with nothing queued remains outstanding" gets "Typed messages queued behind
end-of-input are not reads and are delivered without a token." The `deliver_input` docstring likewise.

---

## O3. Adapter failures while encoding fail the connection like failures while decoding

Files: `multiplex/handlers.py`.

### Change

Route every adapter call through one guard. The guarded calls today are `inbound`, `open_local`, `on_shutdown`,
`on_input_ended`, `on_stream_finished` and `encode_connection_error`; the unguarded ones are, by site:

| Site | Adapter calls |
| --- | --- |
| `_queue_grants` | `encode_credit` |
| `_open_local` (after the `try`) | `encode_open` |
| `_establish` | `encode_refuse`, `encode_accept` |
| `_reset_stream(encode=True)` from `_pump_child`, `_establish`, `_release_done` | `encode_reset` |
| `_is_ready` | `max_data_unit`, `data_unit_overhead`, `message_cost`, `split_message` |
| `_emit_unit` | the same four plus `encode_data`, `encode_message`, `encode_end`, `encode_finish` |
| `_pump_child` via `collect_output(claim)` | `claim_output` |
| `_release_done` | `on_stream_released` |

Add:

```python
def _adapter(self, fn: ta.Callable[..., T], *args: ta.Any, default: T) -> T:
    try:
        return fn(*args)
    except Exception as e:  # noqa
        self._fail(e)
        return default
```

and use it at each site with a default which makes that site a no-op: `()` for every `encode_*`, `0` for
`max_data_unit` / `data_unit_overhead` / `message_cost` (a zero unit makes `_is_ready` false), `None` for
`split_message` and `on_stream_released`, `False` for `claim_output` (the message is then rejected inside the child,
which is already being aborted by `_fail`).

Why a guard per call rather than around the whole turn: `_fail` is idempotent but `_turn` loops while dirty, and an
adapter which raises on every `on_stream_released` would then raise again from the next pump's `_release_done` with
the connection already failed - a turn-level `except` would either loop forever or let the second exception escape.
Per-call guards with no-op defaults make progress regardless.

### Edge cases

- `_emit_unit` consumes send credit before encoding data. If `encode_data` raises, `_fail` resets every stream, the
  unit is lost, and the consumed credit no longer matters. `_emit_streams` then finds nothing ready (all streams are
  terminal), `_emit` runs on to the control queue (connection error) and, once the pump has released the streams,
  `FinalOutput`. This is the existing `_fail`-during-emission path, covered by
  `test_flow.py::test_failure_during_emission_still_finishes_the_connection`.
- `claim_output` raising inside `collect_output`: the lambda in `_pump_child` must wrap it (the guard call goes in the
  lambda), since `collect_output` only guards `run_deferred`.
- `on_stream_released` is a notification: after `_fail` the release still completes (the default is `None`), so the
  table empties and the connection finishes.
- `_fail` itself already guards `encode_connection_error`.
- Second failure while failed: `_fail` returns at once; the default keeps the site a no-op. Add a test for an adapter
  which raises from `on_stream_released` on every call: the connection must still emit its connection error and
  `FinalOutput`, and the driver must close `CLOSED` rather than `FAILED`.

### Tests

- Move `TestAdapterFailuresWhileEncoding` to `multiplex/tests/test_regressions.py`.
- Add cases for `encode_credit`, `encode_reset`, `claim_output` and `max_data_unit` raising, plus the repeated
  `on_stream_released` failure above.

---

## O4. Credit accounting follows the wire; the adapter decides whether to re-advertise

Files: `multiplex/credit.py`, `multiplex/handlers.py` (`_queue_grants`), `multiplex/adapters.py` (docstring),
`multiplex/tests/sshlike.py`, DESIGN 13.

### Change

1. Strategy: add a way to take back a grant the handler did not emit.

   ```python
   class _RecvAccount:
       def withdraw(self, amount: int) -> None:
           check.arg(0 < amount <= self.outstanding)
           self.outstanding -= amount
           self.advertised -= amount
           self.unadvertised += amount
   ```

   and on `MultiplexCreditStrategy` an abstract `withdraw(key: Optional[MultiplexStreamKey], amount: int) -> None`:
   per stream in `_BaseMultiplexCreditStrategy` (`self._accounts(key).recv.withdraw(amount)`), and for `key is None`
   on `ConnectionMultiplexCreditStrategy` (`self._recv.withdraw(amount)`; `StreamMultiplexCreditStrategy` raises
   `TypeError` as its other connection-level methods do). A withdrawn grant is simply unadvertised credit again and is
   proposed afresh by the replenish policy on the next consume. The conservation invariant
   `advertised == received + outstanding` holds throughout.

2. Handler: `_queue_grants` no longer decides for the adapter on half-closed-local streams. For each grant:
   - If the stream is gone, terminal, `remote_ended`, or in `_remote_closed`: nothing more will arrive on it, so the
     grant is withdrawn without consulting the adapter (today's skip, made honest).
   - Otherwise (including `local_finished`) call `encode_credit(stream, amount)`; if it returns an empty sequence,
     withdraw; else extend the control queue.
   - Connection-level grants (`key is None`) are always offered and withdrawn if declined.

   With O3 in place the `encode_credit` call goes through `_adapter(...)` with default `()`, which also withdraws.

3. Adapter contract: `encode_credit`'s docstring states that returning an empty sequence declines the grant - the
   credit stays unadvertised and will be offered again - and that the core offers grants for a stream whose local
   side has finished, since a protocol such as HTTP/2 may keep receiving there while another such as SSH must send
   nothing after CLOSE.

4. `tests/sshlike.py`: `encode_credit` returns `[]` when `self._st(stream).close_sent` (RFC 4254: no messages on a
   channel after CLOSE). The h2-like and loopback adapters keep encoding unconditionally.

### Edge cases

- `_data` on a `local_finished` stream consumes at once; the resulting grant is now offered, so an h2-like peer
  keeps its window and a conforming SSH peer runs out of window exactly as it should after our CLOSE.
- The half-window policy proposes the whole unadvertised amount on each consume; an adapter which keeps declining
  sees one `encode_credit` per data frame and one withdraw each - constant work, no growth.
- `remove_stream` on the connection strategy (`consume` mode) consumes the stream's queued cost at connection level;
  the resulting connection grant is offered as before.
- `MultiplexCreditTotals` needs no change; `recv_advertised` now means "advertised on the wire".

### Tests

- Move `TestReceiveCreditAfterLocalFinish` to `multiplex/tests/test_regressions.py`.
- Add `test_credit.py` cases: `withdraw` conservation per stream and per connection; `withdraw` of an unknown stream
  raises `UnknownStreamMultiplexError`.
- Add a loopback case with an adapter which declines every grant: `recv_advertised` stays at the initial window, the
  peer is refused beyond it (`FlowControlMultiplexError`), and a later consume re-offers.
- Add an SSH-like case: after our CLOSE on a channel the peer keeps sending within its window, no `SshWindowAdjust`
  goes out, and the channel still releases on the peer's CLOSE.

### Docs

DESIGN 13 "Flow control": replace "Credit is not granted on a stream the peer has ended or closed" with the three-way
rule above (not offered where nothing more can arrive; offered otherwise; the adapter may decline; accounting follows
the wire).

---

## O5. A stream spec factory which raises refuses that stream

Files: `multiplex/handlers.py` (`_open_remote`), DESIGN 13.

### Change

```python
try:
    res = self._spec_factory(opening)
except Exception as e:  # noqa
    res = MultiplexRefusal(e)
```

The rest of `_open_remote` already handles a `MultiplexRefusal`: counted in `refused_remote`, encoded with
`encode_refuse(opening, reason)` where the reason is now the exception. Nothing was added to the table or the credit
strategy before the factory ran, so there is nothing to undo.

### Edge cases

- The exception is not reported to the parent pipeline (consistent with N6 for connection-level failures); the
  refusal reason carries it to the peer's encoder. If the application wants to observe factory errors it can do so in
  the factory itself.
- `MultiplexChild.__init__` already converts construction errors into a refusal; the two paths now agree.

### Tests

- Move `TestStreamSpecFactoryFailure` to `multiplex/tests/test_regressions.py`.
- Extend the SSH-like and h2-like refusal tests with a raising factory (the peer sees `SshOpenFailure` /
  `H2RstStream(REFUSED_STREAM)`; other streams proceed).

### Docs

DESIGN 13 "Model": "which may refuse them" becomes "which may refuse them by returning a `MultiplexRefusal`, or by
raising".

---

## O6. The input lifetime begins only at the outermost position

Files: `core.py` (`IoPipeline._feed_in_to`), `multiplex/README.md`.

### Change

The boundary bookkeeping in `_feed_in_to` (the `SawFinalInputIoPipelineError` check, `_saw_final_input`,
`_saw_initial_input`, `_saw_any_input`) describes transport input crossing the pipeline boundary. A message injected
at a handler's position with `feed_in_to` is not transport input. Apply the bookkeeping only when the target context
is `self._outermost`:

```python
def _feed_in_to(self, ctx, msgs):
    self._step_in()
    try:
        boundary = ctx is self._outermost
        for msg in msgs:
            if boundary:
                ...existing checks and flag updates...
            ctx._inbound(msg)
    finally:
        self._step_out()
```

`feed_in`, `feed_initial_input` and `feed_final_input` all target `_outermost`, so driver behavior is unchanged.
`feed_in_to` (public, "TODO: remove? internal only?") no longer touches the flags.

### Edge cases

- The only in-repo callers of `feed_in_to` are tests (`tests/test_core.py`, `multiplex/tests/test_teardown.py`) and
  the multiplex README's documented use; none relies on the flags.
- Injecting `InitialInput` or `FinalInput` at a handler position is no longer checked against the lifetime. That is
  the replace-self pattern the method exists for (re-feeding a lifecycle message to a replacement handler mid-feed),
  which today would raise `SawFinalInputIoPipelineError` for a re-fed `FinalInput` because the boundary already set
  the flag - another reason for the change. Must-propagate tracking still applies.
- `saw_any_input` keeps its meaning: transport input has begun.

### Tests

- Move `TestInjectedInputBeforeInitialInput` (`tests/test_findings.py`) and `TestOpenBeforeInitialInput`
  (`multiplex/tests/test_findings.py`) to the sibling regression modules.
- Add: `feed_in_to` of a `FinalInput` to a replacement handler from within the original `FinalInput` handling does
  not raise.

### Docs

README of multiplex: note that `feed_in_to` may be used before the driver's first step. Core docstring of
`feed_in_to`: injected messages are outside the input lifetime checks.

---

## O7. Strict ragged-EOF detection on Python 3.8: document, no code change

Files: `ssl/handlers.py` (docstrings), `ssl/tests/test_handlers.py`, DESIGN 9, `README.md`.

### What to write

`SSLObject.read()` returns `b''` for a clean close_notify on every supported version, and on Python 3.8 (3.8.20,
OpenSSL 3.0.13) also for a transport EOF without close_notify, where 3.10+ raises `SSLEOFError`. The handler cannot
tell the two apart on 3.8, so `Config(suppress_ragged_eofs=False)` behaves like `True` there: truncation is reported
as a clean EOF. No exception, no warning.

- `SslIoPipelineHandler` class docstring, the `suppress_ragged_eofs` comment in `Config`, DESIGN 9 (TLS paragraph)
  and the package README each get a short, prominent note to that effect, naming 3.8 and the mechanism.
- `test_ragged_eof_strict` is skipped below the version where the ssl module raises, with the note repeated in the
  skip reason. The exact boundary should be confirmed on 3.9 if an interpreter is available (`.venvs` has 3.8 and
  3.14 only); until then `sys.version_info < (3, 10)` is the documented assumption.
- The TLS half-close tests which rely on strict EOFs to prove close_notify ordering keep their meaning on 3.10+ and
  are documented as weaker on 3.8.

---

## Small optional cleanups from the notes

Not findings, but each is a few lines and worth doing while nearby.

- N1: docstrings on `Completable.get_result` / `get_exception` stating they are callable only from a listener;
  optionally raise a `StateIoPipelineError` with that message instead of the bare `AttributeError`.
- N9: `IoPipeline.destroy()` returns at once when the state is `DESTROYING` (reentrant destroy from a `Removed`
  notification), instead of failing a `check.state`.
- N10: `IoPipelineHandlerContext.feed_in` / `feed_out` check `_invalidated` first and raise
  `ContextInvalidatedIoPipelineError`, instead of the `AttributeError` from the deleted link.
- N12: the sync and fdio drivers, on finding the pipeline destroyed under them (a timer callback's policy), end with
  `close()` semantics (`CLOSED`, or `FAILED` with an `AbortedIoPipelineError`) rather than a bare `check.state`
  failure; the asyncio equivalent is part of the O1/O8 change.

---

## Test migration summary

Each moves to the `test_regressions.py` module next to it.

| Failing test today | Fix |
| --- | --- |
| `tests/test_findings.py::TestInjectedInputBeforeInitialInput` | O6 |
| `drivers/tests/test_findings.py::TestDrainingDuplexDeadlock` | O1 sync |
| `drivers/tests/test_findings.py::TestDrainingDuplexDeadlockAsyncio` | O1 asyncio |
| `drivers/tests/test_findings.py::TestAsyncioTimersDuringGracefulClose` | O8 |
| `multiplex/tests/test_findings.py::TestManualReadMessageAfterEnd` | O2 |
| `multiplex/tests/test_findings.py::TestStreamSpecFactoryFailure` | O5 |
| `multiplex/tests/test_findings.py::TestAdapterFailuresWhileEncoding` | O3 |
| `multiplex/tests/test_findings.py::TestReceiveCreditAfterLocalFinish` | O4 |
| `multiplex/tests/test_findings.py::TestOpenBeforeInitialInput` | O6 |

Once all nine have moved, the three `test_findings.py` modules are empty and should be deleted, and the "Run
everything but the deliberately failing demonstrations" instructions in FINDINGS.md go away with them.
