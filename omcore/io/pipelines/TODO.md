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

- jsonrpc
- irc lol
- dns?? stub
- proto / grpc
- (promote) redis / memcache
- db drivers?
