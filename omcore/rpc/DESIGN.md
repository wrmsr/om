# rpc design

This document records the exploration, discussion, and plan behind `omcore/rpc`: a lite, amalgamatable rpc toolbox
built on `omcore.io.pipelines`, intended to replace the repo's four overlapping rpc implementations. It was built in
`omxtra/rpc` and promoted here once the core needed no new machinery for the omllm and JSON-RPC migrations.

It is written for a reader who knows the repo but did not sit through the discussion. Section 1 is the survey that
motivated the work, section 2 the goals that came out of discussing it, sections 3 through 6 the design, section 7 the
roads deliberately not taken, and sections 8 through 10 the testing, migration, and implementation plans.

Status: the core is implemented, tested under 3.8, 3.14, and 3.14t, and promoted to `omcore/rpc` (section 11 records
what was built, section 12 what implementation taught). omllm, JSON-RPC, `ominfra.manage`, and `omxtra.daemons` are
migrated (12.9 through 12.15), and `omxtra.blobs` has a remote store built on it (12.16).


## 1. The landscape

Six areas were read end to end, including their design documents (`omxtra/daemons/DESIGN.md` and `ROADMAP.md`,
`omcore/io/pipelines/DESIGN.md` and `README.md`, the omllm remote READMEs and `_devdocs`), plus the git history of each.

### 1.1 `omllm/core/rpc` with `omllm/agent/remote`

The only live user: it runs the agent's tool backends (filesystem, processes) in a remote process such as a dockerdev
container, bootstrapped with `omcore.os.pyremote` over `docker exec -i`, from a single amalgamated script. Lite per file
since 2026-10-14 (its README said otherwise until this effort; the note predated the lite tooling learning to handle
lite modules under non-lite packages).

Protocol and shape:

- A symmetric `RpcPeer` over raw `asyncio` streams: four-byte network-order length frames of tagged compact JSON.
- Seven envelope kinds: request, result, error, cancel, notification, ping, pong. Request ids are positive ints scoped
  per direction, so the same integer can be in flight both ways.
- A task per inbound request; a bounded in-flight count with a `busy` rejection; wire-level cancel which cancels the
  handler task; late replies for ids this side issued are dropped, replies for ids never issued are protocol errors.
- Notifications may be applied *inline on the receive loop* (`RpcHandler.handle_notification_inline`), which makes
  wire order the delivery order; this is how process output streams. Replies the receive loop itself owes (pongs,
  `busy` rejections) go out from a short-lived task so a backpressured writer cannot stall reading.
- Errors cross as `{code, type, message, traceback}`; codes `remote | cancelled | method_not_found | result_encoding |
  busy`; `translate.py` maps remote builtin exception names back to local builtin types.
- Teardown runs to completion however it is entered, fails every pending call, runs close callbacks, releases
  `wait_closed`.
- The core deals only in JSON values. Each concern is a protocol/server/client triple (`fs/remote`,
  `processes/remote`) which calls the lite marshaler itself; chunked handle-based transfers for large payloads.

What it lacks: pipelines, any sync or fdio story, a scheduler (so ping is a method you call, not a keepalive policy),
and it had an unprefixed module global in lite code, `_FRAME_HEADER`, which is exactly the hazard `AGENTS.md` warns
about (fixed as part of this effort). Its public names collide with the daemons package: `RpcError`, `RpcHandler`,
`RpcProtocolError`, `RpcRemoteError`.

### 1.2 `ominfra/manage/remote`

The direct predecessor, last touched 2026-09-08: system management and code deployment, a mitogen analog without
routing, also pyremote-bootstrapped and amalgamated.

- Little-endian four-byte length frames (`<I`); the lite `ObjMarshalerManager` marshals polymorphic `Command`
  dataclasses.
- A sequence-correlated request/response loop, periodic pings inside the server loop, log forwarding as a response
  kind, a timebomb thread, deathsig, process-group handling, and a bootstrap object sent as the first message so the
  remote builds its injector.
- Both ends are hand-rolled `asyncio.wait` loops.

Most of what is distinctive here is remote process lifecycle, not rpc. The residue worth keeping is the idea of
polymorphic command objects as an alternative to string method tables (a serde-level choice, see 6.6), and the side
concerns, which stay with it when it migrates.

### 1.3 `omxtra/daemons/rpc`

Standard (non-lite) code, moved out of core on 2026-10-16 after an agent over-built it, but still intended for eventual
use. The first rpc to sit on pipelines:

- A bounded length-frame decoder (`!I`) written as a `BufferedBytesToMessageDecoderHandler`, a JSON codec to typed wire
  dataclasses, separate client and server session handlers emitting command and event messages, and specs built with a
  stub flow service. Driven by the sync socket, asyncio stream, and fdio drivers.
- A deliberately narrow protocol: hello handshake with protocol version and instance id, one request per connection,
  `(client_id, request_id)` identity, a fail-closed server-side replay registry, and a four-way outcome taxonomy
  (result or remote error; unavailable; lost response on the same instance, so constrained replay; indeterminate on a
  different instance).
- `RpcServerRuntime` activity leases, thread-per-connection sync server, asyncio and fdio servers, a threaded async
  handler adapter.
- Endpoints and transports were already extracted to `omcore.sockets`, which is lite.
- `objects.py` is a reflection-based object facade; the user has ruled auto-proxying out of scope.

Its own `ROADMAP.md` says the hosts are rpc-specific and meant to inform a general pipeline server.

### 1.4 `omcore/specs/jsonrpc/pipelines`

Standard code, created 2026-09-09, serving MCP and ACP. The most mature sans-io design in the repo:

- One symmetric `JsonrpcSessionHandler`, innermost in the pipeline, owning all protocol state; commands in, events out;
  timers from the `Scheduling` service; every policy in one frozen config (request and handling timeouts, in-flight
  limits with `reject` or `pause`, batches, invalid-message handling, peer-EOF draining, write and idle timeouts).
- `Sent` tied to flush-fence completion, which is what makes backpressure real.
- ndjson and `Content-Length` framing handlers, a codec handler which never raises (encode failures are reported inward
  as `OutboundEncodeFailed`), and a spec builder.
- A driver-independent `BaseJsonrpcConnection` demultiplexing events to an abstract `JsonrpcResponseWaiter`, with a
  `SyncJsonrpcConnection` pumping in the caller's thread (dispatching inline between steps) and an
  `AsyncioJsonrpcConnection` with a pump task, future-backed waiters, and a tracked task per request.
- Tested under the pure driver with a manual clock.

Its dispatchers bind by signature, but that is at the dispatch layer, not the core. Its weakness, from this effort's
point of view, is that the sync and asyncio connections each reimplement send, request, close, dispatch, and the
construction helpers in two colors: about eleven hundred lines for what is one set of logic.

### 1.5 `omxtra/blobs/local`

Not rpc, but the forcing requirement ("the straw that broke the back"): the user wants a local blob store that can be
run remotely exactly like the agent tools. The sync `BlobStore` has ranged gets, streamed puts, commit-on-close
writers, and iterator listings; `LocalBlobStore` is standard-only (`match`, `datetime.UTC`, `omcore.dataclasses`).
Making it remote needs two things: a lite rpc core that can go in an amalgam, and a lite target-side store. The second
is its own refactor and the reason blobs is last in the migration order.

### 1.6 `omcore/io/pipelines`

