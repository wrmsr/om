# I/O Pipeline Design

This document records the architectural contracts of `omcore.io.pipelines`. It is durable design context for
contributors and for protocol implementations built on the pipeline; it is not a substitute for the API docstrings or
tests. The introductory model and basic examples live in [README.md](README.md).

The implementation is inspired by Netty, but it is deliberately smaller, synchronous at its core, bytes-agnostic, and
independent of any particular I/O runtime. HTTP is its largest consumer, not its definition.

---

## 1. Goals and non-goals

The pipeline exists to compose incremental, bidirectional transforms while leaving transport ownership and waiting to
an external driver.

Its primary goals are:

- Pure Python 3.8+ with no required third-party dependencies.
- Arbitrary messages, including but not limited to bytes and HTTP objects.
- The same synchronous handlers under sync, asyncio, fdio, generator-style, or application-specific drivers.
- Explicit lifecycle, ordering, backpressure, completion, and timeout semantics.
- Small handlers which can be assembled and tested without real I/O.
- Predictable teardown and bounded ownership, especially at this low level of the stack.

It is not intended to provide:

- A universal `Channel` or `Driver` base class.
- A hidden worker thread, event loop, or idle heartbeat.
- Per-byte delivery acknowledgement or peer acknowledgement.
- Automatic hard memory bounds merely because flow control is enabled.
- HTTP policy in the generic I/O layer.

A useful pipeline may be driven like a sophisticated generator. The socket drivers are important implementations of
the boundary contract, not a required inheritance hierarchy.

---

## 2. Structural model and ordering

An `IoPipeline` is an ordered chain of handler contexts. Specifications and handler lookup APIs list handlers from the
transport-facing, outermost side to the application-facing, innermost side.

```text
transport / pipeline.output
          |
      outermost
          |
      handler 0
          |
      handler 1
          |
         ...
          |
      innermost
          |
      application
```

Inbound messages move outer to inner:

```text
pipeline.feed_in(msg) -> handler 0 -> handler 1 -> ... -> application
```

Outbound messages move inner to outer:

```text
application -> ... -> handler 1 -> handler 0 -> pipeline.output
```

`IoPipelineHandlerContext.feed_in()` and `feed_out()` continue from the current position; they do not restart traversal
at an endpoint. A handler can transform, split, combine, suppress, or reverse the direction of a message, subject to
the message's propagation rules.

Handlers are synchronous even when a driver is asynchronous. Calls may be reentrant: delivering an outbound message
can synchronously produce an inbound flow transition, and delivering inbound data can synchronously produce a
response. Simple handlers can rely on call ordering. Stateful pump-style handlers such as TLS must explicitly guard
their internal turn and emit in a stable protocol order.

`IoPipelineHandlerContext` represents one handler at one exact position. It is private to that handler invocation and
must not be cached or shared. `IoPipelineHandlerRef` is the public, stable identity for that position; it becomes
invalid when the handler is removed. Removing and re-adding the same handler creates a different ref.

Non-shareable handler instances occur at most once in a pipeline. `ShareableIoPipelineHandler` permits one instance at
multiple positions, but all position-specific state must then live in `ctx.storage` or outside the handler instance.

---

## 3. Execution boundaries and error routing

Every feed, notification, deferred callback, and scheduled callback runs inside a pipeline execution boundary. Nested
operations share the outer boundary. On leaving the outermost boundary, services receive their exit hook and the core
checks propagation obligations.

Drivers or integrations which invoke handler-owned callbacks directly must enter the pipeline:

```python
with pipeline.enter():
    callback()
```

Ordinary handler exceptions are converted into an inbound `IoPipelineMessages.Error` starting immediately inside the
failing handler. The error records the original direction and the failing handler ref. This lets an application-side
policy translate, report, or close without baking policy into every transform.

Exceptions are raised directly when:

- `IoPipeline.Config.raise_immediately` is enabled;
- the exception is `UnhandleableIoPipelineError` or another configured never-handle exception; or
- error handling itself fails.

An error handler must not recursively fail while handling an error. Transport and driver failures must fail the driver
and tear down the pipeline rather than leaving it partially usable.

---

## 4. Lifecycle and propagation

Lifecycle is represented by messages rather than specialized handler methods.

| Message | Direction | Meaning |
| --- | --- | --- |
| `InitialInput` | Inbound | Input has become active; exactly one may begin a pipeline input lifetime. |
| `FinalInput` | Inbound | The input side reached EOF. Output may remain open. |
| `ShutdownOutput` | Outbound | Gracefully end output while input continues: an output half-close. |
| `FinalOutput` | Outbound | Gracefully finish accepted output and terminate the driver. |
| `Error` | Inbound | A processing, protocol, timeout, or transport failure is being reported. |

