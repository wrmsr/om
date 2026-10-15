### immed

- unify config story

### core

- drivers
  - sync
  - anyio
- thread safety? nogil?
- inject interop
- interleavable inter-stage message queueing handler? usecases?
- removed callbacks
  - do netty ByteToMessageDecoder removal handling
  - also removing in flight might mess stuff up (STARTTLS?)
- timeslice-based 'should defer' service (not iteration counting like in decompress)
- all.py
- ssl.OP_ENABLE_KTLS
- sendfile fast path
  - bounded reads only?
  - still need timeouts
  - Accept-Encoding: identity
  - no chunking, no ssl (or KTLS)

### half-close

- bound the asyncio driver's graceful close: a peer which never reads keeps it `DRAINING` until the transport is
  aborted, as the sync drivers are kept waiting to write; a configurable close timeout which fails the `FinalOutput`
  and aborts is a separate decision from servicing commands while it waits (which is done)
- decide whether `IdleStateIoPipelineHandler` should keep firing `ALL_IDLE` once both `FinalInput` and
  `ShutdownOutput` have passed, when nothing can happen until `FinalOutput`: it matches its docstring and may serve as
  a "close the zombie" signal, but is not a deliberate choice

### drivers

- move a `Defer` continuation behind the reads and writes already pending in the synchronous drivers' loops, not only
  behind the timers already due: the fuller form of the fairness yield `yielding.py` describes

### hosts

- process transports (phase 2's optional milestone): start a subprocess with its standard streams as a hosted
  descriptor-pair transport, or on a pseudo-terminal as a hosted duplex transport, with its exit status delivered by
  posting; the fdio and asyncio hosts can already adopt the descriptors, what is missing is the spawn, the reaping
  after EOF, and the posted exit status
- `SimpleHttpHandlerServerIoPipelineHandler.build_standard_pipeline_spec` takes a socket and address only to attach
  them as metadata: a variant taking `IoPipelineHostTransportInfo` would let the HTTP server stack be served over an
  in-process transport (a multiplexed stream, say) without one
- an `Await` reaching the fdio driver is unhandled output, which fails the manager's dispatch of the handler: decide
  whether the fdio forms should reject it as a typed error, or whether hosted pipelines should get an output sink
- the descriptor transport in `drivers/fdio/descriptors.py` and `FdSyncIoPipelineDriver` carry the same flag-saving,
  half-close, and restore logic for descriptor pairs: share it once the sync driver may change
- the in-memory host reports a listener's refusing spec factory to the connecting side as a refused connect, where a
  real peer would see a connection which closes at once; revisit if a test needs the latter
- the asyncio host serves one owned duplex descriptor through two pipe transports on the descriptor and a duplicate
  of it, so closing one does not close the description: good enough for a pseudo-terminal master, worth a look for
  anything stranger

### multiplex

- revisit completion listeners holding the handler context weakly: `_on_parent_flush_done` and `_on_parent_await_done`
  in `multiplex/handlers.py`, the child scheduling and lifecycle services in `multiplex/children.py`
- report a connection failure originating inside the multiplexer (adapter exception, control-output limit) to the
  parent pipeline as an inbound `Error`: today the parent sees only the encoded connection error and `FinalOutput`,
  so an application cannot tell a failure from a graceful shutdown without inspecting the handler
- give `IoPipelineMultiplexCreditStrategy` a receive-side counterpart of `adjust_all_send`, so a protocol which changes its own
  advertised initial window (HTTP/2 `SETTINGS_INITIAL_WINDOW_SIZE`) can adjust existing streams' windows; the h2-like
  test adapter's `SendSettings` only shifts the peer's send credit for that reason
- the synchronous drivers run a parent `Defer` between the messages of one read batch, so the multiplexer's
  per-batch input coalescing (DESIGN 13.5) covers one decoded buffer there rather than the whole batch the asyncio
  driver feeds at once: correct, just narrower

### http

- ensure parity with urllib/http.server in general
- ensure parity with netty security wise
- request pipelining
- verify keepalive
- proxy/tunnel connect
- wire into omcore.http.client/server
- Date default server header
- dynamic streaming vs full by app endpoint
- h2 - _will not implement protocol manually_, plug in to `h2` lib
- lean on ParsedHeaders more - validly-duplicate-but-identical content-length currently isn't handled for ex.
- dangerous switch to not validate http headers
- use nginx for a canned test harness server

### proto impls

- irc lol
- dns?? stub
- proto / grpc
- (promote) redis / memcache
- db drivers?
