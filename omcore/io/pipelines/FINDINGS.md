# Pipeline review findings

## Review scope and status

Review date: 2026-10-09.

The primary change reviewed was `719299245174060732a1f148a420e2e33173ccbd`, "Add protocol-agnostic stream multiplexing
and output half-close support". Tests ran against working-tree HEAD `3907cb30271648047eef6e8e78a4bf80fcfb8574`.

The review covered the new multiplexing implementation, output half-close support, the affected drivers and TLS
handler, and surrounding `omcore.io.pipelines` code. HTTP coverage was limited to the changed pipeline behavior and
the affected tests. It was not a general review of the HTTP pipeline implementation.

**No implementation fixes were made.** The review added 41 integration test methods and supporting stress helpers.
The failing demonstrations were deliberately left failing, without `xfail` markers. No commits were made during the
review. Every repair direction below is a proposal, not an implemented or verified fix.

This document records **28 confirmed findings and one policy-dependent concern**. Findings group related test cases;
their count differs from both the number of test methods and pytest's number of failed subtests. It includes broader
pipeline defects encountered during the review, so inclusion does not by itself mean the reviewed commit introduced
the behavior. Disproved hypotheses are omitted.

### Evidence and terminology

- **Confirmed / unfixed:** reproduced by an integration test; implementation unchanged.
- **Policy-dependent / unfixed:** the behavior is reproduced, but the desired exception-isolation policy needs a
  decision.
- **P1:** prioritize because of data loss, false success, connection stalls, deadlock, or ineffective resource bounds.
- **P2:** correctness, lifecycle, compatibility, or cleanup work that also has a concrete reproducer.
- Tests use actual pipelines and drivers, real sockets/TCP and TLS where applicable, and simplified protocol adapters
  or application handlers. No mocks or monkeypatches were added.
- Pure-driver tests exercise the production `PureIoPipelineDriver`, often with actual frame codecs and TLS MemoryBIO
  engines. They do not substitute for operating-system socket tests.
- Source links and line references describe the reviewed snapshot. Test names are the more durable reproduction
  references as the implementation changes.

## Findings index