`InitialInput`, `FinalInput`, `ShutdownOutput`, and `FinalOutput` are `MustPropagate`. The exact message instance must
reach its terminal position. A handler may retain one temporarily, but silently replacing or dropping it is an error.
`Defer` can pin must-propagate messages across a deliberate deferred boundary.

`FinalInput` is a half-close signal, not a request to close output. Protocol policy may send a final response, finish a
handshake, or continue producing data before issuing `FinalOutput`. Transforms which have already accepted input must
drain any valid decoded output before forwarding a final input signal.

`ShutdownOutput` is the output counterpart of `FinalInput`: no more ordinary output follows, but input continues. It is
an ordered barrier like `FlushOutput` - every handler emits the output it accepted before it - and, like `FinalOutput`,
a protocol handler may retain it while finishing protocol-level output shutdown (TLS sends close_notify), then forwards
the same instance. Once it reaches the outbound terminal only messages marked `AfterShutdownOutput` - read requests,
flushes, deferred work, awaits - and `FinalOutput` may follow it there; anything else, including a second
`ShutdownOutput`, is rejected with `SawShutdownOutputIoPipelineError`. This mirrors `AfterFinalInput`, which keeps
output-related control signals deliverable after `FinalInput`. `ShutdownOutput` does not terminate the driver:
`FinalOutput` is still what ends it, and a driver which has seen both `FinalInput` and `ShutdownOutput` stays open until
application policy sends `FinalOutput`.

`FinalOutput` is an ordered graceful barrier. A buffering or protocol handler may retain it while flushing accepted
data or completing protocol shutdown, then forwards the same instance. Once it reaches the outbound terminal, no
further outbound message may reach that terminal.

`IoPipeline.destroy()` is different: it is immediate, abortive teardown. It does not synthesize either final message,
does not promise to drain output, removes handlers and services, and fails every pending completable with
`AbortedIoPipelineError`.

---

## 5. Completion fences

`IoPipelineMessages.Completable` supplies one-shot success or failure state and listeners. A completable is bound to the
pipeline when first sent outbound and remains pending until explicitly completed. Listeners run once and are released
after completion. Pipeline destruction fails any completable still bound to it. The outcome's result or exception is
only observable from listeners; it is released with them rather than retained, since a retained exception's traceback
would commonly reference the completable itself.

The two transport-facing fences are intentionally coarse:

### `FlushOutput`

`FlushOutput` is an ordered transport-flush fence. Before forwarding it, every handler must emit output it has accepted
before that fence. The driver completes it only after all preceding output has left pipeline-owned buffering and
crossed the driver's transport boundary.

Successful completion does not mean that the peer received, processed, or acknowledged the bytes. This system does
not attempt per-byte completion promises.

Several flushes may be outstanding. They preserve outbound order, and later fences cannot validly complete ahead of an
earlier one.

### `ShutdownOutput`

`ShutdownOutput` is a completable fence with the same ordering as `FlushOutput`. Success means all preceding output
crossed the transport boundary and the transport's output half was shut down - for a socket, `shutdown(SHUT_WR)` - so
the peer reads EOF after the preceding bytes. A transport which cannot half-close (a single non-socket descriptor, an
asyncio writer which cannot write EOF) fails the message with `UnsupportedIoPipelineError` and is otherwise left intact.

### `FinalOutput`

`FinalOutput` is both a must-propagate lifecycle message and a completable. Success means protocol shutdown reached the
transport and the driver finished its graceful-output responsibility. For an owned transport the driver will normally
also close it; for a caller-owned transport, success does not redefine that ownership contract.

Completing a fence after a timeout remains valid. A timeout reports that a deadline was missed; it does not forge a
completion result or retroactively cancel transport progress.

Completion listeners attached by removable handlers must retain the handler or context weakly. Otherwise a fence held
by a transport can unintentionally extend the lifetime of a removed protocol stack.

---

## 6. Flow control and bidirectional backpressure

Flow control is optional. If no `IoPipelineFlow` service is installed, the implied behavior is automatic input and
always-writable output. Flow messages are only meaningful in a pipeline which has that service.

### Input flow

`ReadyForInput` travels outbound from the consumer toward the transport. In manual-read mode it is a token requesting
one unit of input progress. A driver consumes the token when it performs a read; layered transforms may consume a token
when they deliver one unit of decoded input and request more wire input only when necessary.

`FlushInput` travels inbound and marks completion of the current read or decoded batch. It is a boundary event, not
ordinary read activity.

Automatic-read mode permits the driver to keep reading without explicit tokens. `IoPipelineFlow.maybe_ready_for_input`
lets a handler remain correct in both modes.

### Output flow

`ReadyForOutput` and `PauseOutput` travel inbound from transport toward application. Writability is level state with
edge notifications:

