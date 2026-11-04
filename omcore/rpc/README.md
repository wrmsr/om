# rpc

A small, lite rpc toolbox on `omcore.io.pipelines`: a symmetric request / response / notification protocol over any
ordered byte stream, with one async-colored connection core that runs under sync, asyncio, and deterministic in-process
runtimes alike. Everything except `all.py`, `marshal.py`, and `examples/` is `@om-lite` - Python 3.8+, stdlib and
`omcore` lite only - so it can be amalgamated into a remotely bootstrapped script.

See `DESIGN.md` for the survey this grew out of, the reasoning behind each choice, and the roads not taken.


## Layers

```
caller / handlers            (async code, written once)
    |
connection                   RpcConnection: ids, waiters, send fences, handler dispatch, errors, close sequencing
    |   runtime              Sync | Asyncio | Fdio | PureRpcLink: how waiting, pumping, handlers happen
pipeline driver              any omcore.io.pipelines driver
    |
pipeline                     [buffering] [ssl] [write timeout] framing  envelope codec  [handshake] [keepalive] [idle]
                             [between]  session
```

- **Framing** (`framing.py`): a length prefix, four bytes network order by default, then the payload.
- **Envelope codec** (`codecs.py`): frames to the seven envelopes - request, result, error, cancel, notification,
  ping, pong - and back, over a pluggable value codec. JSON is the default; nothing else depends on it.
- **Session** (`session.py`): the innermost handler, owning all protocol state. Commands in, events out, timers from
  the pipeline's scheduler. It never runs anything: a received request is an event.
- **Optional handlers**: keepalive (`keepalive.py`) and idle close are installed only when configured. Two more are
  passed in by instance: a hello handshake (`handshake.py`), exchanging opaque greetings - a protocol name and version,
  an instance id - before anything else crosses; and closing after a number of requests (`closing.py`), for a server
  whose clients connect per call.
- **Connection** (`connection.py`): one class, async-colored, over a runtime. `BaseRpcConnection` is the
  protocol-agnostic part, reusable for another session vocabulary; `RpcConnection` is this protocol's.
- **Runtimes**: the only place sync and asyncio differ. `syncs.py` pumps in the caller's thread and runs handlers
  inline; `asyncios.py` runs a pump task and a tracked task per handler; `fdios.py` hosts connections in an fdio
  manager's callbacks, many to a thread, where nothing may wait - a server's runtime; `pure.py` steps two pure drivers
  on a virtual clock, for tests and in-process loopback.
- **Dispatch and serde** (`dispatch.py`, `serde.py`): method tables, and typed methods and calls over a pluggable
  serde - identity, the lite marshaler, or `omcore.marshal` (`marshal.py`, standard code). The core knows neither.


## Use

Asyncio:

```python
from omcore.rpc import all as rpc

async def add(params):
    return params[0] + params[1]

conn = rpc.AsyncioConnections.of_streams(reader, writer, handler=rpc.MethodTableHandler({'add': add}))
async with conn:
    print(await conn.request('add', [1, 2]))
```

TLS, or any other transport-level handler, goes in by instance, so only code which uses it carries it:

```python
conn = rpc.AsyncioConnections.of_streams(reader, writer, spec_kwargs=dict(
    transport_handlers=[ipl.SslHandler(server_side=False, server_hostname=host)],
))
```

Sync - the same handlers, the same connection, driven from a facade:

```python
with rpc.SyncConnections.connect_unix('/tmp/sock') as conn:
    print(conn.request('add', [1, 2]))

with rpc.SyncConnections.of_stdio(handler=handler) as conn:
    conn.serve()
```

Deterministic, both ends in one thread, timeouts firing instantly on a virtual clock:

```python
pair = rpc.pure_connection_pair(b_kwargs=dict(handler=handler))
assert pair.a.request('add', [1, 2]) == 3
```

Typed, over a serde:

```python
serde = rpc.LiteMarshalSerde()
table = {'bounds': rpc.typed_method(bounds, Box, Point, serde=serde)}
caller = rpc.TypedCaller(conn, serde, translate_error=rpc.translate_remote_builtin_error)
point = await caller.call('bounds', box, Point)
```


## Recipes

- **Concern triples.** Per concern, a `protocol.py` of method names and wire shapes, a lite `server.py` method table,
  and a `client.py` of typed calls. Concerns merge their tables at a composition root with
  `rpc_merge_method_tables`, which rejects duplicates.
- **Pushed streams.** Inline notifications (`inline_notifications=` on a method table) are applied on the pump in wire
  order, so everything the peer sent before a response has been applied by the time the response is seen.
- **Pulled streams.** Handle plus chunk calls: open returns a handle, chunk calls move bounded pieces, close releases
  it. Listings page the same way.
- **One at a time under asyncio.** Wrap the handler in `AsyncioSerializingRpcHandler`.
- **Blocking work under asyncio.** A handler which awaits `asyncio.to_thread` (or the loop's executor on 3.8).
- **A dialect.** Another protocol's wire, over the same session: subclass `RpcValueEnvelopeCodec`, mapping its
  messages onto the envelopes and its ids onto envelope ids. A handler answering whole requests overrides
  `handle_request_message`, and raises `RpcHandlerError` to send an error exactly as given. `omxtra.daemons.rpc` is one.
- **Polymorphic commands and service classes.** See `examples/services.py`: `omcore.marshal` polymorphism with a
  dispatch `Method`, and `@rpc_service_method` collected through an `AttrRegistry`.


## Things to know

- **Sync handlers run inline.** Under a sync runtime a handler runs on the pump, to completion, and must never actually
  suspend. A handler calling back out to the peer pumps reentrantly, which is what keeps two sync peers calling each
  other from deadlocking.
- **A sync connection only moves while called.** Between calls nothing reads the transport: an idle sync client neither
  answers pings nor runs its own timers. A server in `serve()` is always pumping. Keepalive against an idle sync client
  needs the client to ping periodically itself.
- **Cancellation** (asyncio): a caller cancelled mid-request abandons it and tells the peer; a peer's cancel or a
  handling timeout cancels the handler task; a handler cancelled from elsewhere answers `cancelled`. Handlers should let
  `CancelledError` propagate. Every task is tracked, and `wait_closed` waits for them.
- **Backpressure** is real: `request`, `notify`, and `ping` wait until their bytes reach the transport. The in-flight
  limit answers excess requests `busy`, or with the `pause` policy stops reading (pure servers only).
- **Closing** is graceful by default and always bounded. A graceful close from inside a request handler waits for that
  very request, so it only ends at the drain timeout: answer first, close from elsewhere.
- **Failures surface once.** A transport-level failure aborts; a failure with a healthy transport still flushes the
  answers queued for in-flight requests, which reach the caller as `RpcRemoteShuttingDownError` - also an
  `RpcConnectionClosedError`.
- **Amalgams.** Lite modules must not alias imports, and type aliases naming classes must quote them; see
  `DESIGN.md` 12.9. `omdev/scripts/lib/rpc.py` is the package's own amalgam, executed under 3.8 by the precheck.


## Tests

Unittest-style and lite, run under 3.8 as well as 3.14 and 3.14t:

```
./python -m pytest omcore/rpc
VENV=8 ./python -m omcore.testing.unittest omcore.rpc.tests.test_pure
```

`test_jsonrpc_seam.py` (standard code) proves `BaseRpcConnection` carries JSON-RPC's session over the same runtimes.