The foundation this must be powered by. Everything except `all.py` is lite, which is the crucial enabler. Netty-like:
synchronous handlers in an outer-to-inner chain, lifecycle messages (`InitialInput`, `FinalInput`, `ShutdownOutput`,
`FinalOutput`, `Error`, `Defer`), `Completable` fences (`FlushOutput`) for backpressure, services (`Flow`, `Scheduling`,
`Posting`), tickless heap scheduling, drivers for sync sockets and fds, asyncio streams, fdio, and a pure deterministic
driver with a manual clock plus a `PureLink` which steps two pure drivers back to back. Idle, read, and write timeout
handlers, logging, SSL, buffering, multiplexing, relays, and hosts all exist.

Two gaps mattered here: there was no pipeline-handler-shaped length-prefixed frame codec (daemons wrote its own;
`omcore/io/streambufs/framing.py` has the decoder), and there is deliberately no driver base class, sync or async.

### 1.7 Where the four overlap

| Concern | omllm | manage | daemons | jsonrpc |
| --- | --- | --- | --- | --- |
| Framing | 4-byte BE | 4-byte LE | 4-byte BE | ndjson, content-length |
| Codec | tagged JSON, lite marshal | lite marshal manager | hand-mapped JSON | omcore marshal |
| Correlation | per-direction ints | seq ints | client id + request id | injectable id creator |
| Error shape | code, type, message, traceback | CommandException | code, type, message | int code, message, data |
| Notifications | yes, inline option | log only | no | yes |
| Cancel | on the wire | no | no | local only |
| Keepalive | ping method | interval ping in loop | none | idle handler |
| Handshake | none | bootstrap object | hello + instance id | none |
| Concurrency | task per request | task per command | thread or task per connection | task per request; inline in sync |
| Transport | asyncio streams | asyncio streams | pipelines drivers | pipelines drivers |
| Lite | yes | yes | no | no |

The recombination rule that fell out: jsonrpc's architecture, omllm's protocol, daemons' guarantees as optional legos,
all of it lite.


## 2. Goals and constraints

Stated by the user over the course of the discussion, in roughly the order they came up.

1. **An amalgamatable lite core with a non-lite `all.py`**, like `omcore/io/pipelines/all.py`, and not painful or
   alien to use from standard code.
2. **Maximize code shared across sync, fdio, asyncio, and any future loop**, even if asyncio is the only real
   implementation for a while.
3. **Lean heavily on pipelines, but decouple what need not be coupled.**
4. **Heavily composable.** Pings and keepalives available but optional; when unneeded, absent as code: generalized side
   classes which are simply not instantiated.
5. **Ideally also satisfies jsonrpc's needs**, even though the internal wire format is not jsonrpc.
6. **Extremely low magic in the core**: no reflection or inspection. The daemons auto-proxying object facade is
   strictly out of scope for now.
7. **Pluggable serde** hooking both the standard reflection-based marshal system and the tiny lite one, with the core
   probably unaware of either.
8. **`asynclite` may help, but do not rope it in just to.**
9. **Both one-at-a-time and delegated (worker pool or task) request processing have valid uses.** This is the touchiest
   scoping question; be wary of scope creep into a "background job manager"; err toward punting with callouts.
10. **Wire pluggability at the envelope level**: JSON is the default and the only wired implementation, but JSON-ness
    must not be hard-coded into the core (CBOR is the illustrative alternative). Do not try to type-alias an envelope
    value union; keep the extension point hands-off.
11. **No parallel sync and async code colors.** The modern idiom is `omcore/inject/impl/sync.py` (and
    `omdev/repl/manhole/sync.py`): a sync and an async *interface*, but under the hood a single async/await sans-io
    core, with the sync facade driven by `lang.sync_await`. The pipelines code itself is the exception because it is
    the lowest level and hand-optimized; this toolbox sits high enough that coroutine overhead is negligible. The
    blobs package's parallel pair is a deliberate experiment in a more specific package, not a precedent.
12. **Start in `omxtra/rpc`; `omcore/rpc` is the intended home.** Promote in its own commit once nothing new is
    expected to be needed for the omllm and jsonrpc migrations.
13. **Own the `Rpc` prefix outright.** Do not avoid clashes with the omllm names; replace them when omllm migrates.
14. **All asyncio tasks strictly tracked**, as the jsonrpc connection does.
15. **Amenable to asyncio cancellation**: at least give a nod to a handler task raising `CancelledError`.
16. **A demo** combining polymorphic serde with `omcore.dispatch.Method` and/or `omcore.collections.AttrRegistry`,
    outside the core.
17. **Tests are unittest-style like `io/pipelines`, and actually run under `VENV=8`**; test continuously under 14, 14t,
    and 8. This mandates no code in the package's `__init__.py` files.
18. **Migration order**: core, omllm, jsonrpc, manage, daemons, blobs (blobs is a stretch goal for the first session;
    the first two alone are "a big win").
19. **Framing codec**: written pipelines-style, staged here, and kept under `rpc/` even after promotion for the
    foreseeable future.

A "toolbox" is the governing metaphor: an ecosystem of interrelated legos with iteratively developed conventions and
recipes, smaller than pipelines but the same shape and trajectory.


## 3. Architecture

### 3.1 The one picture

```
                  caller (sync facade or async)           handlers (method tables)
                              |                                   ^
                              v                                   |
    +-----------------------------------------------------------------------------+
    |  RpcConnection  (one async-colored class: ids, waiters, send fences,        |
    |                  dispatch glue, error conversion, close sequencing)         |
    +----------------------------------+------------------------------------------+
                                       |  RpcRuntime (sync | asyncio | ...)
                                       |  make_promise / wait / start / spawn / cancel
    +----------------------------------v------------------------------------------+
    |  pipeline driver  (sync socket/fd, asyncio stream, pure, ...)               |
    |                                                                             |
    |   outermost                                                      innermost  |
    |   [buffer] [ssl] [write timeout] [framing] [envelope codec] [keepalive]     |
    |   [idle] [...between...] [SESSION]                                          |
    +-----------------------------------------------------------------------------+
```

Everything inside the pipeline is sync sans-io in the pipelines idiom. Everything above the driver is one async-colored
class plus a small per-loop runtime. The split falls exactly on the line pipelines already draws.

### 3.2 Why the session stays inside the pipeline

The session is where timers live. Pipelines' `Scheduling` service gives it tickless deadlines which behave identically
under every driver and deterministically under the pure driver's manual clock. An async sans-io core cannot sleep and
would need a timer port of its own; the pipeline already is that port. Keeping the session a sync handler also keeps it
testable with nothing but a pure driver and a list of events, which is how jsonrpc's is tested.

### 3.3 Why the connection is one class

Comparing jsonrpc's `sync.py` and `asyncio.py` side by side shows what is duplicated: `_send` (enqueue and wait for
`Sent`), `send_request` (register a waiter, send, wait, cancel on abandonment), `close` (enqueue `Close`, bounded wait,
abort on expiry), request and notification dispatch wrapping, error conversion, and every construction helper. All of
that is logic, and all of it is written twice because the two classes are different colors.

Under the single-color idiom the only things that genuinely differ reduce to five operations: make a promise, wait on
one, start the pump, run a handler, cancel a handler. Those five are the runtime seam (section 5). Everything else is
written once.

### 3.4 Data flow for one request

1. The caller invokes `request(method, params)` on the connection (or on the sync facade, which `sync_await`s it).
2. The connection allocates an id from its id creator, makes a runtime promise, registers it as the waiter for that id,
   and enqueues a `SendRequest` command on the driver, then waits on a second promise for the session's `Sent` event.
3. The pump steps the driver. The command reaches the session, which registers the pending request, feeds the request
   envelope outbound through the codec and framing to the transport, follows it with a `FlushOutput` fence, and emits
   `Sent` when the fence completes.