- The initial implied state is writable.
- Emit exactly one notification for each transition.
- `PauseOutput` means producers must stop creating ordinary output.
- `ReadyForOutput` means output production may resume.
- Once output has been shut down, `ReadyForOutput` is never announced again: nothing may produce ordinary output. A
  pause may still be, for a backlog still draining. Shut down means `ShutdownOutput` (or `FinalOutput`) reached the
  terminal, not merely that the transport performed it. Buffering handlers - TLS, HTTP chunking - follow the same rule
  as the drivers.

Socket drivers derive their local state from queued transport bytes with hysteresis: transition to paused above the
high watermark and back to ready at or below the low watermark. The queue still accepts data; watermarks are a
cooperative pressure signal, not a hard allocation limit.

A handler which buffers outbound data must combine downstream writability with its own backlog. It must not merely
forward downstream transitions, because doing so can announce writable while its own queue is over its high watermark.
The combined state uses the same level-triggered, edge-notified contract.

Output backpressure must never stop input. Pending output, a stalled flush, or a pending drain must not delay read
requests, deferred work, or the delivery of input: two peers each blocked on output, each waiting for the other to read,
would otherwise deadlock symmetrically. Only output bytes and output fences are ordered against pending output.

Backpressure should be held at the layer where byte accounting is honest. TLS, for example, retains blocked application
plaintext rather than eagerly converting all of it to ciphertext. Protocol-control output required to make progress,
such as TLS handshake alerts or `close_notify`, must not be gated in a way that deadlocks the protocol.

Hard safety bounds remain separate configuration: maximum buffers, frame sizes, body sizes, and similar limits are
still required where untrusted or unbounded input can accumulate.

---

## 7. Scheduling and timeouts

`IoPipelineScheduling` is an optional service. Handlers requiring it validate its presence when added; handlers whose
timeout configuration is disabled must not require it.

Scheduled work is owned by an exact handler ref:

- Removing the owner cancels its callbacks.
- Destroying the pipeline cancels all callbacks.
- Callbacks execute inside the owning pipeline.
- `Handle.cancel()` is idempotent before execution.

Prefer `schedule_context()` for handler work. The scheduling implementation can then retain the context weakly and
provide it only while running. Do not close over the handler, context, ref, or pipeline from a callback stored in that
same object graph; doing so recreates low-level reference cycles.

The heap scheduler used by sync and fdio drivers exposes the next absolute monotonic deadline and relative delay. The
asyncio driver implements the same service with loop tasks. Drivers wait for the earliest of transport readiness and a
real deadline, then run due callbacks. With no pending callback, there is no timer and no heartbeat: the design is
tickless.

Cancelling a scheduled handle, or running it, releases its callback at once: a cancelled far-future handle may linger
in a scheduler's heap until it surfaces, and must not keep its callback's captures alive meanwhile.

Timeout handlers intentionally cover different questions:

- `IdleStateIoPipelineHandler` emits repeating read, write, or combined idle events. Ordinary messages are activity;
  successful `FlushOutput` or `ShutdownOutput` completion additionally records transport-side write activity.
  `FinalInput` ends read idleness and `ShutdownOutput` ends write idleness.
- `ReadTimeoutIoPipelineHandler` emits one error when ordinary inbound activity stops.
- `WriteTimeoutIoPipelineHandler` times explicit `FlushOutput`, `ShutdownOutput`, and `FinalOutput` fences. It does
  not inject a flush or infer completion for ordinary output.
- HTTP request timeout handlers enforce an absolute semantic request/response deadline and do not reset on body
  activity.
- TLS handshake and shutdown timeouts are absolute state deadlines and do not reset merely because another TLS record
  arrived.

Timeout expiry emits `TimeoutIoPipelineError`, which is both an `IoPipelineError` and built-in `TimeoutError`. Generic
handlers report errors but do not decide whether to send a protocol response, gracefully close, or abort the transport.
That remains application or protocol policy.

---

## 8. Driver boundary and parity

There is intentionally no common `IoPipelineDriver` base class. A driver is any integration which faithfully implements
the terminal contract. The sync socket, asyncio stream, fdio socket, and pure/no-I/O implementations are reference
drivers. A shared conformance suite runs the same observable scenarios against all four without imposing inheritance.

A conforming transport driver must:

1. Construct the pipeline with its transport metadata and any runtime services.
2. Feed exactly one `InitialInput` before ordinary input.
3. Preserve the order of queued input and outbound terminal messages.
4. Handle bytes incrementally, including nonblocking partial sends and `BlockingIOError`.
5. Respect manual-read tokens when an `IoPipelineFlow` service is present.
6. Maintain output watermarks and emit only writability transitions.
7. Complete each `FlushOutput` after preceding queued bytes cross the transport boundary.
8. Treat `FinalOutput` as a drain request, complete it after graceful transport work, and expose `DRAINING` while that
   work remains.
