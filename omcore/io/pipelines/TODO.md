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

- stop announcing `ReadyForOutput` after `ShutdownOutput` in the TLS handler and http chunking, as the drivers now do
  once it reaches the terminal (DESIGN 6)
- mark host-facing messages `AfterShutdownOutput` - jsonrpc `JsonrpcPipelineMessages.Event`, http client
  `IoPipelineHttpClientMessages.Output` - which would otherwise be rejected after a half-close
- fail TLS's pending `ShutdownOutput` and flushes when a failed or EOF'd handshake drops queued plaintext, rather than
  reporting success
- decide whether asyncio `ShutdownOutput` should complete only once the FIN is actually sent: it completes after
  `write_eof()` plus a drain returning at the low watermark, which DESIGN 8 allows but DESIGN 5's wording outpromises

### drivers

- clear the asyncio driver's `_pending_awaits` on `close()`: an awaitable which never completes keeps a cycle alive
- let the pure driver simulate write failures once its peer is gone, so back-to-back links can model one side closing
  (the draining deadlock test in `drivers/tests/test_driver_edges.py` can only assert half of it today)

### multiplex

- revisit completion listeners holding the handler context weakly: `_on_parent_flush_done` and `_on_parent_await_done`
  in `multiplex/handlers.py`, the child scheduling and lifecycle services in `multiplex/children.py`
- make per-stream scheduler weights settable: the scheduler supports them, but every stream is added with weight 1
- tidy the review-written regression tests to house style (function-level imports, long class docstrings):
  `multiplex/tests/test_emission.py`, `multiplex/tests/test_credit_bounds.py`, `drivers/tests/test_driver_edges.py`,
  `drivers/tests/test_asyncio_backpressure.py`, `ssl/tests/test_halfclose_edges.py`

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