4. The peer's response envelope comes back through framing and codec to the session, which matches it to the pending
   entry and emits `ResponseReceived`.
5. The pump delivers the event to the connection, which resolves the waiter. The caller's wait returns; a result
   envelope yields its value, an error envelope raises `RpcRemoteError`.

Under the sync runtime, steps 3 through 5 happen inside the caller's `wait`: the promise pumps the driver until it is
done. Under asyncio, the pump task does them while the caller is suspended on a future.


## 4. The wire and the session

### 4.1 Framing

A fixed-width unsigned length prefix (four bytes, network order by default; width and byte order configurable) followed
by that many payload bytes. The limit applies to the payload. A received frame over the limit is fatal, since the stream
cannot be resynchronized; a sent one is caught by the codec before it reaches framing. Implemented as a
`BufferedBytesToMessageDecoderIoPipelineHandler` over `LengthFieldByteStreamFrameDecoder`, producing and consuming
`RpcFrame`. A stream ending inside a frame is reported as an inbound `Error` message rather than raised, so
`FinalInput` still propagates.

### 4.2 Envelopes

Seven frozen dataclasses, the protocol omllm already proved: `RpcRequestMessage(id, method, params)`,
`RpcResultMessage(id, result)`, `RpcErrorMessage(id, error)`, `RpcCancelMessage(id)`,
`RpcNotificationMessage(method, params)`, `RpcPingMessage(id)`, `RpcPongMessage(id)`.

Ids are opaque values, scoped to the direction they were issued in; the connection's id creator decides their shape (a
per-direction integer counter by default; a uuid creator when a future replay registry needs stable client-chosen ids).
Params and results are typed `Any` and are never inspected by anything below the serde.

### 4.3 Codecs, in two pluggable halves

- **Value codec**: bytes to an opaque value tree and back. `JsonRpcValueCodec` is the default (compact, UTF-8, NaN
  rejected). Anything which can carry string-keyed mappings, strings, and whatever the serde produces plugs in here;
  CBOR is the illustrative alternative.
- **Envelope codec**: the seven envelopes to and from such a tree. `RpcValueEnvelopeCodec` spells each as a mapping
  tagged by kind, `{"type": "request", "id": 1, "method": "fs.read_file", "params": {...}}`, and error data as
  `{"code", "type", "message", "traceback"?}`. Unknown keys are ignored on decode. This is the one place a differently
  shaped dialect differs.

The pipeline handler around them decodes inbound frames (a decode failure is a protocol error and fatal) and encodes
outbound envelopes without ever raising: an unencodable or oversized envelope is dropped and reported inward as
`OutboundEncodeFailed`, so the session fails only that request or substitutes an error response. The core modules never
import `json`; only the default value codec does.

### 4.4 The session

`RpcSessionIoPipelineHandler`, innermost, modeled directly on jsonrpc's session with batches and spec-mandated invalid
message handling removed and pings, wire cancel, and the envelope kinds added.

State: `new`, `open`, `closing`, `closed`. Three maps: pending outbound requests, pending outbound pings, in-flight
inbound requests, each entry carrying an optional scheduler handle.

Commands (connection to session): `SendRequest(request, timeout_s)`, `SendNotification`, `SendResponse`,
`CancelRequest(id, notify_peer)`, `SendPing(ping, timeout_s)`, `Close(graceful)`. Events (session to connection):
`RequestReceived`, `NotificationReceived`, `ResponseReceived`, `RequestFailed`, `RequestHandlingAborted`,
`PongReceived`, `PingFailed`, `Sent`, `OutputPaused`, `OutputResumed`, `Closed`. Commands are `AfterFinalInput` so
responses can still be sent after the peer half-closes; events are `AfterShutdownOutput` so the connection still hears
about them after an output half-close. Internal: `OutboundEncodeFailed` from codec to session.

Behaviors worth calling out:

- **Execution-agnostic.** The session emits `RequestReceived` and nothing more; who runs the handler, and how, is the
  connection's business.
- **Pings answered by the session itself**, never involving the host. Outbound pings are tracked like requests with
  their own default timeout.
- **Cancel both ways.** Inbound `RpcCancelMessage` aborts the in-flight entry and emits `RequestHandlingAborted` with an
  `RpcCancelledError`; no reply is sent, since the peer has already given up. Outbound cancels are sent when a request
  is abandoned by its caller or times out (`cancel_abandoned_requests`, default on).
- **Timeouts**: per-request and default request timeouts, ping timeouts, inbound handling timeout, close drain
  timeout, idle timeout (only when nothing is in flight), all via `Scheduling`, and only armed when configured, so an
  unconfigured session schedules nothing.
- **Limits**: pending outbound and in-flight inbound counts; `reject` answers with a `busy` error, `pause` stops reading
  via flow control until there is room (only safe for pure server roles; the spec builder sets the flow service's
  auto-read accordingly).
- **Session-generated errors** carry stable codes: `busy`, `shutting_down`, `handling_timeout`, `result_too_large`,
  `result_encoding`, with the local exception class name as `type`.
- **Strictness policy**: unmatched responses and pongs are dropped by default (they race with timeouts and cancels by
  nature; configurable to close); a duplicate inbound request id closes the connection with a protocol error, since
  same-code peers never do that.
- **Peer EOF**: fails pending outbound work; by policy either closes or drains in-flight inbound requests so their
  responses still reach a half-closed peer.
- **`Sent` is tied to the flush fence** following each send command, which is what makes backpressure real.
- **Closing** fails everything pending, aborts everything in flight (answering with `shutting_down` when the transport
  is still usable and the policy says so), emits `Closed` exactly once, surfaces a failure as a raw exception output so
  a stalled transport flush cannot hide it, and completes pipeline output.
- **Reentrancy** is handled as in jsonrpc: every `feed_out` may synchronously deliver an `Error` back, so state is
  re-checked after each, and the terminal transition is idempotent.

### 4.5 Optional side handlers

- **Keepalive** (`RpcKeepaliveIoPipelineHandler`): between codec and session, only instantiated when
  `keepalive_interval_s` and `keepalive_timeout_s` are set. After the interval with nothing received it sends a ping;
  if nothing at all is received within the timeout it fails the connection with an `RpcTimeoutError`. Any received
  envelope is liveness, so an active connection never pings. Its pongs are consumed before reaching the session and
  use a private string id space so they never collide with explicit pings.
- **Idle close**: pipelines' own `IdleStateIoPipelineHandler`, installed only when `idle_timeout_s` is set; the session
  closes on `ALL_IDLE` only when nothing is in flight.
- **Write timeout, SSL, logging, outbound buffering**: pipelines legos, installed by the spec builder by config.
- **Handshake / instance identity** (future, with the daemons migration): a handler holding traffic until hellos are
  exchanged, exposing the peer's instance id. Not built now.

### 4.6 The spec builder

`rpc_build_pipeline_spec(config, ...)` assembles the pipeline outermost first: caller-supplied outermost handlers,
optional logging, outbound byte buffering (when flow is on), optional SSL, optional write timeout, framing, the envelope
codec handler (or a caller-supplied one), the keepalive handler when configured, the idle handler when configured,
caller-supplied between-handlers, the session, caller-supplied innermost handlers. The flow service's auto-read follows
the in-flight limit policy. Every seam is a keyword: framing handler, envelope codec or codec handler, session handler.


## 5. The connection and the runtime seam

### 5.1 `BaseRpcConnection` and `RpcConnection`