9. Integrate scheduler deadlines without polling when none exist.
10. Destroy the pipeline and fail pending completables on abort or failure.
11. Perform `ShutdownOutput` after the output preceding it, complete it, and keep reading; fail it with
    `UnsupportedIoPipelineError`, leaving the transport intact, where the transport cannot half-close.
12. Keep honoring read requests and delivering input while output is blocked.
13. Run the scheduled callbacks already due before continuing a `Defer`: the deferred boundary is a fairness yield.
14. On `close()`, release queued input nothing will process, fail the waiters of input it never processed, and cancel
    the work it started on the application's behalf.

The generic core remains completely bytes-agnostic. At a byte transport boundary, however, the reference drivers
deliver each bounded read batch as one `ByteStreamBuffer` followed by one `FlushInput` when flow control is installed.
The sync and fdio drivers fill a mutable segmented buffer directly with `recv_into`; asyncio wraps the `bytes` returned
by its public stream API; the pure driver preserves the same observable batching contract.

Byte buffers are consumption-oriented messages with transfer ownership. Once a producer feeds a `ByteStreamBuffer`
into a pipeline, it must not advance, mutate, refill, or recycle that object. A byte decoder may adopt the buffer and
consume it directly rather than copying it into another accumulator. `split_to()` transfers a stable read-only view of
the selected segments to the produced frame or body message, so later consumption of the source buffer does not change
the view. Consumers should use `peek()` or `segments()` when their API supports scattered input, and deliberately use
`tobytes()` / `ByteStreamBuffers.to_bytes()` at boundaries which require owned contiguous bytes. Ordinary `bytes`,
`bytearray`, and `memoryview` messages remain accepted by the byte toolbox for simple and contrived uses.

The shared driver lifecycle is:

```text
NEW -> RUNNING -> DRAINING -> CLOSED
          |           |
          +---------> FAILED
```

Explicit `close()` is abortive while running or draining. `CLOSED` records successful graceful completion or explicit
closure; `FAILED` records a transport, pipeline-driving, or teardown failure. A pipeline destroyed from under a running
driver - by an application policy in a timer callback, say - ends the driver as an explicit close would.

`next(read=False)` is the common non-waiting step: it processes queued and immediately due work but does not wait for
future input or deadlines. This is important for embedding a pipeline in another scheduler and for deterministic tests.

Each reference driver exposes `output_shutdown` once it has shut down its transport's output half. Driver-specific
ownership remains explicit:

- The sync socket driver temporarily makes its caller-owned socket nonblocking and restores its prior timeout mode.
  Output shutdown is `shutdown(SHUT_WR)`, which leaves the socket itself open. The synchronous drivers wait with
  `poll()` where it exists (Linux and darwin), so a descriptor numbered above `FD_SETSIZE` is as good as any other.
- The sync descriptor-pair driver shuts down a socket write descriptor through a temporary duplicate, never closing the
  caller's descriptor. A non-socket write descriptor can only be half-closed by closing it, which the caller must
  explicitly permit; its original flags are restored first, and the closed number is never touched again.
- The asyncio driver owns its stream-driving tasks and coordinates `drain()` with flush and shutdown fences: output
  bytes and fences wait behind a pending drain, while read requests, deferred work, awaits, and output for the caller
  do not. Output shutdown is `write_eof()`, which the transport performs after its buffered bytes. The transport's own
  write buffer limits are set to the watermarks, and since it writes in the background, a drain is kept pending while
  output is paused: its completion is the return to writable, so a producer which never flushes is still resumed.
  Output bytes held behind a pending drain count toward writability like the transport's own buffer, so a producer
  continuing through `Defer` - which is not held - is still paused. `ShutdownOutput` completes once the transport has
  performed the half-close - its drain runs with zero watermarks, so it returns when the buffer is empty rather than
  at the low watermark. `FinalOutput` starts the graceful close as a task which flushes everything written and only
  then closes the transport (closing first would stop it reading at once); while a peer which has yet to read keeps
  that from completing, timers, awaits and drain completions are still serviced. A coroutine the driver turns into a
  task for an `Await` is the driver's: it is cancelled if the `Await` is failed by its producer - a multiplexed stream
  which ended, say - and when the driver closes. A task or future supplied is the caller's.
- The fdio driver is a nonblocking `FdioHandler`; `FdioManager` combines descriptor readiness with the earliest handler
  deadline. It is valid in forked or otherwise single-threaded contexts and does not depend on asyncio.
