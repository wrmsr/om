### immed

- assess cyclic garbage - possible weakrefs:
  - `IoPipelineHandlerContext._pipeline`
  - `IoPipelineHandlerContext._context`
- hand optimize a bit
  - segmented split_to should mutate seg list in place

### core

- revive DESIGN.md
- drivers
  - 'pure' - no io
  - sync
  - fdio
  - anyio
- thread safety? nogil?
- inject interop
- interleavable inter-stage message queueing handler? usecases?
- removed callbacks
  - do netty ByteToMessageDecoder removal handling
  - also removing in flight might mess stuff up (STARTTLS?)
- timeslice-based 'should defer' service (not iteration counting like in decompress)
- all.py

### http

- ensure parity with urllib/http.server in general
- ensure parity with netty security wise
- request pipelining
- keepalive
- proxy/tunnel connect
- wire into omcore.http.client/server
- Date default server header
- dynamic streaming vs full by app endpoint
- h2 - _will not implement protocol manually_, plug in to `h2` lib
- lean on ParsedHeaders more - validly-duplicate-but-identical content-length currently isn't handled for ex.
- dangerous switch to not validate http headers

### proto impls

- websocket
- jsonrpc
- irc lol
- dns?? stub
- proto / grpc
- redis / memcache
- db drivers?