One async-colored class, in two layers. `BaseRpcConnection` is protocol-agnostic: lifecycle, waiters and send fences
under opaque keys, the send-and-wait pattern with abandonment, close sequencing, and close callbacks, with hooks naming
the session's close command and default close bound. `RpcConnection` is this toolbox's protocol on top of it: its
envelopes, its session events, `RpcHandler`, and its error mapping. The split exists so that a connection for another
session vocabulary - JSON-RPC's - is a subclass demultiplexing its own events onto the base's helpers; see 12.1.

Between them they own:

- id assignment through an injectable id creator;
- the waiter map (id to promise) for requests and pings, and a send-fence map (command to promise) for `Sent`;
- `request`, `notify`, `ping`, `start`, `serve`, `close`, `wait_closed`, async context management;
- event demultiplexing from the runtime sink: responses and failures resolve waiters, `Sent` resolves fences,
  `RequestReceived` runs a handler, `NotificationReceived` applies inline or runs a handler, `RequestHandlingAborted`
  cancels the spawned handler, `Closed` and driver completion mark the connection closed, fail every waiter, cancel
  every handler, and release `wait_closed`;
- handler invocation: the result becomes a `SendResponse` with a result envelope; an exception becomes an error
  envelope via error conversion (code `remote`, the exception's class name as `type`, `str(exc)`, an optional bounded
  traceback); `RpcMethodNotFoundError` becomes code `method_not_found`; a cancelled handler becomes code `cancelled` if
  the request is still in flight, and the cancellation is re-raised;
- close sequencing: a graceful close enqueues `Close(graceful=True)` and waits for `Closed` bounded by the configured
  drain plus write timeouts (or an explicit timeout); on expiry, or for an abortive close, the runtime is told to abort
  the driver; `close` never raises for a connection which failed earlier, the failure being available as
  `close_exception`;
- close callbacks, as omllm's peer has, run after everything pending has been failed.

The connection speaks wire values. It knows neither serde nor JSON.

### 5.2 `SyncRpcConnection`

