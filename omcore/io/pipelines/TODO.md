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
- `PollAsyncioStreamIoPipelineDriver._drain_again` / `_next_drain_flush_outputs` are unreachable now that fences are
  held behind a pending drain; remove them once the hold-behind-drain path is settled

### multiplex

- revisit completion listeners holding the handler context weakly: `_on_parent_flush_done` and `_on_parent_await_done`
  in `multiplex/handlers.py`, the child scheduling and lifecycle services in `multiplex/children.py`
- report a connection failure originating inside the multiplexer (adapter exception, control-output limit) to the
  parent pipeline as an inbound `Error`: today the parent sees only the encoded connection error and `FinalOutput`,
  so an application cannot tell a failure from a graceful shutdown without inspecting the handler
- give `MultiplexCreditStrategy` a receive-side counterpart of `adjust_all_send`, so a protocol which changes its own
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