- While draining after `FinalOutput`, every reference driver keeps taking input off the transport and discards it:
  nothing consumes it any more, but a peer whose own output waits for this side to read must not wait forever.
- The pure driver queues supplied transport input, accepts output only through explicit drain steps, and advances an
  injected scheduler clock only when requested. It is both an executable reference contract and a deterministic
  generator-style integration; it does not emulate socket syscalls. An output shutdown is recorded when a drain step
  reaches it, which is where a caller simulating the peer delivers EOF to it; pending output never prevents reading.
  `fail_output()` makes the next drain step fail as a write to a departed peer would, so two pure drivers linked back
  to back can model one side closing.

---

## 9. Layering protocol transforms

Handler placement determines both the messages a handler observes and the scope of its deadlines or flow accounting.
A typical HTTP/TLS pipeline is conceptually layered as follows:

```text
transport
  optional outbound byte buffer
  TLS records / plaintext transform
  HTTP byte codec
  transfer coding (chunking / dechunking)
  content coding (compression / decompression)
  semantic timeout and connection policy
application adapter
```

The exact handler list is outer-to-inner. Therefore outbound data encounters these logical transforms in reverse: an
application response is compressed before it is chunked, encoded to bytes, encrypted, and sent.

Every buffering transform participates in ordered boundaries:

- On `FlushOutput`, emit accepted output before forwarding the same fence.
- On `FinalOutput`, either finish valid buffered protocol output or report/emit the protocol's abort representation,
  then forward or deliberately retain the same final barrier.
- On `ShutdownOutput`, behave as for the output half of `FinalOutput`: no ordinary output can follow, so finish or
  abort the current protocol unit and emit accepted output before forwarding or retaining the same instance.
- Fences arriving behind a retained `ShutdownOutput` or `FinalOutput` keep their order behind it, so the terminal
  applies its usual rules to them.
- On `FinalInput`, emit any already-decoded valid input before forwarding EOF.

Compression flushes compressor state before forwarding a flush fence. HTTP chunking flushes buffered body data so
chunk lengths match the data actually emitted. TLS may retain `FinalOutput` through `close_notify` exchange and only
forward it when its protocol shutdown reaches the closed state.

TLS uses an apply/pump/emit turn so reentrant application reactions cannot reorder ciphertext. Its output writability
combines transport state with queued plaintext. Its handshake and shutdown timers require scheduling only when those
timeouts are configured. A handshake which fails, times out, or is cut short by a transport EOF fails the flush and
shutdown fences queued behind it - the plaintext they fenced was discarded and there is no session to half-close -
while a retained `FinalOutput` is still forwarded, since it is the close. Strict ragged-EOF detection
(`suppress_ragged_eofs=False`) needs the SSL context's `OP_IGNORE_UNEXPECTED_EOF` option clear, or the engine reports a
truncated stream as a clean EOF; Python 3.8's default contexts set it, so the handler clears it on the caller's context,
a documented side effect. Removed from a pipeline, the handler drops the plaintext and backlog it holds.

TLS half-close follows RFC 8446 section 6.1: on `ShutdownOutput` it encrypts the queued plaintext, sends close_notify,
forwards the same `ShutdownOutput` so the transport half-closes after that record, and keeps decrypting until the peer's
own close_notify arrives as an ordinary EOF. Python's `unwrap()` reads incoming records while looking for the peer's
close_notify and rejects application data found there, so the handler first decrypts everything already received into a
backlog which later reads serve - as does a full close, for the same reason. A later `FinalOutput` waits for the peer's
close_notify as usual, and is released only once the plaintext preceding it has been delivered; only then does the
shutdown timeout run. A close requested during the handshake abandons it only if nothing was accepted for output before
it; otherwise the handshake completes first. HTTP chunking and compression treat a `ShutdownOutput` arriving
mid-message like `FinalOutput`, emitting the message's abort representation.

Semantic timeout handlers belong on the semantic-object side of the corresponding codec. Transport write timeouts
belong far enough outward to observe a fence only after all intended protocol layers have accepted it. Placement is a
policy decision and should be apparent in the pipeline specification.

---

## 10. Services, metadata, and dynamic handlers

Services are behavioral collaborators fixed for the lifetime of a pipeline. Lookup is by `isinstance`, so interfaces
such as `IoPipelineFlow` and `IoPipelineScheduling` can have runtime-specific implementations. A single-value lookup
requires at most one matching service.

Services may observe:

- pipeline added and removed;
- handler adding, added, removing, and removed;
- entry to and exit from the outermost execution boundary.

Metadata is passive, exact-type-keyed information fixed at construction. Drivers use it to expose their identity
without coupling handlers to a driver base class.