A logic-free facade: each public method is `sync_await` over the corresponding method of an `RpcConnection` built on a
sync runtime, exactly as `InjectorImpl` wraps `AsyncInjectorImpl`. The asyncio form is the core used directly.
`BaseSyncRpcConnection` holds the protocol-agnostic part - lifecycle, a reentrant cross-thread guard, and `run`, which
drives any awaitable written against the async connection (a typed caller's call, say) under that guard.

### 5.3 `RpcRuntime`

The seam, as an abstract class with a `RpcRuntimeSink` callback interface (`on_event`, async, and `on_driver_done`):

- `make_promise()` returns an `asynclite` promise whose `wait` behaves as the runtime does;
- `is_cancelled_exception(exc)` classifies exceptions escaping handlers;
- `enqueue(*commands)` hands commands to the driver, returning False once it no longer accepts them;
- `start(sink)` binds the sink and, where pumping is a background activity, starts it;
- `spawn(key, fn)` runs a handler: inline to completion under sync, as a tracked task under asyncio;
- `cancel(key)`, `cancel_all()`, `close()` (abort the driver and cancel handlers, idempotent), `wait_closed()`.

### 5.4 The sync runtime

`syncs.py`. `BaseSyncRpcRuntime` holds the shared part: a pumping promise (`RpcSyncPromise`, implementing the asynclite
promise interface) whose `wait` loops - if done, return; if the driver is done, raise closed; step once, bounded by the
time remaining; repeat - and inline `spawn`. `SyncRpcRuntime` steps a `SyncIoPipelineDriver` with
`next(read=True, raise_on_stall=True)` and the driver's wait bound set to the time remaining; a wait-bound timeout just
re-checks the deadline. A stall - the driver raising without failing itself, because nothing can read, write, or fire -
fails the connection, since nothing waited for could ever arrive.

`pure.py` is the deterministic variant: `PureRpcLink` steps two pure drivers back to back, one `PureRpcRuntime` per end,
and whichever end is waited on pumps both. Each step delivers at most one event, or moves bytes, or - when nothing else
can happen - advances a shared virtual clock straight to the earliest deadline (or the wait's own). A wait nothing
could satisfy raises `PureRpcLinkDeadlockError`. Timeouts thus fire exactly and instantly, which is what makes the bulk
of the tests deterministic.

Nothing in these paths suspends, so `sync_await` is satisfied. `spawn` awaits the handler inline, which means a handler
which itself calls back out to the peer pumps reentrantly from inside the delivery of an earlier event; that is
inherent to a single-threaded inline model, bounded by stack depth, and documented. There is no cancellation: `cancel`
is a no-op and `is_cancelled_exception` is always False.

### 5.5 The asyncio runtime

`asyncios.py`. Holds a `PollAsyncioStreamIoPipelineDriver`. `start` creates one pump task which loops on `await
driver.next()`, delivering events to the sink, and on exit (driver stopped, transport failure, or the task itself
cancelled) reports driver completion, closes the driver, and sets a closed event. Promises are asynclite's asyncio
promises. `spawn` creates a task per handler, kept in a map by key (unkeyed ones in a set), with done callbacks which
remove it and observe its exception. `cancel` cancels by key; `close` aborts the driver and cancels every task but the
caller's own; `wait_closed` waits for the closed event, the pump task, every handler task, and their done callbacks.
`is_cancelled_exception` recognizes `CancelledError`.

### 5.6 Cancellation, the nod

Four cases, all inside the single-color core or the asyncio runtime:

1. A caller cancelled while awaiting a response: the waiter is popped and, by config, a wire cancel is sent.
2. A peer cancel or a handling-abort event: the spawned handler is cancelled by key.
3. A handler task cancelled from outside: an error envelope with code `cancelled` is sent if the request is still in
   flight and the connection still open, then the cancellation propagates.
4. The pump task cancelled: every waiter fails, every handler is cancelled, the driver is closed.

The rule for handler authors is to let cancellation propagate. The sync runtime has none and says so.

### 5.7 Execution policy

The sync runtime dispatches inline, one at a time. The asyncio runtime spawns a task per request. There is no other
knob in the core. Thread offload is a handler which awaits `to_thread`; one-at-a-time under asyncio is a serializing
handler wrapper around an asyncio lock, a dispatch-layer lego in the asyncio module. The session's in-flight limit with
the `reject` or `pause` policy is the only backpressure policy. No pools, queues, priorities, or persistence anywhere.

### 5.8 fdio

Designed for, not built. An fdio runtime lives inside manager callbacks and cannot wait, so it would be a serve-only
runtime with inline handlers and `wait` unsupported. Nothing in the core precludes it; it gets built if and when the
daemons fdio host migrates and still wants fdio.


## 6. Dispatch, serde, errors, and the standard-code surface

### 6.1 Handlers

`RpcHandler` has `handle_request(method, params)`, `handle_notification_inline(method, params) -> bool` (sync, applied
on the pump in wire order), and `handle_notification(method, params)` (run like a request handler).
`RpcMethodTableHandler` is a plain mapping from method name to async callable, with separate tables for spawned and
inline notifications; `rpc_merge_method_tables` rejects duplicates at composition time; `rpc_async_method` wraps a
plain callable. This is what omllm's composition root does by hand today. No signature binding anywhere in core.

### 6.2 Serde

Above the connection, never below it. An `RpcSerde` with `marshal(obj, ty)` and `unmarshal(value, ty)`; an identity
implementation; a lite-marshal adapter over `omcore.lite.marshal` (lite); a standard-marshal adapter over
`omcore.marshal` (standard, reachable from `all.py` land). Typed helpers consume it: a typed method wrapper which
unmarshals params and marshals the result around a method table entry, and a typed client which marshals params and
unmarshals results around a connection. Concern code stops calling a marshaler by hand, and the core never imports
either marshaler. Error data is an envelope struct and never passes through the serde.

### 6.3 Errors

Local: `RpcError`, `RpcProtocolError`, `RpcConnectionClosedError`, `RpcTimeoutError`, `RpcMessageTooLargeError`,
`RpcTooManyRequestsError`, `RpcCancelledError`, `RpcMethodNotFoundError`. Remote: `RpcRemoteErrorData(code, type,
message, traceback?)`, raised as `RpcRemoteError` with `RpcRemoteCancelledError` and `RpcRemoteMethodNotFoundError`
subclasses for the codes callers tend to catch. Codes are strings, collected in `RpcErrorCodes`; handlers may use any
other. The builtin-exception translation from omllm (`FileNotFoundError` and friends by name) becomes a client-side
lego.

### 6.4 Ids

Opaque hashables from an injectable creator: an integer counter per connection by default, a uuid creator available.
Per-direction scoping means the two ends never coordinate.

### 6.5 `all.py` and the standard-code surface

A non-lite `all.py` with `auto_proxy_init` and a recommended import alias, exporting the lite classes under short
names (`Connection`, `Config`, `Handler`, `MethodTableHandler`, `SyncConnections`, `AsyncioConnections`, ...) plus the
standard-only pieces: the `omcore.marshal` serde adapter and anything else that needs 3.14. The demo combining
polymorphic marshal with `dispatch.Method` lives next to it, in standard code, outside the core.

### 6.6 Polymorphic commands as a recipe

manage's style, a single `Command` union dispatched by type, is a serde-level choice in this design: one rpc method
whose params type is a polymorphic (tagged) union, with a dispatch `Method` or an `AttrRegistry` choosing the
implementation. That is exactly the demo of 2.16, and it needs nothing from the core.

### 6.7 Lite discipline

Every module except `all.py` and the standard marshal adapter is `# @om-lite`: 3.8 syntax, `typing` generics, no
`kw_only`, no `|` types, absolute `omcore.…` imports of lite modules only (never `all.py` modules). Every module-level
name carries the `Rpc`/`rpc_`/`RPC_` prefix including private helpers, because amalgamation shares one namespace
regardless of underscores. `__init__.py` files are empty so the package imports under 3.8 through its non-lite parent.


## 7. Paths not taken

Each of these was considered and rejected for the stated reason. They are recorded so the next person does not have to
re-derive them, and so a change of circumstances can be recognized.

- **Parallel sync and asyncio connection classes over a shared base** (jsonrpc's `base.py` / `sync.py` /
  `asyncio.py`). Rejected: it duplicates every piece of stateful logic in two colors, and the stateful surface here is
  larger (pings, cancels, keepalive interplay). The user named this explicitly as not the modern idiom.
- **Moving the session's logic into the async connection core.** Rejected: the session needs timers, and the pipeline's
  `Scheduling` service is the timer port which works identically under every driver and deterministically in tests. An
  async sans-io core cannot sleep without inventing another port.
- **Pump-by-waiter under asyncio** (whoever is waiting steps the driver, under a lock) instead of a pump task.
  Rejected: a server with nothing waiting still needs a pump, a handler calling back out to the peer would contend
  with a serving pump holding the lock, and handing the pump "baton" between waiters needs a wait-for-either primitive
  asynclite does not have. The pump task is simpler and is what jsonrpc already does; the sync runtime's caller-pumps
  model is the special case, not the general one.
- **Using asynclite's event-backed promise for the sync runtime.** Rejected: asynclite's sync backend assumes another
  thread makes progress (its events are `threading.Event`s); the rpc sync runtime assumes the caller does. Waiting is
  therefore runtime-specific and lives in the sync runtime's own promise, which pumps. asynclite is used only for the
  promise *interface* and the asyncio promise implementation, and conceptually for cancellation classification.
- **Using asynclite's sleeps, locks, queues, or events in the core.** Rejected as not needed: timers are the session's,
  the pump task removes any need for a pump lock, and a closed signal is a promise.
- **A pipelines driver base class or a formal driver "port" abstraction.** Rejected: pipelines deliberately has no
  driver base class so drivers integrate fully with their runtimes and core code can never ask what context it is in.
  The rpc runtimes import their driver kinds directly, as jsonrpc's connections do, and the core imports neither.
- **A runner seam on the asyncio runtime for thread offload, or a concurrency knob.** Rejected: thread offload is a
  handler awaiting `to_thread` and needs nothing from the core; one-at-a-time under asyncio is a serializing handler
  wrapper. A knob which queued requests would be the start of a job manager.
- **Worker pools, job queues, priorities, persistence.** Out of scope by the user's explicit caution. The in-flight
  limit with `reject` or `pause` gives backpressure without any of it.
- **Making the internal session speak jsonrpc.** Rejected: batches, spec-mandated invalid-message responses, id typing
  rules, and integer error codes are jsonrpc's alone. Realistic sharing is framing, the connection layer, the promise
  and runtime model, and the spec-builder pattern; jsonrpc keeps its session. Whether the two sessions eventually grow
  out of one abstract skeleton is deferred until the internal one has been used.
- **Reflection-based dispatch or an object facade in core.** Out of scope by the user; method tables only. The
  daemons `objects.py` facade is not carried forward.
- **A type alias for the envelope value tree.** Rejected by the user: it would fudge the typing story and wrongly
  suggest the core knows the shape; params and results are `Any` and the extension point is hands-off.
- **One request per connection, hello handshake, instance ids, and a replay registry in the core** (daemons). Kept
  available as legos (a handshake handler, a registry wrapping a dispatcher host-side), not forced: the omllm case
  runs both ends from the same code with no reconnect and needs none of it.
- **Polymorphic command dataclasses as the core dispatch model** (manage). Rejected as a core model, kept as a serde
  and dispatch recipe (6.6).
- **Building keepalive on `IdleStateIoPipelineHandler`.** Rejected: keepalive needs read-idleness, a ping, then a
  second deadline, and must consume its own pongs; its own two-phase timer is simpler than coordinating with the idle
  handler's events, and the idle handler remains available separately for idle close.
- **Putting the length-prefixed frame codec in `omcore/io/pipelines/bytes`.** Deferred by the user: it is written in
  the pipelines idiom but stays under `rpc/` for the foreseeable future, so this effort does not touch omcore lib code
  until the design has settled. May be re-evaluated later.
- **Starting directly in `omcore/rpc`.** Rejected by the user in favor of staging in `omxtra/rpc`, with promotion as
  its own commit once the omllm and jsonrpc needs are known to be met.
- **Avoiding the `Rpc` prefix clashes with omllm.** Rejected by the user: the new code owns the prefix; omllm's
  colliding names are replaced when it migrates. Until then the two are never amalgamated together.
- **Keeping omllm's raw-asyncio channel as a driver alternative.** Rejected: the asyncio stream pipeline driver covers
  it, and keeping two transports would defeat the point.
- **mitogen-style routing, multi-hop, and connection brokering.** Out of scope; nothing in the envelope precludes a
  routing header later, but no space is reserved for one.
- **A pipeline per call via multiplexing.** Rejected as scope creep: ordered streams are recipes over notifications and
  handle-plus-chunk calls (section 8.3). Multiplexed child pipelines exist in pipelines if a stream-per-call model is
  ever wanted.
- **Timing out requests by default.** Rejected for the home use case (long-running tool calls);
  `default_request_timeout_s` is None by default, unlike jsonrpc's sixty seconds, and is set per connection or per
  call where wanted.
- **Replying to a peer's cancel.** Rejected: the peer has already failed its waiter; a reply would be a late response
  it drops anyway. omllm's reply-with-`cancelled` behavior is reproduced only for the case where a handler is cancelled
  from outside while the request is still in flight, where the peer is still waiting.


## 8. Recipes

Conventions developed alongside the core, not features of it.

### 8.1 Concern triples

As omllm does: per concern a `protocol.py` (method name constants, request and result shapes), a `server.py` (a method
table, lite, in the amalgam), and a `client.py` (typed stubs, standard code). Concerns marshal through the serde
helpers rather than by hand, merge their tables at the composition root, and the composition root wires a connection to
any service which needs to call back out.

### 8.2 Ordered streams, pushed

Inline notifications in wire order, as process output does: the producer sends notifications, the consumer's handler
applies them inline, and anything the producer sent after them (such as the reply to a later request) is observed only
after they have been applied.

### 8.3 Ordered streams, pulled

Handle plus chunk calls, as the filesystem concern does: an open call returns a handle, chunk calls move bounded pieces,
a close call releases it. Listings page the same way. This is what the blobs concern will use for get, put, and list.

### 8.4 Serialized handling under asyncio

The serializing handler wrapper around an asyncio lock, for a backend which is not safe to call concurrently.

### 8.5 Blocking work under asyncio

A handler which awaits `to_thread` (standard code; lite code on 3.8 uses the loop's executor directly).


## 9. Testing

As built, under `tests/`: `test_codecs` (value and envelope codecs, a non-JSON value codec, framing), `test_session`
(the session and keepalive at the wire, against `raw.py`'s raw peer on one pure driver), `test_pure` (the connection
over the pure link: the bulk), `test_syncs` and `test_asyncios` (real sockets, threads, child processes over stdio,
every cancellation path), `test_serde`, `test_stress` (seeded randomized traffic, cancellation, and closes racing
traffic on both runtimes, checking invariants), and two standard-code modules: `test_examples` (the demos) and
`test_jsonrpc_seam` (12.1). The plan, as written beforehand:

- All core tests are `unittest.TestCase` modules under `tests/`, lite-marked, and run under `VENV=8`, `VENV=14`, and
  `VENV=14t` throughout development; under 8 via `omcore.testing.unittest` by dotted module name, under 14 and 14t via
  pytest.
- The primary harness is two pure drivers over a `PureLink`, each wrapped in a sync runtime variant which pumps the
  link between steps and can advance both manual clocks. This makes every protocol behavior deterministic: request
  and response, notifications inline and spawned, cancel both ways, pings and keepalive expiry, timeouts of every kind,
  limits and both policies, encode failures and substitutes, peer EOF with both policies, graceful and abortive close,
  `Sent` fences and backpressure under a bounded link, protocol errors, idle close.
- The session is also tested on its own with a single pure driver and a list of events, as jsonrpc's is.
- The sync runtime is tested end to end over a socketpair with the socket sync driver, with a peer thread.
- The asyncio runtime is tested over `asyncio` socket pairs and over a subprocess's stdio, including task tracking:
  no leaked tasks after close, handlers cancelled on abortive close and on peer cancel, `wait_closed` completing.
- Codecs and framing have unit tests covering round trips, malformed input, oversize in both directions, and the
  configurable width and byte order.
- The serde adapters round-trip through typed method and client helpers with both marshalers (the standard one in a
  non-lite test module).
- Amalgamation is exercised by the omllm migration's existing `.venvs/8` integration test once omllm is migrated.

Beyond the suite, wider ad hoc sweeps (hundreds of pure-link seeds, dozens of asyncio close-racing seeds, a sync sweep
over real sockets under 3.14t) were run during development; one found the `wait_closed` bookkeeping race of 12.6.


## 10. Migration and promotion plan

Order: core, omllm, jsonrpc, manage, daemons, blobs. Promotion to `omcore/rpc` sits between core and omllm, because
omllm depends only on omcore and cannot import omxtra.

1. **Core complete in `omxtra/rpc`** with the tests of section 9 green under 8, 14, and 14t, plus omllm-shaped and
   jsonrpc-shaped exercises in the tests (a filesystem-style handle-plus-chunk concern and a process-style inline
   notification stream; a connection driven through the jsonrpc-like `pause` policy) so that no new machinery is
   expected for the first two migrations.
2. **Promote** to `omcore/rpc` in one commit: move the package, update the memory of the intended home, keep the
   framing codec inside it.
3. **omllm**: replace `omllm/core/rpc` with imports of the new package; port `omllm/agent/remote` (`_main.py` builds an
   asyncio connection over the bootstrap's stdio streams; `server.py` merges concern tables into a table handler;
   `client.py` becomes a connection plus the inline-notification router plus the typed concern clients); port the fs
   and process concerns onto the serde helpers; regenerate the amalgam; run the omllm tests under 14 and 14t and the
   `.venvs/8` integration test. Colliding names are replaced outright.
4. **jsonrpc**: rebase its connection layer onto the shared connection core and runtimes. Its session stays. Either it
   adopts the shared session message set directly or its connection subclass translates `Jpm` events; decide on
   contact. Its sync and asyncio modules shrink to construction helpers and jsonrpc-specific result conversion.
5. **manage**: replace `channel.py` and `execution.py` with a connection over the pyremote streams; keep the bootstrap
   message, timebomb, deathsig, log forwarding, and heartbeat as the lifecycle extras they are (heartbeat becomes the
   keepalive handler).
6. **daemons**: port the hosts to the connection and runtimes, add the handshake handler and a replay-registry
   dispatcher wrapper as legos, drop `objects.py`. (Done, keeping `objects.py` and the whole public API: see 12.15.)
7. **blobs** (stretch): a lite target-side local store, then a blobs concern triple over the pull recipe with paged
   listings. (Done: see 12.16.)


## 11. Implementation plan

Module by module, in build order, with responsibilities, public surface, and invariants, but not code. Modules marked
*done* exist and pass ruff and mypy as of this writing; the rest are the work ahead.

### 11.1 `errors.py` — done

The error hierarchy of 6.3, `RpcErrorCodes`, `RpcRemoteErrorData` with its `type` wire name via the lite marshal field
key, and `rpc_remote_error_for_data` picking the subclass by code.

### 11.2 `messages.py` — done

`RpcUnspecified` (the class itself is the sentinel for "use the configured default"), the `RpcEnvelope` base and the
seven envelopes with `__post_init__` validation raising `RpcProtocolError`, the `RpcResponseMessage` union, and the
`RpcSessionMessages` namespace of commands, events, and the internal encode-failure message, with the pipelines
marker mixins described in 4.4.

### 11.3 `framing.py` — done

`RpcFrame` and `RpcLengthPrefixedFramingIoPipelineHandler` as in 4.1: constructor validation that the limit is
representable in the field width; decode translating the streambufs limit and corruption errors into
`RpcMessageTooLargeError` and `RpcProtocolError`; the end-of-stream-inside-a-frame case as an inbound `Error` message;
outbound size check and prefix encoding with `int.to_bytes`.

### 11.4 `codecs.py` — done

`RpcValueCodec` and `JsonRpcValueCodec`; `RpcEnvelopeCodec` and `RpcValueEnvelopeCodec` with public
`envelope_to_value` and `envelope_from_value` so a dialect can subclass or wrap; `RpcEnvelopeCodecIoPipelineHandler`
which raises on inbound decode failure and reports outbound failures inward.

### 11.5 `configs.py` — done

`RpcConfig` as in section 4 with validation in `__post_init__`, an `update` helper, and `DEFAULT`. Keepalive interval
and timeout must be set together.

### 11.6 `session.py` — done

`RpcSessionIoPipelineHandler` as in 4.4. Internal structure mirrors jsonrpc's: entry dataclasses with scheduler
handles, `_send` with the flush fence and `Sent` reporting through a weakly held context, policy-driven handling of
inbound envelopes, encode-failure substitution with a guard against substituting for a substitute, `_finish_close` as
the single idempotent terminal transition, flow-control deferral of `ReadyForInput`.

### 11.7 `keepalive.py` — done

`RpcKeepaliveIoPipelineHandler` as in 4.5, with a liveness re-check after each outbound feed because feeding output can
reentrantly close the pipeline.

### 11.8 `specs.py` — done

`rpc_build_pipeline_spec` as in 4.6.

### 11.9 `dispatch.py` — done

`RpcHandler`, `RpcMethodTableHandler` with `add_*` merging, `rpc_merge_method_tables`, `rpc_async_method`.

### 11.10 `runtime.py` — done

`RpcRuntimeSink` and `RpcRuntime` as in 5.3.

### 11.11 `connection.py` — done

As 5.1 and 5.2, with the base / protocol split. Invariants: a waiter is resolved or failed exactly once; `Closed` or
driver completion fails every outstanding waiter with a fresh closed error carrying the cause; nothing is left
unresolved once `wait_closed` returns; every spawned handler key is unique per in-flight request; a late response for
a dropped waiter is ignored.

### 11.12 `ids.py` — done

`RpcIdCreator` with integer, uuid, and callable implementations, and `rpc_id_creator_of`.

### 11.13 `syncs.py` — done

`RpcSyncPromise`, `BaseSyncRpcRuntime`, `SyncRpcRuntime`, and `SyncRpcConnections` (of a driver, a socket, an fd pair,
`connect_tcp`, `connect_unix`, a `subprocess.Popen`, this process's stdio). Named in the plural, like `asyncios.py`, so
neither shadows a stdlib module name within the package.

### 11.14 `pure.py` — done

`PureRpcLink`, `PureRpcRuntime`, `PureRpcLinkDeadlockError`, and `pure_rpc_connection_pair`, as 5.4.

### 11.15 `asyncios.py` — done

`AsyncioRpcRuntime`, `AsyncioSerializingRpcHandler`, and `AsyncioRpcConnections` (of streams, `connect_tcp`,
`connect_unix`, an asyncio subprocess, this process's stdio).

### 11.16 `serde.py` and `translate.py` — done

`RpcSerde`, `IdentityRpcSerde`, `LiteMarshalRpcSerde`, `rpc_typed_method`, and `RpcTypedCaller` (named for what it
does; typed calls under a sync facade go through `run`). `translate.py` is omllm's builtin translation, unchanged.

### 11.17 `marshal.py`, `all.py`, `examples/` — done, standard code

The `omcore.marshal` serde adapter; `all.py` under the alias `rpc`; `examples/services.py`, the demo of 6.6 and of
service methods collected through an `AttrRegistry`.

### 11.18 Tests and README — done

Section 9, and `README.md`.

### 11.19 Then

Promotion, and the migrations of section 10, each in its own commits.


## 12. What implementation taught

### 12.1 The connection seam carries JSON-RPC

`test_jsonrpc_seam.py` writes a JSON-RPC connection on `BaseRpcConnection` - its `on_event` maps the JSON-RPC session's
events onto the base's waiter, fence, and handler helpers - and drives the existing JSON-RPC pipeline session, batches
included, over the sync, pure, and asyncio runtimes unchanged, interoperating on the wire with the existing JSON-RPC
connection in both directions. The runtimes needed nothing; the base connection needed only the split. This settles
the open question of 10.4: JSON-RPC keeps its session and gets a connection subclass; it does not adopt this protocol's
session messages.

### 12.2 Failures surface once, and closes keep their final answers

The plan carried over JSON-RPC's rule that a failing session close also surfaces its exception as raw driver output, so
the host wakes even behind a stalled flush; the runtimes take that as a driver failure and abort. The tests showed the
cost: a close with a healthy transport - the drain timeout expiring, say - aborted the driver and discarded the
`shutting_down` answers just queued for the requests in flight. Now the raw exception is surfaced only when the
transport itself is in trouble (the closure came from a pipeline error: a failed or stalled transport, garbage from the
peer, a keepalive timeout). Otherwise the session flushes normally. A stall during that final flush is still bounded:
the write timeout raises a pipeline error after the session has closed, which the session lets escape; unhandled, it
fails the driver, which is the abort. Nothing may be output after `FinalOutput`, so escaping is the only channel left,
and it is the pipelines' standard meaning of an unhandled error.

### 12.3 An abortive close still answers

`Close(graceful=False)` at the session means "do not wait for in-flight work", not "drop the transport": the requests
in flight are answered `shutting_down` and flushed. A peer whose request was in flight gets a definite answer rather
than a disconnect. Dropping the transport outright is `runtime.close()`.

### 12.4 `pause` admits a read batch

The `pause` in-flight policy stops further reads; frames already read in the same batch are still admitted, so the
limit can be overshot by one read batch. This matches JSON-RPC's behavior and is documented in the tests.

### 12.5 Error typing

`RpcMessageTooLargeError` is an `RpcError` and a `ValueError`, not a protocol error: sending one fails only that
message, like any other unencodable value, while receiving one is fatal by the framing's nature. Ids off the wire must
be hashable, so a list or mapping id is a protocol error rather than a crash in the session's bookkeeping. Remote type
names are qualified (`builtins.FileNotFoundError`), as omllm's are, so its translation carries over.

### 12.6 `wait_closed` waits for bookkeeping too

A randomized sweep found `wait_closed` returning while finished handler tasks were still tracked: tasks already done
when it looked were not waited for, and their done callbacks - which observe and untrack them - run one loop iteration
later. It now yields until the tracking settles, so "no task left behind" holds exactly when it returns.

### 12.7 Performance

On a socketpair, one round trip costs about the same as JSON-RPC's on the same driver (about 0.65 against 0.72
milliseconds sequentially, in one measurement), and concurrency does not improve it: each send waits for its own flush
fence. Batching sends behind one fence is the obvious lever if it ever matters; nothing here precludes it.

### 12.8 Sync connections move only while called

An idle sync connection reads nothing, so it neither answers pings nor runs its own timers between calls. A server in
`serve()` is always pumping, so this only matters for idle sync clients facing a peer with keepalive; such a client
must ping periodically itself. Documented in the README.

### 12.9 Amalgamation has rules plain imports do not check

Porting omllm put the core in a real amalgam for the first time, and it failed in three ways the lite tests could not
see, since they import modules normally:

- **Type aliases are hoisted.** The amalgamator moves every `# ta.TypeAlias` line above all class definitions, so an
  alias naming a class must spell it as a string.
- **Import aliases do not survive.** Imports of amalgamated modules are stripped and their names become globals, so
  `from .messages import RpcSessionMessages as Rsm` leaves `Rsm` undefined. Lite modules use real names.
- **Module-level imports decide what is carried.** The spec builder imported the TLS and logging handlers to support
  flags; the agent never uses either, but carried both. Optional handlers are now passed in as instances
  (`transport_handlers`, `outermost_handlers`), so only callers who construct one carry it.

The guard is the pipelines' own: a lite `_amalg.py` root in the package, generating `omdev/scripts/lib/rpc.py`, which
the lite precheck executes under 3.8.

### 12.10 pyremote registered its module too late

The pyremote bootstrap renames the payload's module (`__pyremote__`) on its first line but only registered that name
in `sys.modules` at finalization, after the payload's module-level code has run. Python 3.8's dataclasses look a
class's module up in `sys.modules` while creating any class with a string-annotated field; the pipelines core has such
fields, the old payload had none, so the agent died at load. The bootstrap now registers the name on the same first
line, with a regression test which fails without it under 3.8.

### 12.11 A `shutting_down` answer is a closed connection

Because even an abortive close answers what is in flight (12.3), a caller whose peer is closing gets a `shutting_down`
error where it used to see a disconnect. It is raised as `RpcRemoteShuttingDownError`, which is also an
`RpcConnectionClosedError`, so code handling a lost connection - omllm's process teardown, for one - handles it too.

### 12.12 The cost to the agent payload

The agent amalgam grew from about 6,400 lines (45 KB compressed, as pyremote sends it) to about 19,800 (144 KB): the
pipelines core, the asyncio stream driver, the stream buffers, and their logging. That is the price of running on the
shared foundation; nothing optional is carried.

### 12.13 The JSON-RPC migration

As 12.1 predicted, JSON-RPC kept its session and gained a connection subclass. `BaseJsonrpcConnection` is now the one
JSON-RPC connection, a `BaseRpcConnection` over the JSON-RPC session's events, running on any runtime;
`AsyncioJsonrpcConnection` binds it to the asyncio runtime and a driver, and `SyncJsonrpcConnection` is a facade over it
on the sync runtime which adapts sync dispatchers and notification handlers, handing them the sync connection so they
can call back synchronously. The public names, signatures, and construction helpers are unchanged, and MCP, ACP, and
the LSP client needed no edits. The three connection modules went from about 1,380 lines to about 890, some 300 of
which are the transport construction helpers.

What the base needed: two hooks, so a vocabulary raises its own error types (`_closed_error`, `_send_timeout_error`),
and closers that run whenever the driver finishes rather than only on an explicit close - the old sync connection
closed a child's stdin as soon as the child went away. Behavior changes: a sync `send_batch` raises on its first failed
request, as the asyncio one always did, rather than waiting for all of them first; and the dispatcher is set with
`set_dispatcher` rather than through a private attribute.

### 12.14 The manage migration

`ominfra.manage`'s remote execution kept its lifecycle extras and lost its protocol. The bootstrap object, formerly
the first raw message, is now the first call, `manage.bootstrap`; once it has built the remote's injector, the command
handler's `manage.execute` is added to the method table, and commands travel as the injected lite marshaler's
polymorphic `Command`s through the serde layer - the recipe of 6.6, with the lite marshaler. Forwarded log records are
`manage.log` notifications applied inline on the host. The in-process ("fake remote") connector runs the same protocol
over a socketpair. The hand-written channel, its little-endian framing, and both `asyncio.wait` loops are gone.

Two deliberate changes. Only records at INFO and above are forwarded: the pipelines driver logs every message it
moves at DEBUG, so forwarding those over the same connection would feed back without end; debug records still reach
the remote's own handlers, which by default write to the inherited stderr. And the remote no longer pings the host
every few seconds: those pings only logged their latency, and a dead host already ends the remote through EOF,
deathsig, or the timebomb. The rpc keepalive is there if liveness checking is ever wanted. manage had no tests; it now
has a few, and was checked by hand against in-process and subprocess targets, the latter under 3.8.

### 12.15 The daemons migration

`omxtra.daemons.rpc` kept its wire, its public API, its replay registry, and its outcome taxonomy, and lost its
framing, codec, and session handlers. Its pipelines are now `omcore.rpc` framing, a dialect codec, the handshake
handler, the session, and - server side - the close-after-requests handler; its sync, asyncio, and fdio hosts and its
two clients are `omcore.rpc` connections. The dialect codec maps the protocol's `(client_id, request_id)` onto the
envelope id, so the session correlates responses and the replay registry sees the identity the client chose. Its
output is pinned byte for byte against the protocol's blocking helpers, which remain its oracle; `objects.py` stayed,
being public API with users, and needing nothing from the transport.

The protocol needed four things the toolbox lacked, and they became toolbox pieces rather than daemons code, each
small and each tested apart: the hello handshake (`handshake.py`), closing after a number of requests (`closing.py`),
whole-message request handling with verbatim error answers (`RpcHandler.handle_request_message` and
`RpcHandlerError`), and the fdio runtime (`fdios.py`). The fdio runtime's one requirement of `omcore.io.pipelines` was
an optional callback on the fdio driver's readiness methods, taking the outputs an event-emitting pipeline produces
instead of failing the check that there are none.

The client is written once, async-colored, as a connection subclass (`RpcClientRpcConnection`): it waits for the
service's greeting, sends one request under its client-chosen id, and classifies every failure by whether the request
may have run - unavailable before the greeting, indeterminate after the send began. The sync client runs it under
`SyncRpcConnection.run`; the asyncio client awaits it. The server side is one handler (`RpcServerHandler`): it leases
activity from the server runtime, dispatches through the registry, and answers with the registry's response verbatim.

Three behaviors needed care. Timeouts moved from socket timeouts into the session: the client's `io_timeout_s`
became the request, handshake, and write timeouts, and the server's `connection_timeout_s` the idle timeout, which
closes a silent connection but never times out a request being handled. The activity lease is held until the
connection closes, as the fdio host already did, so a draining service waits for answers to drain. And the asyncio
host runs each dispatch apart from its connection, shielded: a client vanishing mid-request aborts the connection and
with it the connection's handler task, which before the port would never have happened - the old host awaited the
handler with nothing reading - and a cancelled dispatch would leave its registry entry pending for ever, hanging the
retry it exists to serve.

One toolbox change came out of it: an event an optional handler emits for whoever cares, such as the handshake's
completion, is now marked `RpcInfoEvent`, and a connection not consuming one passes it at debug rather than warning -
servers have no use for the client's greeting, and were logging a warning per connection.

### 12.16 The blobs remote store

The forcing case is met: a `LocalBlobStore` runs on another host exactly as omllm's agent tools do. It took two
steps. First the blobs core and local backend became lite - the types, errors, keys, capabilities, the sync
interface, and the local store and its helpers - which meant 3.8 spellings and, under the amalgamation naming rule,
prefixed names: the preconditions are now `BlobIfAbsent`, `BlobIfMatch`, and `BlobIfNoneMatch`. Then a concern triple
in `omxtra/blobs/remote`: a lite protocol and service, and a standard `RemoteBlobStore` (an `AsyncBlobStore`) with a
pyremote launcher. The target's amalgam serves the store under the sync runtime, so the store's blocking calls simply
run inline.

The pulled-stream recipe of 8.3 shaped the wire, with one difference for reads: they hold no handle. Each chunk after
the first is a get pinned by `BlobIfMatch` to the version the first saw, and a read whose object is replaced midway
starts over, so a read is consistent without the target keeping anything open between calls. Writes do hold a
handle - a target-side store writer, entered at the begin and exited at the commit or abort - because a store writer
is what makes an uncommitted write invisible; the target discards whatever a connection leaves open when it closes.
Listings page by `start_after`.

Store errors cross under a type naming their class, `blobs.<Class>`, rather than the module-qualified name the
connection would give them: inside an amalgam every class lives in the script's module, so module names say nothing.
Static checks run on the host before any call, as the store contract requires. A connection failure is a
`BlobTransportError` for reads and for calls which never left, and a `BlobIndeterminateError` for a mutation which may
have arrived - the store's existing vocabulary for exactly that distinction.

The whole blobs conformance suite runs against the remote store twice: in process, and against the amalgam bootstrapped
into the Python 3.8 venv, with small chunks and pages so both are exercised. The 3.8 tier earned its place at once: it
caught a `datetime.UTC` which an autofix had put back into the lite local store, and which an import check cannot see.
