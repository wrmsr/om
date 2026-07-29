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
| `FinalOutput` | Outbound | Gracefully finish accepted output and terminate the driver. |
| `Error` | Inbound | A processing, protocol, timeout, or transport failure is being reported. |

`InitialInput`, `FinalInput`, and `FinalOutput` are `MustPropagate`. The exact message instance must reach its terminal
position. A handler may retain one temporarily, but silently replacing or dropping it is an error. `Defer` can pin
must-propagate messages across a deliberate deferred boundary.

`FinalInput` is a half-close signal, not a request to close output. Protocol policy may send a final response, finish a
handshake, or continue producing data before issuing `FinalOutput`. Transforms which have already accepted input must
drain any valid decoded output before forwarding a final input signal.

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
after completion. Pipeline destruction fails any completable still bound to it.

The two transport-facing fences are intentionally coarse:

### `FlushOutput`

`FlushOutput` is an ordered transport-flush fence. Before forwarding it, every handler must emit output it has accepted
before that fence. The driver completes it only after all preceding output has left pipeline-owned buffering and
crossed the driver's transport boundary.

Successful completion does not mean that the peer received, processed, or acknowledged the bytes. This system does
not attempt per-byte completion promises.

Several flushes may be outstanding. They preserve outbound order, and later fences cannot validly complete ahead of an
earlier one.

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

Socket drivers derive their local state from queued transport bytes with hysteresis: transition to paused above the
high watermark and back to ready at or below the low watermark. The queue still accepts data; watermarks are a
cooperative pressure signal, not a hard allocation limit.

A handler which buffers outbound data must combine downstream writability with its own backlog. It must not merely
forward downstream transitions, because doing so can announce writable while its own queue is over its high watermark.
The combined state uses the same level-triggered, edge-notified contract.

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

Timeout handlers intentionally cover different questions:

- `IdleStateIoPipelineHandler` emits repeating read, write, or combined idle events. Ordinary messages are activity;
  successful `FlushOutput` completion additionally records transport-side write activity.
- `ReadTimeoutIoPipelineHandler` emits one error when ordinary inbound activity stops.
- `WriteTimeoutIoPipelineHandler` times explicit `FlushOutput` and `FinalOutput` fences. It does not inject a flush or
  infer completion for ordinary output.
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
the terminal contract. The sync socket, asyncio stream, and fdio socket implementations are reference drivers.

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

The shared driver lifecycle is:

```text
NEW -> RUNNING -> DRAINING -> CLOSED
          |           |
          +---------> FAILED
```

Explicit `close()` is abortive while running or draining. `CLOSED` records successful graceful completion or explicit
closure; `FAILED` records a transport, pipeline-driving, or teardown failure.

`next(read=False)` is the common non-waiting step: it processes queued and immediately due work but does not wait for
future input or deadlines. This is important for embedding a pipeline in another scheduler and for deterministic tests.

Driver-specific ownership remains explicit:

- The sync socket driver temporarily makes its caller-owned socket nonblocking and restores its prior timeout mode.
- The asyncio driver owns its stream-driving tasks and coordinates `drain()` with flush fences.
- The fdio driver is a nonblocking `FdioHandler`; `FdioManager` combines descriptor readiness with the earliest handler
  deadline. It is valid in forked or otherwise single-threaded contexts and does not depend on asyncio.

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
- On `FinalInput`, emit any already-decoded valid input before forwarding EOF.

Compression flushes compressor state before forwarding a flush fence. HTTP chunking flushes buffered body data so
chunk lengths match the data actually emitted. TLS may retain `FinalOutput` through `close_notify` exchange and only
forward it when its protocol shutdown reaches the closed state.

TLS uses an apply/pump/emit turn so reentrant application reactions cannot reorder ciphertext. Its output writability
combines transport state with queued plaintext. Its handshake and shutdown timers require scheduling only when those
timeouts are configured.

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

- sync, asyncio, and fdio reference drivers;
- automatic and manual input flow;
- immediate and delayed/partial transport writes;
- high/low watermark transitions without duplicate notifications;
- `FlushOutput` and `FinalOutput` success and failure;
- `read=False` and tickless idle behavior;
- handler removal and pipeline destruction;
- Python 3.8 compatibility;
- reference release with cyclic GC disabled;
- HTTP clients and servers, including TLS and compression consumers.

Tests use `unittest` style and real or deterministic in-process collaborators. Avoid mocks and monkey-patching at this
layer; socket pairs, memory BIOs, explicit schedulers, and small recording handlers make the contracts clearer.

---

## 13. Deliberately separate future decisions

The following are not implied by the current contracts and should be designed independently:

- Whether fdio graceful completion should perform an observable `shutdown(SHUT_WR)` phase before close.
- Which HTTP client or server configurations should install generic write timeouts automatically.
- Default policy after generic idle, read, or write timeout errors.
- A pure/no-I/O reference driver or a shared conformance harness.
- Thread-safety and free-threaded Python guarantees.
- Request pipelining, HTTP/2 integration, and other protocol-level multiplexing.

These decisions may extend the system, but they must preserve ordering, completion, tickless scheduling, backpressure,
and ownership invariants described above.