Handlers may be added, removed, or replaced while the pipeline is ready. Removal invalidates the old context and ref,
cancels owner-bound scheduled work, unlinks the position, and then sends `Removed`. Code performing replacement during
message handling must make the continuation point explicit; it must not keep using an invalidated context.

---

## 11. Ownership and reference-cycle discipline

This package sits beneath long-lived services, so prompt reference-counted cleanup is a design requirement, not merely
an optimization. A normal request should not depend on cyclic GC to release pipeline objects.

The core topology owns inward links strongly and outward links weakly rather than forming a doubly-linked reference
ring. Contexts reference their pipeline weakly. A public `IoPipelineHandlerRef` intentionally owns its context and
pipeline so retaining a public ref keeps its target meaningful until the ref is released.

Contributors must preserve these rules:

- Never cache an `IoPipelineHandlerContext` on its handler.
- Owner-bound scheduler handles retain contexts weakly.
- Use `schedule_context()` instead of a closure over `ctx`.
- A handler retaining a completion handle must not also be retained strongly by that handle's callback.
- Completion listeners installed by removable handlers use weak handler or context references.
- Clear queued messages, buffers, tasks, and completion state during removal, completion, close, or failure.
- When retaining a bytes-like message by reference, document that the producer must not mutate or recycle it.

Some runtime internals, especially asyncio tasks and futures, may form unavoidable temporary cycles. Pipeline-owned
cycles are not excused by that fact. Reference-ownership tests should disable cyclic GC and assert prompt release when
adding new callbacks, scheduling, or long-lived completion listeners.

---

## 12. Conformance and testing expectations

Core and handler tests should normally drive `IoPipeline` directly with small recording services. Driver behavior must
also have integration coverage because queue ordering, partial writes, readiness, and completion timing live at the
transport boundary.

Changes to lifecycle, flow, scheduling, or completion behavior should cover, as applicable:

- sync, asyncio, fdio, and pure reference drivers, including asyncio over a real socket as well as a simulated writer;
- automatic and manual input flow;
- immediate and delayed/partial transport writes;
- full-duplex progress with both peers' output blocked;
- high/low watermark transitions without duplicate notifications;
- `FlushOutput`, `ShutdownOutput`, and `FinalOutput` success and failure;
- `read=False` and tickless idle behavior;
- handler removal and pipeline destruction;
- Python 3.8 compatibility;
- reference release with cyclic GC disabled;
- HTTP clients and servers, including TLS and compression consumers.

Tests use `unittest` style and real or deterministic in-process collaborators. Avoid mocks and monkey-patching at this
layer; socket pairs, memory BIOs, explicit schedulers, and small recording handlers make the contracts clearer.

---

## 13. Stream multiplexing

`multiplex` carries many logical streams over one pipeline. A `MultiplexIoPipelineHandler`, normally innermost in the
parent pipeline, owns a set of streams, each backed by a child `IoPipeline` it drives; a `IoPipelineMultiplexAdapter` is the seam
to the concrete wire protocol. The core contains nothing protocol-specific: it was shaped against SSH channels and
HTTP/2 streams, and toy versions of both are exercised in its tests.

### Model

- A stream is identified by an opaque, hashable key chosen by the protocol. The core does not assume keys are
  integers, allocated by one side, or shared between peers.
- Peer-opened streams get their child spec from a factory given the stream's opening information, which may refuse
  them. Local streams are opened with `MultiplexMessages.OpenStream`, fed to the handler inbound (from a handler outside
  it, or from outside the pipeline with `feed_in_to`) or outbound; it completes once the stream is established.
- The adapter tells the core what arrived by calling a `IoPipelineMultiplexConnection`, valid only during that call. The core
  asks the adapter to encode what to emit, as one of two kinds of output: control output - opens, acceptances,
  refusals, resets, credit grants - which bypasses stream queues; and stream-ordered output - data, typed messages,
  end-of-output, finish - which keeps its place in its stream.
- The stream table, the stream state machine, credit accounting, and output scheduling do not depend on child
  pipelines, so a tagged-message consumer can be layered on them.

### The child pipeline contract

The multiplexing handler is each child's driver, performing the duties of section 8:

1. The child is built from the factory's spec plus `IoPipelineMultiplexStreamMetadata` (key, origin, opening information), the
   spec's own flow service or else a default one, and - only when the parent has one - a scheduling service which
   delegates to the parent's under the multiplexing handler's ownership. Nothing else is inherited.
2. `InitialInput` is fed when the stream is established: on acceptance for a peer-opened stream, on confirmation for an
   explicitly opened local one, at once for an implicit open. The child is built at that moment, so nothing can be
   queued on a local stream before its confirmation.
3. Per-stream order is exact in both directions, across data, typed messages, and fences.
4. Data is emitted in units no larger than the adapter's maximum unit nor than available credit; the remainder stays
   queued. Flow-controlled typed messages are split through the adapter, or wait until they fit.