| ID | Priority | Finding | Fix status |
| --- | --- | --- | --- |
| [MUX-01](#mux-01-batched-open-data-close-drops-accepted-input) | P1 | Batched open/data/close drops accepted input | Unfixed |
| [MUX-02](#mux-02-cooperative-child-producers-bypass-backpressure) | P1 | Deferred producers overrun child watermarks | Unfixed |
| [MUX-03](#mux-03-flow-controlled-typed-output-is-missing-from-watermarks) | P1 | Typed output bypasses byte accounting | Unfixed |
| [MUX-04](#mux-04-a-finished-child-can-strand-connection-receive-credit) | P1 | Finished children retain unusable receive credit | Unfixed |
| [MUX-05](#mux-05-the-control-output-limit-does-not-bound-an-already-queued-batch) | P1 | Paused control output exceeds its configured bound | Unfixed |
| [MUX-06](#mux-06-deferred-yields-do-not-interleave-due-timers) | P2 | Yield policy does not provide timer fairness | Unfixed |
| [MUX-07](#mux-07-a-read-token-issued-after-eof-can-leave-typed-input-stuck) | P2 | A read token after EOF does not restart input delivery | Unfixed |
| [MUX-08](#mux-08-peer-close-completes-final-output-before-earlier-fences) | P2 | Peer close reverses fence completion order | Unfixed |
| [MUX-09](#mux-09-removal-during-multi-frame-emission-uses-an-invalid-context) | P2 | Reentrant removal breaks multi-frame emission | Unfixed |
| [MUX-10](#mux-10-teardown-retains-stream-input-and-bookkeeping) | P2 | Teardown retains stream payloads and bookkeeping | Unfixed |
| [MUX-11](#mux-11-a-stream-factory-exception-fails-the-entire-connection) | Review | Factory exception isolation is inconsistent with construction failure | Policy-dependent; unfixed |
| [IO-01](#io-01-final-output-draining-can-deadlock-with-peer-output) | P1 | Final draining stops receiving and deadlocks | Unfixed |
| [IO-02](#io-02-asyncio-shutdown-completes-before-the-transport-half-closes) | P1 | Asyncio completes shutdown before native half-close | Unfixed |
| [IO-03](#io-03-duplicated-descriptors-restore-the-wrong-blocking-flags) | P2 | Duplicated descriptors restore incorrect flags | Unfixed |
| [IO-04](#io-04-synchronous-drivers-reject-valid-descriptors-numbered-1024) | P2 | Synchronous drivers fail on valid descriptors outside `select()` capacity | Unfixed |
| [IO-05](#io-05-driver-close-leaves-application-await-tasks-running) | P2 | Application coroutine survives driver close | Unfixed |
| [IO-06](#io-06-stream-reset-leaves-its-forwarded-await-task-running) | P2 | Application coroutine survives stream reset | Unfixed |
| [IO-07](#io-07-close-leaves-unprocessed-enqueue-waiters-pending) | P2 | Enqueue waiter survives close without completion | Unfixed |
| [IO-08](#io-08-cancelling-an-enqueue-waiter-fails-the-driver) | P2 | Cancelling a waiter causes `InvalidStateError` | Unfixed |
| [IO-09](#io-09-closed-drivers-retain-unprocessed-enqueued-input) | P2 | Closed drivers retain queued payloads | Unfixed |
| [TLS-01](#tls-01-certificate-failure-can-produce-successful-output-fences) | P1 | Certificate failure is followed by successful fences for discarded data | Unfixed |
| [TLS-02](#tls-02-handshake-timeout-can-report-successful-output-shutdown) | P1 | Handshake timeout produces false shutdown success | Unfixed |
| [TLS-03](#tls-03-handshake-completion-announces-writability-after-shutdown) | P2 | TLS resumes output after shutdown reached the terminal | Unfixed |
| [TLS-04](#tls-04-strict-eof-is-ineffective-with-the-tested-python-38-default-contexts) | P1 | Strict EOF accepts TLS truncation on the tested Python 3.8 runtime | Unfixed |
| [TLS-05](#tls-05-abort-retains-plaintext-waiting-for-the-handshake) | P2 | Aborted TLS handler retains queued plaintext | Unfixed |
| [CORE-01](#core-01-delimiter-framing-stalls-on-fragmented-manual-input) | P2 | Delimiter decoder does not rearm an incomplete manual read | Unfixed |
| [CORE-02](#core-02-one-removal-callback-exception-strands-the-rest-of-destruction) | P2 | A failed removal callback stops remaining destruction | Unfixed |
| [CORE-03](#core-03-destruction-retains-undrained-terminal-output) | P2 | Destroyed pipeline retains terminal output | Unfixed |
| [HTTP-01](#http-01-chunking-announces-writability-after-output-shutdown) | P2 | HTTP chunker resumes output after shutdown | Unfixed |

## Multiplexing

### MUX-01: Batched open-data-close drops accepted input

**Status:** Confirmed / unfixed. **Priority:** P1.

An adapter reports an accepted remote open, request data, and a graceful peer close within one inbound batch. The
factory accepts the stream, but the application receives neither `InitialInput` nor its request bytes. The same events
delivered separately start the application, deliver the data, and finish normally.

In [`MultiplexIoPipelineHandler._close`](multiplex/handlers.py#L581), the absence of a constructed child causes the
pending establishment to be discarded and the stream to close. Establishment was only deferred until the handler's
pump; the stream had already accepted input. This conflicts with the documented graceful peer-close behavior of
delivering queued input before `FinalInput`.

**Reproducer:** [TestMultiplexAdversarial.test_remote_open_data_close_in_one_batch_delivers_accepted_input](multiplex/tests/test_adversarial.py#L286).
The test compares separate delivery with `LBatch([LOpen, LData, LClose])`.

**Repair direction:** Preserve accepted remote establishment and queued input through a graceful close, then deliver
the end of input and finish the child. Keep this distinct from refusal or reset before acceptance.

### MUX-02: Cooperative child producers bypass backpressure

**Status:** Confirmed / unfixed. **Priority:** P1.

A cooperative producer writes 16 KiB, flushes, and defers its continuation. It stops on `PauseOutput`. With a child high
watermark of 64 KiB and zero peer credit, all 64 chunks are produced before the first pause: 1 MiB is queued despite the
producer cooperating with the flow protocol. The test allows a generous eight-chunk bound and observes 64.

[`MultiplexChild.collect_output`](multiplex/children.py#L525) runs child `Defer`s while draining terminal output.
[`_pump_child`](multiplex/handlers.py#L821) updates writability only after that collection returns. Each continuation
can therefore create another continuation before the producer learns that its queue is full. An unlimited producer
could monopolize the pump and grow memory indefinitely.

**Reproducer:** [TestMultiplexAdversarial.test_deferred_child_producer_is_paused_before_exhausting_output](multiplex/tests/test_adversarial.py#L157).
It reuses the cooperative producer already used by the top-level asyncio backpressure tests.

**Repair direction:** Check and announce child queue pressure during collection, before running further production,
and bound work between deferred continuations. Preserve ordering and account for reentrant pause handlers.

### MUX-03: Flow-controlled typed output is missing from watermarks

**Status:** Confirmed / unfixed. **Priority:** P1.

A typed extended-data message has a nonzero adapter-reported flow-control cost. It waits for send credit, but its
payload does not count toward child output watermarks. In the reproducer, 128 bytes wait behind zero credit with a
16-byte high watermark, and the producer receives no `PauseOutput`.

[`MultiplexStream.push_out_message`](multiplex/streams.py#L269) queues the typed item without updating `out_bytes`.
Child writability uses that byte count. This makes byte output bounded by cooperative backpressure while equivalent
flow-controlled typed payloads can accumulate without it, including SSH-like extended data.

**Reproducer:** [TestMultiplexAdversarial.test_flow_controlled_typed_output_applies_backpressure](multiplex/tests/test_adversarial.py#L261).
The expected pause is missing before credit is granted; the test also specifies the expected resume after delivery.

**Repair direction:** Define and maintain a queued size for flow-controlled typed payloads, including replacement or
splitting of their queue heads, and include that size in child watermarks.

### MUX-04: A finished child can strand connection receive credit

**Status:** Confirmed / unfixed. **Priority:** P1.

With connection credit replenished on consumption, a manual-read child can hold the entire connection window in
unread input. If it then finishes its own output and the adapter waits for peer close, the destroyed child leaves that
input and credit attached to the stream. It can never consume the input, but other streams remain blocked until the
peer completes the stream-close handshake.

The reproducer uses an eight-byte connection window, queues eight bytes on one stream, and finishes that child.
`FinalOutput` succeeds, yet no connection grant is emitted and `in_bytes` remains eight. A second stream exists on the
same connection. [`MultiplexChild.finish`](multiplex/children.py#L644) destroys the child, while
[`_release_done`](multiplex/handlers.py#L891) waits for a terminal stream before removing it and its credit.

**Reproducer:** [TestMultiplexAdversarial.test_finished_child_releases_unread_connection_credit](multiplex/tests/test_adversarial.py#L337).

**Repair direction:** Discard input that a finished child can no longer consume and return the associated connection
credit promptly. The protocol may still need to retain stream identity while awaiting peer close.

### MUX-05: The control-output limit does not bound an already queued batch

**Status:** Confirmed / unfixed. **Priority:** P1.

With the parent paused, `max_control_during_pause=3`, and remote streams disallowed, a batch of 100 opens produces 100
refusal frames plus a connection-error frame. The connection is marked failed when the configured bound is crossed,
but its queued control frames continue to be emitted.

[`_emit`](multiplex/handlers.py#L954) calls `_fail()` inside its control-output loop without stopping or discarding
remaining ordinary control output. Marking failure therefore does not enforce the advertised resource bound for this
batch.

**Reproducer:** [TestMultiplexAdversarial.test_control_output_limit_bounds_one_decoded_batch](multiplex/tests/test_adversarial.py#L213).
The test permits the first over-limit refusal, but observes all 100 instead.

**Repair direction:** Stop ordinary control emission after the limit fails the connection, while explicitly handling
whatever bounded terminal protocol output is needed. Also consider when the control queue itself is bounded.

### MUX-06: Deferred yields do not interleave due timers

**Status:** Confirmed / unfixed. **Priority:** P2. **Affected drivers:** pure, SocketSync, FdSync, fdio, asyncio.

The documented [yield policy](yielding.py#L16) says deferring permits the driver to interleave reads, writes, and timers.
The integration test sets a 16-byte turn budget and a one-unit counting yield policy, then sends 4,096 bytes as 256
units. An outer handler schedules a zero-delay timer on the first unit. On every driver, the timer observes that all
256 units have already been emitted.

The multiplexer does create deferred boundaries. The driver output-processing loops keep executing those deferred
continuations before returning to due-timer processing. The test establishes timer starvation across these boundaries;
it does not measure every kind of read or write scheduling fairness.

**Reproducer:** [TestMultiplexYielding.test_counting_yields_interleave_a_due_parent_timer](multiplex/tests/test_adversarial.py#L105).
Four cases use real sockets, and one uses the production pure driver.

**Repair direction:** Give a deferred fairness boundary actual scheduling meaning in the drivers, including a chance
to service due timers. Preserve backpressure processing between multiplex turns.

### MUX-07: A read token issued after EOF can leave typed input stuck

**Status:** Confirmed / unfixed. **Priority:** P2.

A manual-read stream receives its EOF and a queued typed message marked `AfterFinalInput`. Its application schedules a
timer that later emits `ReadyForInput`. The timer runs and the token reaches the child terminal, but the typed message
is not delivered without another event causing a pump.

[`MultiplexChild.wants_input`](multiplex/children.py#L377) excludes a child after final input has been delivered.
[`_pump_child`](multiplex/handlers.py#L821) does not otherwise count the newly collected read token as progress. It can
stop immediately after collecting the token even though permitted typed input remains queued.

**Reproducer:** [TestMultiplexAdversarial.test_timer_read_token_delivers_typed_message_after_eof](multiplex/tests/test_adversarial.py#L177).

**Repair direction:** Include actionable read-token changes in pump progress, including delivery of messages permitted
after `FinalInput`. Do not make another unrelated event necessary to use the token.

### MUX-08: Peer close completes final output before earlier fences

**Status:** Confirmed / unfixed. **Priority:** P2.

The application sends data, a flush, and output shutdown. Their parent transport drain is deliberately held. When a
graceful peer close causes the application to finish, completion listeners run in this order:

```text
observed: final, flush, shutdown
expected: flush, shutdown, final
```

The earlier fences may correctly fail because the peer closed; the failure is that the later final fence completes
first. [`_drain_remote_closed`](multiplex/handlers.py#L855) completes the final fence and then destroys the child. That
destruction fails earlier fences still awaiting a parent flush.

**Reproducer:** [TestMultiplexAdversarial.test_peer_close_completes_earlier_fences_before_final_output](multiplex/tests/test_adversarial.py#L242).

**Repair direction:** Resolve earlier outstanding fences in their original order before completing final output,
including fences already emitted into the parent but not yet transport-complete.

### MUX-09: Removal during multi-frame emission uses an invalid context

**Status:** Confirmed / unfixed. **Priority:** P2.

An adapter encodes one data unit as two outbound frames. An outer handler removes the multiplexer when it sees the
first frame. Emission then attempts to feed the second frame through the invalidated context and raises, failing the
parent rather than stopping emission cleanly.

The outer emitter checks removal at several boundaries, but the per-frame loop in
[`_emit_unit`](multiplex/handlers.py#L1049) does not recheck after every outbound call. Those calls can reenter the
pipeline and remove the handler.

**Reproducer:** [TestMultiplexAdversarial.test_removal_during_multi_frame_encoding_stops_emission](multiplex/tests/test_adversarial.py#L226).
The adapter and removal handler are ordinary simplified implementations, not patches.

**Repair direction:** Stop after any encoded frame invalidates the handler. Audit other loops over adapter-produced
frame sequences for the same requirement; only the two-frame data case is reproduced here.

### MUX-10: Teardown retains stream input and bookkeeping

**Status:** Confirmed / unfixed. **Priority:** P2.

Removing the multiplexer, or destroying its parent, does not release unread stream input while a caller retains the
multiplexer object. A weakly referenced queued payload remains alive with cyclic collection disabled. The teardown
path also leaves the stream table and credit entries populated.

[`_teardown`](multiplex/handlers.py#L679) aborts children and clears several handler queues, but does not remove the
streams and their credit/scheduler entries or clear their unread input. Retaining a closed handler for inspection can
therefore retain application payloads that can never be processed.

**Reproducer:** [TestMultiplexAdversarial.test_teardown_releases_queued_input_while_handler_is_retained](multiplex/tests/test_adversarial.py#L308).
Both handler removal and parent destruction reproduce the payload-retention failure. The test additionally specifies
empty stream and credit bookkeeping after teardown.

**Repair direction:** Release stream input and all owned stream bookkeeping during abortive teardown, independently
of whether the multiplexer object itself remains referenced.

### MUX-11: A stream factory exception fails the entire connection

**Status:** Policy-dependent / unfixed. **Priority:** Review.

After one healthy stream is established, the stream specification factory raises `ValueError` for another open. The
handler emits a connection error and aborts the healthy stream. It does not refuse just the new stream.

The factory call in [`_open_remote`](multiplex/handlers.py#L498) is outside the per-child construction-failure handling.
Its exception reaches the adapter-inbound exception path, which fails the connection. By comparison, failure to build
a remote child from a returned specification is handled as a refusal of that stream.

**Reproducer:** [TestMultiplexAdversarial.test_factory_exception_isolated_to_the_refused_stream](multiplex/tests/test_adversarial.py#L194).
The test asks for refusal of the bad stream and continued use of the good stream. It currently fails on the emitted
connection error.

**Decision needed:** Determine whether arbitrary factory exceptions intentionally make the connection unusable, or
should be isolated like child-construction failures. The observed behavior is certain; the proposed isolation
expectation is the policy-dependent part. No implementation policy was changed.

## Drivers and asynchronous work

### IO-01: Final-output draining can deadlock with peer output

**Status:** Confirmed / unfixed. **Priority:** P1.

An application writes 1 MiB and sends `FinalOutput` without requesting further input. The raw peer first sends its own
1 MiB and then reads the application response. Small socket send buffers force both directions to make progress.
SocketSync, FdSync, and asyncio time out: the driver no longer consumes the unwanted peer input, so the peer cannot
finish sending and begin receiving the output that the driver is trying to drain.

The synchronous driver's [readiness selection](drivers/sync.py#L627) still gates reading on the application read token
while draining. Asyncio's [`_handle_output_final_output`](drivers/asyncio.py#L917) cancels its reader before waiting for
the writer to close; a full `StreamReader` buffer can then keep the transport paused.

The equivalent fdio test passes because fdio discards transport input while draining. The design document already
describes that behavior for pure and fdio. This finding is a concrete graceful-drain gap in the other drivers.

**Reproducers in [test_finaldrain.py](drivers/tests/test_finaldrain.py):**

- `TestSyncFinalDrain.test_socket_final_drain_keeps_receiving`
- `TestSyncFinalDrain.test_fd_final_drain_keeps_receiving`
- `TestAsyncioFinalDrain.test_final_drain_keeps_receiving`
- Passing control: `TestFdioFinalDrain.test_final_drain_keeps_receiving`

**Repair direction:** Continue receiving and discarding transport input during final drain when no application input
consumer remains, as fdio does. Keep that distinct from delivering additional input into a finished application.

### IO-02: Asyncio shutdown completes before the transport half-closes

**Status:** Confirmed / unfixed. **Priority:** P1.

The application writes 1 MiB and sends `ShutdownOutput`. The configured high watermark is 2 MiB, so `drain()` can return
without emptying the asyncio transport buffer. The shutdown completable succeeds while
`writer.transport.get_write_buffer_size()` still reports **1,040,512 bytes**.

[`_handle_output_shutdown_output`](drivers/asyncio.py#L963) calls `write_eof()` and uses drain completion for the fence.
Asyncio defers the native socket shutdown until its buffered bytes are written, while `drain()` is a watermark-based
flow-control operation. Successful drain does not establish that the deferred native half-close happened. This
violates the documented shutdown success boundary, which includes the transport's output half being shut down.

**Reproducer:** [TestAsyncioFinalDrain.test_shutdown_completion_waits_for_transport_half_close](drivers/tests/test_finaldrain.py#L106).
It uses a real socket transport and its public buffer-size observation.

**Repair direction:** Complete shutdown only at an actual transport half-close boundary. Do not equate an ordinary
successful `drain()` with completion of a deferred `write_eof()`.

### IO-03: Duplicated descriptors restore the wrong blocking flags

**Status:** Confirmed / unfixed. **Priority:** P2.

Two different descriptor numbers can refer to the same open file description. Preparing the first descriptor changes
the flags seen through the second. [`FdSyncIoPipelineDriver._prepare_transport`](drivers/sync.py#L857) saves each
descriptor's flags immediately before modifying it, so the second saved value may already include `O_NONBLOCK`.
Restoration then writes that modified value back, leaving a caller's originally blocking transport nonblocking.

This occurs after both abortive and graceful close with duplicated socket descriptors. A duplicated PTY slave also
reproduces incorrect restoration after the permitted write-descriptor-close half-close path. The read descriptor
correctly remains nonblocking while active, but is not restored correctly when the driver finishes.

**Reproducers in [TestFdOwnership](drivers/tests/test_fd_ownership.py):**

- `test_duplicate_socket_descriptors_restore_original_flags`
- `test_terminal_read_descriptor_restores_flags_after_write_half_close`

**Repair direction:** Snapshot all original flags before changing any descriptor. Preserve the original snapshot for
the surviving read descriptor when half-close closes a shared write descriptor. This relies on POSIX shared-description
semantics and is directly relevant to Darwin, although Darwin execution remains outstanding.

### IO-04: Synchronous drivers reject valid descriptors numbered 1024

**Status:** Confirmed / unfixed. **Priority:** P2.

The process descriptor limit permits a socket descriptor numbered 1024, but both synchronous drivers fail with
`ValueError: filedescriptor out of range in select()`. The same request/response and half-close operation succeeds with
a normal descriptor number. The reproducer obtains the descriptor with `F_DUPFD`, rather than opening thousands of
unrelated resources or replacing an existing descriptor.

The shared [`_wait_for_io_or_timer`](drivers/sync.py#L478) uses `select.select()`. Its descriptor-number limit is lower
than the process's valid descriptor range in the tested environment. This can fail in a process with many unrelated
open descriptors even if the driver itself handles only one connection.

**Reproducer:** [TestFdOwnership.test_valid_high_numbered_descriptors_transfer_and_half_close](drivers/tests/test_fd_ownership.py#L24).
It checks both driver types and both descriptor ranges. It skips if the process limit cannot allocate descriptor 1024.

**Repair direction:** Use a readiness mechanism capable of handling the supported descriptor range, with a portable
backend appropriate for Linux and Darwin. The observed boundary of 1024 describes this environment.

### IO-05: Driver close leaves application Await tasks running

**Status:** Confirmed / unfixed. **Priority:** P2.

An application sends `Await` with a coroutine that waits on an event. After the driver has started that coroutine,
closing the driver fails the `Await` message but leaves the underlying task running.

[`_handle_output_await`](drivers/asyncio.py#L843) creates or obtains the future and tracks it in `_pending_awaits`.
[`close`](drivers/asyncio.py#L1224) cancels driver read/drain and scheduling tasks, but does not cancel and settle these
application await tasks. The test specifically supplies a coroutine, so its running task was created by the driver;
it does not depend on ownership assumptions about an externally supplied task.

**Reproducer:** [TestAsyncioLifecycle.test_close_cancels_a_coroutine_started_by_await](drivers/tests/test_asyncio_lifecycle.py#L124).
The test explicitly cancels the leaked task in cleanup.

**Repair direction:** Give driver-created await tasks a close/cancellation lifecycle, settle them, and release their
callbacks and bookkeeping. Specify ownership separately for awaitables supplied as existing tasks or futures.

### IO-06: Stream reset leaves its forwarded Await task running

**Status:** Confirmed / unfixed. **Priority:** P2.

A multiplex child starts a coroutine through `Await`. Resetting that stream fails the child's await message and removes
the stream, while the parent connection remains usable. The coroutine still runs in the parent asyncio driver.

The multiplexer [forwards child awaits as parent awaits](multiplex/handlers.py#L954), relaying their completion back
through weak references. Child teardown does not propagate cancellation of the running parent-side work. Weak
completion references prevent some ownership cycles but do not stop a live task.

**Reproducer:** [TestAsyncioLifecycle.test_reset_cancels_a_coroutine_started_by_child_await](drivers/tests/test_asyncio_lifecycle.py#L141).
It confirms the child message failed, the stream disappeared, and the parent remained ready before checking that the
task should have stopped. Cleanup cancels the leaked task explicitly.

**Repair direction:** Tie forwarded work to the child's lifetime and propagate cancellation without closing the parent
or affecting other streams. Fixing driver close alone does not address a reset on a continuing connection.

### IO-07: Close leaves unprocessed enqueue waiters pending

**Status:** Confirmed / unfixed. **Priority:** P2.

Calling `enqueue_waitable()` and closing before its command is processed leaves the returned future pending forever.
The driver is closed and has no opportunity to fulfill the command, but the caller receives neither success, failure,
nor cancellation.

The command and its future remain in the asyncio driver's command queue. The [close path](drivers/asyncio.py#L1224)
does not settle unprocessed feed-command futures.

**Reproducer:** [TestAsyncioLifecycle.test_close_finishes_unprocessed_enqueue_waitable](drivers/tests/test_asyncio_lifecycle.py#L102).

**Repair direction:** Fail or cancel outstanding enqueue waiters as part of closing the queue, with a defined result
for work that was never processed. The test accepts cancellation or an exceptional completion.

### IO-08: Cancelling an enqueue waiter fails the driver

**Status:** Confirmed / unfixed. **Priority:** P2.

Cancelling the future returned by `enqueue_waitable()` before its command runs makes the next driver step raise
`asyncio.InvalidStateError` and fail the driver. A caller timeout or cancellation of its wait can therefore break an
otherwise usable transport.

[`_handle_command_feed_in`](drivers/asyncio.py#L321) calls `set_result()` or `set_exception()` without checking whether
the future is already cancelled or complete.

**Reproducer:** [TestAsyncioLifecycle.test_cancelled_enqueue_waiter_does_not_fail_driver](drivers/tests/test_asyncio_lifecycle.py#L114).

**Repair direction:** Handle cancellation of the notification future without completing it again. Separately define
whether cancelling the waiter cancels queued work; neither policy requires failing the whole driver this way.

### IO-09: Closed drivers retain unprocessed enqueued input

**Status:** Confirmed / unfixed. **Priority:** P2. **Affected drivers:** SocketSync, FdSync, fdio, asyncio.

Enqueue a weakly referenced payload before initialization, remove the caller's reference, and close the driver. The
payload remains alive in each affected driver's unprocessed input or command queue. The pure driver passes the same
check.

The relevant close paths discard transport output or close the transport but do not clear the queued application
input. Holding a closed driver therefore holds messages that cannot be processed, even if no pipeline was ever built.
This is separate from pending-waiter completion in IO-07: this test uses ordinary `enqueue()` with no waiter.

**Reproducer:** [TestAsyncioLifecycle.test_close_releases_unprocessed_input](drivers/tests/test_asyncio_lifecycle.py#L56).
Its single integration test exercises all five drivers, using real sockets for the four transport-backed cases.

**Repair direction:** Clear unprocessed input during close and failure, settling any associated waiters before dropping
their commands. Include the close-before-initialization path.

## TLS

### TLS-01: Certificate failure can produce successful output fences

**Status:** Confirmed / unfixed. **Priority:** P1.

A real TLS server presents the temporary self-signed test certificate. A client using its default trust store queues
plaintext, `FlushOutput`, and `ShutdownOutput` before the handshake. Certificate verification fails and the application
receives `SSLCertVerificationError`. When application error policy subsequently sends `FinalOutput`, both earlier
output fences report success despite the plaintext never being delivered and TLS never establishing.

[`_turn`](ssl/handlers.py#L579) clears plaintext and marks the TLS state closed on `SSLError`, but does not fail the
retained output fences. A later [`_emit`](ssl/handlers.py#L914) treats the now-empty write queue and closed state as
reasons to forward those fences normally. Transport success then becomes a false report about the discarded TLS data.

**Reproducer:** [TestTlsAdversarial.test_failed_certificate_verification_fails_undelivered_output_fences](ssl/tests/test_adversarial.py#L31).
Separate subtests demonstrate false success for flush and shutdown.

**Repair direction:** Preserve the distinction between successfully drained output and output discarded after TLS
failure. Resolve affected retained fences as failures while still performing whatever transport cleanup is necessary.

### TLS-02: Handshake timeout can report successful output shutdown

**Status:** Confirmed / unfixed. **Priority:** P1.

With no responding TLS peer, the client queues plaintext, flush, shutdown, and final output. Only ClientHello crosses
the simulated transport. Advancing the driver's clock to the one-second handshake deadline discards the plaintext.
The flush fails, but `ShutdownOutput` succeeds.

[`_on_state_timeout`](ssl/handlers.py#L349) clears the plaintext queue and forwards a retained shutdown through the
ordinary transport path before final output. The transport can half-close successfully, but the shutdown fence also
promises that earlier accepted output crossed its transport boundary; those bytes were discarded.

**Reproducer:** [TestTlsAdversarial.test_handshake_timeout_does_not_report_undelivered_output_as_shutdown_success](ssl/tests/test_adversarial.py#L80).
The production pure-driver clock makes the deadline deterministic without replacing the scheduler.

**Repair direction:** Fail fences whose preceding plaintext was discarded by the timeout. Preserve fence ordering and
must-propagate handling without converting abortive TLS cleanup into successful delivery.

### TLS-03: Handshake completion announces writability after shutdown

**Status:** Confirmed / unfixed. **Priority:** P2.

Queue five plaintext bytes and shutdown before the handshake, with TLS watermarks of four and two bytes. The handler
pauses the application while plaintext waits. A real handshake then permits the bytes and shutdown to progress, after
which the handler emits `ReadyForOutput` even though `pipeline.saw_shutdown_output` is already true.

The last phase of [`_emit`](ssl/handlers.py#L914) derives writability from remaining plaintext and downstream writability
without suppressing a resume after shutdown. Earlier phases of the same emission can already have forwarded shutdown.
An application responding to this resume can attempt ordinary output that the pipeline must now reject.

**Reproducer:** [TestTlsAdversarial.test_handshake_does_not_resume_output_after_retained_shutdown](ssl/tests/test_adversarial.py#L60).

**Repair direction:** Suppress output-resume announcements once the output shutdown boundary has been reached, while
allowing the input half and its required control work to continue.

### TLS-04: Strict EOF is ineffective with the tested Python 3.8 default contexts

**Status:** Confirmed on the tested Python 3.8 runtime / unfixed. **Priority:** P1.

After a successful handshake and a partial response, the server aborts without sending TLS `close_notify`. The client
handler is configured with `suppress_ragged_eofs=False`. On the tested Python 3.8 runtime, no `SSLError` reaches the
application and the connection is exposed as clean EOF. The new integration test passes on the tested 3.14 runtimes.

The available Python 3.8 default SSL contexts have `OP_IGNORE_UNEXPECTED_EOF` enabled. That causes the SSL engine to
suppress the truncation before the handler's strict-EOF policy can enforce it. Both the ordinary 3.14 and 3.8 runtimes
reported OpenSSL 3.0.13, so checking the OpenSSL version alone does not distinguish these configurations.

**Reproducer:** [TestTlsAdversarial.test_strict_eof_detects_truncation_with_default_ssl_contexts](ssl/tests/test_adversarial.py#L102).
The pre-existing `TestSslHandlers.test_ragged_eof_strict` in [test_handlers.py](ssl/tests/test_handlers.py) also fails on
this Python 3.8 environment. It was the only existing I/O test failure in the combined Python 3.8 run.

**Repair direction:** Make the strict-EOF contract consistent with the SSL context's effective options, accounting for
context ownership or sharing. Do not assume this option has the same default across Python or SSL builds.

**Portability limit:** This establishes a runtime/context-specific compatibility failure, not that every Python 3.8
installation behaves identically. Darwin and its available SSL configurations were not executed.

### TLS-05: Abort retains plaintext waiting for the handshake

**Status:** Confirmed / unfixed. **Priority:** P2.

Queue 700,000 plaintext bytes before a handshake can complete and abort the driver. A retained TLS handler still
reports 700,000 outbound buffered bytes afterward. The data cannot be delivered after removal, but remains owned by
the closed handler.

The handler's [`Removed` notification](ssl/handlers.py#L304) cancels timers without releasing the queued plaintext.
This differs from a TLS engine error path that explicitly clears its write queue.

**Reproducer:** [TestTlsAdversarial.test_abort_releases_plaintext_waiting_for_handshake](ssl/tests/test_adversarial.py#L123).

**Repair direction:** Clear owned buffers and retained lifecycle state on removal, consistently with abortive teardown.
The test directly demonstrates outbound plaintext retention; other owned TLS state should be audited during repair.

## Core pipeline behavior

### CORE-01: Delimiter framing stalls on fragmented manual input

**Status:** Confirmed / unfixed. **Priority:** P2. **History:** Pre-existing flow-control gap, also noted by the class TODO.

With manual reads, an application requests a newline-delimited frame. The first transport delivery contains `hel`,
which the decoder buffers without producing a frame. It does not request more transport input. A subsequent `lo\n`
therefore stays unread, and the application never receives `hello` or gets an opportunity to request its next frame.

[`DelimiterFrameDecoderIoPipelineHandler`](bytes/decoders.py#L118) buffers and decodes bytes without translating an
outstanding application read into further transport reads when a partial frame produces no output.

**Reproducer:** [TestPipelineAdversarial.test_delimiter_decoder_rearms_manual_read_for_incomplete_frame](tests/test_adversarial.py#L69).

**Repair direction:** Implement the decoder's manual-input flow contract, or route this framing through the existing
bytes-to-message decoder machinery that provides it. Preserve framing and maximum-buffer limits while rearming reads.

### CORE-02: One removal callback exception strands the rest of destruction

**Status:** Confirmed / unfixed. **Priority:** P2.

A pipeline contains two handlers. The first handler removed during destruction raises from its `Removed` callback.
The exception propagates, but the remaining handler never receives removal, and the pipeline is still marked
`DESTROYED`. Calling `destroy()` again cannot complete the skipped cleanup.

[`IoPipeline.destroy`](core.py#L2010) removes handlers in one loop without isolating individual removal failures.
Its finalization sets the destroyed state even when the loop exits early. Propagating the exception is compatible with
the test; abandoning cleanup of the other handlers is what fails.

**Reproducer:** [TestPipelineAdversarial.test_destroy_finishes_cleanup_when_one_removed_callback_raises](tests/test_adversarial.py#L56).
The raising handler is an ordinary integration-test implementation.

**Repair direction:** Attempt remaining handler and service cleanup even after a callback fails, preserving the
appropriate exception to report afterward. Do not leave irrecoverable partial teardown hidden behind `DESTROYED`.

### CORE-03: Destruction retains undrained terminal output

**Status:** Confirmed / unfixed. **Priority:** P2.

A payload reaches the pipeline's terminal output queue but has not been consumed by a driver or caller. Destroying the
pipeline removes handlers and fails pending completables, but the payload remains in `pipeline.output` while the
pipeline object is retained. A weak-reference assertion fails even with cyclic collection disabled.

The [destruction path](core.py#L2010) does not clear the terminal output queue. Immediate abort does not promise output
delivery, but it should release output that can no longer be used by the destroyed pipeline.

**Reproducer:** [TestPipelineAdversarial.test_destroy_releases_undrained_output](tests/test_adversarial.py#L85).

**Repair direction:** Release terminal output during destruction while preserving the failure semantics of any queued
completables. Do not rely on callers discarding the whole pipeline object to release its payloads.

## Changed HTTP pipeline behavior

### HTTP-01: Chunking announces writability after output shutdown

**Status:** Confirmed / unfixed. **Priority:** P2.

A chunked response buffers five body bytes with a four-byte high watermark, pausing its producer. `ShutdownOutput`
arrives before the response message ends. The chunker emits the abort representation and forwards shutdown, then emits
`ReadyForOutput` even though ordinary output is no longer legal.

The changed shutdown branch in [`chunking.py`](../../http/pipelines/chunking.py#L136) resets the buffered byte count.
The surrounding `outbound()` finally block calls `_update_writability()`, which treats the empty buffer as a reason to
resume without checking output shutdown. The finding concerns that resume signal, not the intended mid-message abort
representation.

**Reproducer:** [TestShutdownWritability.test_chunker_does_not_resume_output_after_shutdown](../../http/pipelines/tests/test_shutdown_writability.py#L21).
It uses a complete pipeline with the response chunker, writability observer, flow service, and feedback handler.

**Repair direction:** Suppress resumed output writability after the shutdown boundary, including the update performed
while unwinding the outbound call.

## Verification record

### Runtime and suite results

The review ran in Linux dockerdev. Python was always invoked through the repository's `./python` launcher. Relevant
tests were run with pytest on the default environment. The Python 3.8 environment did not have pytest, so its unittest
tests were also run through the repository launcher. The free-threaded environment was verified to have the GIL disabled.

| Run | Result |
| --- | --- |
| Initial relevant existing tests, Python 3.14.8 | 482 passed across the initial runs |
| Final relevant pytest selection, Python 3.14.8 | 523 collected methods; 499 passed and 42 failing test/subtest reports |
| Added tests, Python 3.8.20 | 41 methods; 36 failure reports and 7 error reports |
| Added tests, free-threaded Python 3.14.8 | 41 methods; 35 failure reports and 7 error reports |
| Combined I/O unittest discovery, Python 3.8.20 | 479 methods; 36 failure reports and 7 error reports |
| Combined I/O unittest discovery, free-threaded Python 3.14.8 | 479 methods; 34 failure reports and 7 error reports |
| `make fix check` | Passed |

The default pytest failures all come from the added tests: 42 reports cover 31 distinct failing methods. Parent test
results and failed subtests are reported separately, so the displayed pass/fail sum is not the collected-method count.
Unittest likewise reports individual failing subtests, and reports raised exceptions such as the demonstrated timeout
or `InvalidStateError` under "errors".

The extra Python 3.8 failure among the added tests is TLS-04. Combined I/O discovery excludes the added HTTP test and
includes the existing strict-EOF test, which also fails on Python 3.8. There were no newly failing existing tests on
the default or free-threaded 3.14 runtimes. No import or syntax failure was being counted as a demonstrated defect.

### Stress campaigns

The session generator varies stream count, request/response sizes, frame sizes, stream and connection windows,
connection-credit replenishment policy, padding, manual/automatic input, child read batches, turn budgets, yield
counts, driver chunks, watermarks, and link capacity. SSH-like typed extended data and H2-like connection credit are
included. Plain and TLS sessions use actual framing and check delivered bytes, lifecycle results, errors, and stream
release.

| Campaign | Runtime | Completed sessions | Additional failures |
| --- | --- | ---: | ---: |
| 45-minute randomized run, seeds 6 through 5120 | 3.14 | 20,460 | 0 |
| 45-minute randomized run, seeds 10006 through 13201 | 3.8 | 12,784 | 0 |
| 45-minute randomized run, seeds 20006 through 24101 | Free-threaded 3.14 | 16,384 | 0 |
| Shuffled endpoint/transfer order, seeds 70000 through 70499 | 3.14 | 2,000 | 0 |
| Shuffled endpoint/transfer order, seeds 80000 through 80499 | 3.8 | 2,000 | 0 |
| Additional session-runner campaign, seeds 60000 through 60099 | 3.14 | 400 | 0 |
| Long-lived connection reset/churn, seeds 200 through 299 | 3.14 | 200 | 0 |
| Long-lived connection reset/churn, seeds 400 through 499 | Free-threaded 3.14 | 200 | 0 |
| Repeated real socket/TCP suites | 3.14 | 240 | 0 |
| Repeated real socket/TCP suites | Free-threaded 3.14 | 240 | 0 |

Totals: **54,028 randomized sessions**, plus **400 long-lived connections with 32 reset/churn waves each**, plus
**480 real socket/TCP sessions**. The real transport sessions carried 12 streams with 150,000 request bytes and 400,000
response bytes each: approximately 3.168 GB of application data in total.

The churn tests reset a subset of active streams while preserving healthy streams on the same connection, then check
data, connection-credit conservation, empty stream tables, and continued connection usability. Final connection
shutdown is also checked. The real transport suites cover SocketSync, FdSync, fdio, and asyncio, with and without TLS.

The early long-running campaigns loaded the session helper before shuffled scheduling was added. The checked-in
helper now shuffles endpoint stepping and transfer order reproducibly. Seed ranges reproduce the generated session
parameters; the later shuffled campaigns and the current runner also reproduce that shuffled scheduling policy.

These passing campaigns exercise paths different from the targeted failures above. They establish substantial positive
coverage; they do not cancel out the adversarial failures or prove correctness for all interleavings.

### Coverage and additional positive tests

A final coverage run with branch measurement enabled reported **88% combined coverage** for production
`omcore.io.pipelines` code, excluding tests. This percentage is coverage.py's combined statement/branch result, not a
claim that 88% of branches alone were covered. Selected module results were:

| Module | Reported coverage |
| --- | ---: |
| `multiplex/handlers.py` | 88% |
| `multiplex/children.py` | 88% |
| `multiplex/credit.py` | 92% |
| `multiplex/streams.py` | 99% |
| `multiplex/schedulers.py` | 89% |
| `ssl/handlers.py` | 86% |

In addition to the failure demonstrations, added passing integration tests cover randomized framed sessions and churn,
sync socket multiplexing, and a composed byte-buffer/delimiter/Unicode/flat-map pipeline with one-byte transport
fragmentation, CRLF and LF delimiters, a split multibyte character, filtered messages, and final incomplete input.

### Darwin considerations

**Darwin was not executed.** Linux successes are not a Darwin certification. The added operating-system tests use
POSIX interfaces, sockets, PTYs, and a select-based fdio poller rather than requiring Linux-only polling facilities.

The most direct portability follow-ups are:

- IO-03: original descriptor flags must survive duplicated descriptors and terminal write-half closure. The shared
  open-file-description behavior must be handled correctly on Darwin as well.
- IO-04: descriptor-number capacity and available readiness backends must be considered independently of the process
  descriptor limit. The test skips if that limit cannot allocate the requested descriptor.
- TLS-04: inspect effective SSL context options across the Python/SSL builds used on Darwin; runtime defaults matter.
- IO-01, IO-02, and MUX-06: execute the real transport, asyncio, and fairness tests on Darwin's socket and event-loop
  implementation. The integration assertions concern behavior, rather than Linux-specific buffer-size constants.

## Reproduction commands

Run commands from the repository root. The failing demonstrations are intentional and should produce a nonzero exit
status until their implementations or, for MUX-11, the agreed policy and test expectation are resolved.

### Added failure demonstrations

```sh
./python -m pytest -q \
  omcore/io/pipelines/multiplex/tests/test_adversarial.py \
  omcore/io/pipelines/drivers/tests/test_finaldrain.py \
  omcore/io/pipelines/drivers/tests/test_asyncio_lifecycle.py \
  omcore/io/pipelines/drivers/tests/test_fd_ownership.py \
  omcore/io/pipelines/ssl/tests/test_adversarial.py \
  omcore/io/pipelines/tests/test_adversarial.py \
  omcore/http/pipelines/tests/test_shutdown_writability.py
```

For one finding, select the linked test by its class and method, for example:

```sh
./python -m pytest -q \
  omcore/io/pipelines/multiplex/tests/test_adversarial.py::TestMultiplexAdversarial::test_remote_open_data_close_in_one_batch_delivers_accepted_input

VENV=8 ./python -m unittest \
  omcore.io.pipelines.ssl.tests.test_adversarial.TestTlsAdversarial.test_strict_eof_detects_truncation_with_default_ssl_contexts
```

### Full relevant selection used for the final default-runtime result

```sh
./python -m pytest -q \
  omcore/io/pipelines \
  omcore/http/pipelines/tests/test_chunking.py \
  omcore/http/pipelines/tests/test_shutdown_writability.py \
  omcore/http/pipelines/clients/tests/test_compressors.py \
  omcore/http/pipelines/servers/tests/test_asgi.py \
  omcore/http/pipelines/servers/tests/test_backpressure_integration.py

VENV=8 ./python -m unittest discover -s omcore/io/pipelines -t . -q
VENV=14t ./python -m unittest discover -s omcore/io/pipelines -t . -q
```

The final default-runtime run was additionally wrapped in `coverage run --branch --source=omcore.io.pipelines`;
`coverage report --omit='*/tests/*'` produced the production coverage figures above.

### Reproducible stress and positive integration tests

The repository runner is [multiplex/tests/stress.py](multiplex/tests/stress.py), with implementation in
[multiplex/tests/randomized.py](multiplex/tests/randomized.py). It prints the seed, protocol, and TLS setting on failure.
A normal seed covers SSH-like and H2-like sessions both plain and under TLS. A churn seed covers H2-like connections
plain and under TLS.

```sh
./python -m omcore.io.pipelines.multiplex.tests.stress --start 70000 --count 500
VENV=8 ./python -m omcore.io.pipelines.multiplex.tests.stress --start 80000 --count 500

./python -m omcore.io.pipelines.multiplex.tests.stress --churn --start 200 --count 100 --waves 32
VENV=14t ./python -m omcore.io.pipelines.multiplex.tests.stress --churn --start 400 --count 100 --waves 32

./python -m pytest -q \
  omcore/io/pipelines/multiplex/tests/test_randomized.py \
  omcore/io/pipelines/multiplex/tests/test_sync_sockets.py \
  omcore/io/pipelines/multiplex/tests/test_sockets.py \
  omcore/io/pipelines/handlers/tests/test_integration.py
```

## Repair tracking

All 29 entries remain open at the end of this review. Each confirmed finding has a failing integration demonstration,
including a runtime-specific one for TLS-04. MUX-11 has a failing demonstration of the proposed isolation behavior and
requires a policy decision. None of the proposed repair directions has been applied or validated.

When resolving a finding, record its implementation change and the result of its linked reproducer here. Keep the
positive transport and stress checks relevant to that change, and include Darwin execution when available.