5. In manual-read mode one child `ReadyForInput` permits one batch: everything queued at that point, up to
   `read_batch_max_bytes` of whole data units, delivered as one consumable `ByteStreamBuffer` with typed messages in
   order, followed by `FlushInput`. A token arriving with nothing queued remains outstanding. Input decoded from one
   parent read is delivered once that read has been processed - at the parent's `FlushInput`, or when a parent `Defer`
   requested at the read's first message runs - so it coalesces as a driver's read does, without depending on a
   `FlushInput` arriving. Typed messages queued behind end-of-input are not reads: they are delivered without a token,
   since a child which has seen `FinalInput` has no reason to request one.
6. Child writability is derived from the stream's queued outbound cost - data, plus flow-controlled typed messages at
   the cost the adapter gave them when collected - with high and low watermarks and hysteresis, announced once per
   transition, and re-derived before each of the child's `Defer` continuations runs, so a producer continuing through
   them is paused in time. Credit exhaustion and parent pauses reach a child only through the growth of its queue.
7. A child `FlushOutput` completes once everything queued before it has been emitted into the parent and a parent
   `FlushOutput` issued after that point has completed; it fails if the stream or connection dies first.
8. A child `ShutdownOutput` is the stream's end-of-output: emitted after everything before it, it completes under the
   same rule. A child `FinalOutput` drains the stream's queue under credit, finishes the stream as the adapter encodes
   it, completes after the matching parent flush, and the child is then destroyed. While it drains, the stream's local
   side is not yet finished.
9. Child timers run through the parent's scheduler, inside the child. Removing a child handler, destroying the child,
   or removing the multiplexing handler cancels them; cancelled timers hold the child side only weakly.
10. Stream reset, connection failure, connection EOF before the peer ended its output, removal of the multiplexing
    handler, and parent destruction abort the child: it is told with an inbound `Error`, its queued fences fail, and it
    is destroyed, failing anything else pending.

Additionally: `Defer` reaching a child's terminal runs with the child's `run_deferred`. `Await` is forwarded as a new
parent `Await` of the same awaitable, its completion relayed into the child; where the parent's driver cannot await,
the child sees exactly what a top-level pipeline on that driver would (the sync and pure drivers return it to their
caller as unhandled output). Any other message at a child's terminal is offered to the adapter; if unclaimed it fails
within that child as an inbound `Error`. A handler error in a child stays in the child; one escaping it - an error
reaching the child's terminal unhandled, a failing timer callback, a failed construction - resets that stream only.

### Lifecycle

A stream's state is the product of its halves plus a terminal outcome: local OPENING (awaiting confirmation), OPEN,
ENDED (end-of-output emitted), FINISHED (child done); remote OPEN or ENDED; terminal CLOSED, RESET, or REFUSED. Both
halves ending does not close a stream - typed messages may still follow end-of-data in some protocols, and closure may
need a handshake - so the adapter closes explicitly, and the core resets or refuses.

- The peer ending its output feeds `FinalInput` to the child after everything queued before it. Typed messages may
  follow it if marked `AfterFinalInput` (and, outbound, after `ShutdownOutput` if marked `AfterShutdownOutput`).
- A close from the peer while the child still runs is graceful: the child receives what was queued, then
  `FinalInput`; its further output is discarded, fences other than `FinalOutput` failing; the stream is released once
  the child finishes. A close after the local side finished releases the stream at once. A close decoded from the same
  read as the acceptance it follows is just as graceful: the child is built, receives what was accepted, then
  `FinalInput`.
- A reset aborts the child with `StreamResetMultiplexIoPipelineError`, recording which side reset. If the child had already
  finished and only awaits its final flush, it completes normally.
- On connection EOF, streams whose peer had ended its output carry on - the connection's output is still open - while
  the others are aborted with `StreamTruncatedMultiplexIoPipelineError`, and unconfirmed local opens fail. The adapter's
  `on_input_ended` then decides the connection's fate; by default it shuts down gracefully.
- Graceful shutdown (`MultiplexMessages.Shutdown`, or the adapter's `begin_shutdown`) admits no new streams in either
  direction, lets existing ones finish, and then emits parent `FinalOutput`. An adapter implementing "streams above
  this key were not processed" resets those streams itself through the connection.
- Released keys are reported to `on_stream_released`, where a protocol needing to absorb late frames remembers them.
  Flow-controlled frames for a stream which has ended but is not yet released are counted against any connection-level
  window and dropped; for a released one, the adapter reports their cost with `discard`.
- A child pipeline destroyed by anyone but its driver - its opener, say - abandons its stream, which is reset. A remote
  stream whose child cannot be built is refused, and counted as refused; a stream spec factory raising refuses that
  stream alone, with the exception as the reason.
- An adapter raising while encoding or sizing fails the connection, as one raising while decoding does. Tearing the
  connection down releases every stream's queued input and output, and the parent `Await`s forwarded for its streams
  are failed, as they are when their stream alone ends, so the parent's driver cancels the work it started for them.
- Concurrent stream limits apply per origin and may be changed at any time; refusals by limit and by factory are
  encoded by the adapter with a reason.

Stream errors (reset, truncation, connection closed) are `AbortedIoPipelineError`s.

### Flow control

Credit accounting is a pluggable strategy: `StreamMultiplexCreditStrategy` (per stream only) and
`ConnectionMultiplexCreditStrategy` (per stream plus connection-wide).

- Credit is signed. Adapters grant per stream or per connection and shift every stream at once, by positive or
  negative deltas; a stream at or below zero simply cannot send flow-controlled output until it recovers.
- A flow-controlled unit's cost is its length plus the adapter's per-unit overhead (padding, say); a typed message's
  cost comes from the adapter, once, when the message is collected from its child. Uncontrolled typed items cost
  nothing but never overtake data queued before them.
- Receive credit is debited on arrival and replenished by policy as delivery consumes it (by default once half a window
  is consumed). Connection-level replenishment is its own policy: by default it frees credit as input arrives, so the
  connection window bounds only what is in flight and one slow stream cannot stall the others; freeing it on consumption
  instead bounds total buffering. Arrivals beyond advertised credit raise `FlowControlMultiplexIoPipelineError` to the adapter,
  which decides whether that is a stream or a connection error.
- Queued input per stream is bounded by its window; uncontrolled typed messages by a separate count limit. Empty data
  is never queued.
- Credit is not granted on a stream the peer has ended or closed: nothing more will arrive. A stream whose local side
  has finished may still receive, so its grants are offered to the adapter, which encodes them when its protocol allows
  (HTTP/2 after END_STREAM) and declines them - returning nothing - when it does not (SSH after its CLOSE); a declined
  grant is withdrawn, so the accounting follows the wire. Input a finished or failed child left queued, and input a
  reset discards, returns its credit as if it had been consumed.
- Control output is never gated by credit, per-stream backlog, or parent writability. While the parent is paused, the
  amount emitted is bounded; exceeding the bound fails the connection.
- While the parent is paused no stream output is emitted; it stays queued per stream, where byte accounting is honest.
- One turn emits at most a configured budget of flow-controlled output (and, optionally, units under a yield policy)
  and continues through a parent `Defer`, because the parent's driver reports writability only after processing what was
  emitted. Readiness is checked again before each unit, as emitting can reenter: a reset, a failure, or another stream
  spending shared connection credit can change it.

### Output scheduling and the turn

When several streams have sendable output, a pluggable scheduler chooses between them; the default is deficit round
robin with a byte quantum and per-stream weights, which starves no stream that stays ready. A stream's weight comes
from its parameters at open and may be changed through the connection (an HTTP/2 PRIORITY, say), applying from its
next turn.

The handler follows the TLS handler's discipline: entry points record state; a pump advances children, delivering
input and collecting output, without feeding the parent; a single emit phase feeds the parent. Within a turn the emit
order is fixed: open completions, control output, forwarded Awaits, stream output by scheduler, one parent
`FlushOutput` covering every child fence reached, a parent read request, and finally parent `FinalOutput` once a
shutdown has drained. Nested entries during emission only record state and mark the turn dirty.

The handler requests parent input after each parent batch it consumed messages from, leaving a decoder which consumed
a batch without producing anything to request more itself.

### Ownership

The handler owns its streams and children. Children and their services never own the handler, its context, or the
parent pipeline: completion listeners on parent fences and Awaits hold the context and the child side weakly, child
timers are owned by the handler's ref and reach the child weakly, and the child's scheduling service reports failures
without holding the child. Closing a stream clears its queues, timers, and completion state immediately, and a closed or
reset stream - and a destroyed parent with everything in it - is released by reference counting alone.

The handler exposes read-only facts a protocol may use for its own defenses: stream counters (opened, refused, reset by
each side, closed, active by origin), control output emitted during the current pause, and per-stream queued input.

---

## 14. Deliberately separate future decisions

The following are not implied by the current contracts and should be designed independently:

- Which HTTP client or server configurations should install generic write timeouts automatically.
- Default policy after generic idle, read, or write timeout errors.
- Thread-safety and free-threaded Python guarantees.
- Request pipelining (correlation by order, without stream identity or credit), and HTTP/2 itself.

These decisions may extend the system, but they must preserve ordering, completion, tickless scheduling, backpressure,
and ownership invariants described above.
